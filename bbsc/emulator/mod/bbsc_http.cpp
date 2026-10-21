// SPDX-FileCopyrightText: Copyright 2026 CLS_AMG
// SPDX-License-Identifier: GPL-2.0-or-later

// BBSC mod: the game's HTTP calls. In the emulator build, core/libraries/network/http.cpp
// changes Bloodborne's summon traffic on its way out (Wozzardman's seamless route plus BBSC's
// connect-first and stale-record cleanup). A mod cannot reach that code, so the DLL does it one
// step earlier: it swaps the eboot's import slots (GOT entries the emulator filled at load) of
// the libSceHttp functions the game calls for its own wrappers, which change the request and pass
// it on to the emulator's function.
//
// Import slots, CUSA03173 01.09 (tools/gamedata/eboot_imports.py, BBSC offsets):
//   0x053E5618 sceHttpCreateConnectionWithURL   0x053E5620 sceHttpCreateRequestWithURL
//   0x053E55E0 sceHttpAddRequestHeader          0x053E5628 sceHttpSetRequestContentLength
//   0x053E5670 sceHttpSendRequest               0x053E5648 sceHttpDeleteRequest
//   0x053E5668 sceHttpReadData
//
// What the wrappers do:
//   - URLs: the entries of host_overrides.json (same file and format as the emulator's) are
//     applied here too, so a stock emulator reaches the BBSC game server and summon broker.
//   - /summon_messenger/*: header X-ShadPS4-Bloodborne-Seamless: 1 (the broker's seamless mode).
//   - summon search/request (a host looking for signs): the host's placement header, as the
//     emulator sent it, AND the same text to every other player through the BBSC relay - the game
//     does not import sceHttpGetAllResponseHeaders, so the guest cannot read it from the broker's
//     reply; the relay brings it instead (bbsc_relay.cpp -> BbscMod::OnHostPlacement).
//   - summon create (a guest's sign): the AreaId becomes the host's map once a host's placement
//     is known (connect-first), and the first seamless create of this run sends a forced delete
//     for the same SessionId/UserId first (stale broker record after a crash).
//   - a claim the broker delivered with a sign that never became a join, and a session that
//     ended, re-arm that delete: the next sign starts clean (see "Stuck claims" below).
// Not done: the emulator's 3 s "fast sign" re-posts. They replaced the game's own reply; extra
// posts from here would take the broker's claim themselves and the game would never join.

#ifdef _WIN32
#include <windows.h>
#include <winhttp.h>
#else
#include "linux/bbsc_win32.h" // bbport
#endif
#ifndef _WIN32
#include "core/memory.h" // bbport: SessionState
#endif

#include <array>
#include <atomic>
#include <cctype>
#include <cstring>
#include <fstream>
#include <map>
#include <thread>
#include <mutex>
#include <sstream>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "common/logging/log.h"
#include "common/types.h"
#include "core/bloodborne_re.h"

namespace BbscMod {
void RelaySendPlacement(const std::string& placement);
void RelaySendPlacementTo(s64 target_user, const std::string& placement); // bbport
u64 EbootAddress(); // bbsc_mod.cpp: where the game image is (0 until found)
void GuardSlot(u64 slot_offset, u64 wrapper, void** original, const char* name); // bbsc_mod.cpp
}

namespace {

constexpr u64 EbootSize = 0x056D4000ULL;
constexpr u64 SlotCreateConnection = 0x053E5618;
constexpr u64 SlotCreateRequest = 0x053E5620;
constexpr u64 SlotAddHeader = 0x053E55E0;
constexpr u64 SlotSetContentLength = 0x053E5628;
constexpr u64 SlotSend = 0x053E5670;
constexpr u64 SlotDelete = 0x053E5648;
constexpr u64 SlotReadData = 0x053E5668;
// A claim delivered with our sign is followed by a join (session state 4) within seconds when it
// works; one that has not after this long is a dead claim.
constexpr s64 ClaimJoinWaitMs = 20'000;
constexpr s64 PlacementStaleMs = 20'000;
// bbport: a placement sent to our own sign by the host that rang it stays longer (BBSC's bbsc.dll
// of 2026-10-17: 90 s), as that host keeps the claim open while the game joins.
constexpr s64 DirectedPlacementStaleMs = 90'000;

using CreateConnectionFn = int PS4_SYSV_ABI (*)(int, const char*, bool);
using CreateRequestFn = int PS4_SYSV_ABI (*)(int, s32, const char*, u64);
using AddHeaderFn = int PS4_SYSV_ABI (*)(int, const char*, const char*, s32);
using SetContentLengthFn = int PS4_SYSV_ABI (*)(int, u64);
using SendFn = int PS4_SYSV_ABI (*)(int, const void*, u64);
using DeleteFn = int PS4_SYSV_ABI (*)(int);
using ReadDataFn = int PS4_SYSV_ABI (*)(int, void*, u64);

CreateConnectionFn original_create_connection = nullptr;
CreateRequestFn original_create_request = nullptr;
AddHeaderFn original_add_header = nullptr;
SetContentLengthFn original_set_content_length = nullptr;
SendFn original_send = nullptr;
DeleteFn original_delete = nullptr;
ReadDataFn original_read_data = nullptr;

std::mutex state_mutex;
std::map<int, std::string> request_urls;            // reqId -> URL the request really goes to
std::vector<std::pair<std::string, std::string>> overrides; // URL prefix -> replacement
std::atomic<bool> stale_cleared{false};
std::atomic<s64> placement_received_ms{0};
// 5-player test 2026-10-12: every player polls /summon_messenger/get, waiting guests too, so every
// guest sent its own placement as "a host looking for signs". The other waiting guests switched
// their sign's map between the real host (Dream) and a guest in Central Yharnam, and the broker
// hid every sign outside the searcher's map (Preparing) - nobody past the 3rd was summoned.
// bbport (issue #17): a host now sends its placement only to the sign it rings (below), so a
// waiting guest's own polling sends nothing.
std::atomic<u32> placement_sender{0};
// bbport (issue #17): which sign is ours, and whether the placement we hold was sent to it.
// Following the first host on the server that looked for signs tied a guest to a stranger on a
// busy server (12 hosts on Seamless Hunt in one session): its sign went to that host's map and
// the friend never found it. As in BBSC's bbsc.dll of 2026-10-17, a host now sends its placement
// to the one sign it rings, and a guest takes only a placement sent to its own sign.
std::atomic<s64> own_sign_user{0};
std::atomic<bool> placement_directed{false};
std::atomic<s64> claim_delivered_ms{0}; // our sign's reply carried a host's claim (0 = none open)
std::atomic<bool> was_in_session{false};

s64 NowMs() {
    return static_cast<s64>(GetTickCount64());
}

// ---- host_overrides.json ------------------------------------------------------------------------

#ifdef _WIN32
std::string ReadFile(const std::wstring& path) {
    std::ifstream in(path, std::ios::binary);
    std::stringstream text;
    text << in.rdbuf();
    return text.str();
}

// {"prefix": "replacement", ...} - flat string pairs, as JOIN-HOST writes them.
void LoadOverrides() {
    wchar_t exe[MAX_PATH]{};
    GetModuleFileNameW(nullptr, exe, MAX_PATH);
    std::wstring dir{exe};
    const std::wstring exe_name = dir.substr(dir.find_last_of(L"\\/") + 1);
    dir = dir.substr(0, dir.find_last_of(L"\\/") + 1);
    // bbhost sends the game's URLs to its own server ([online] host) itself. shadPS4's
    // host_overrides.json on the same PC pointed them at another server (2026-10-12: game API on
    // the shadPS4 server, NP sessions on bbhost's - nothing matched). BBSC_URL_OVERRIDES=0 does the
    // same for any host.
    const char* switch_env = std::getenv("BBSC_URL_OVERRIDES");
    if (_wcsnicmp(exe_name.c_str(), L"bbhost", 6) == 0 || (switch_env && switch_env[0] == '0')) {
        LOG_INFO(Mod, "HTTP: URL overrides off ({}) - the host sends the game's URLs itself",
                 switch_env && switch_env[0] == '0' ? "BBSC_URL_OVERRIDES=0" : "bbhost");
        return;
    }
    // The emulator's own rule: a "user" folder in the folder it was started in wins (portable).
    wchar_t cwd[MAX_PATH]{};
    GetCurrentDirectoryW(MAX_PATH, cwd);
    std::vector<std::wstring> candidates{std::wstring(cwd) + L"\\user\\host_overrides.json",
                                        dir + L"user\\host_overrides.json"};
    if (const wchar_t* appdata = _wgetenv(L"APPDATA")) {
        candidates.push_back(std::wstring(appdata) + L"\\shadPS4\\host_overrides.json");
    }
    for (const auto& path : candidates) {
        const std::string json = ReadFile(path);
        std::vector<std::string> strings;
        for (size_t at = json.find('"'); at != std::string::npos; at = json.find('"', at)) {
            const size_t end = json.find('"', at + 1);
            if (end == std::string::npos) {
                break;
            }
            strings.push_back(json.substr(at + 1, end - at - 1));
            at = end + 1;
        }
        for (size_t i = 0; i + 1 < strings.size(); i += 2) {
            overrides.emplace_back(strings[i], strings[i + 1]);
        }
        if (!overrides.empty()) {
            LOG_INFO(Mod, "HTTP: {} URL override(s) from host_overrides.json", overrides.size());
            return;
        }
    }
    LOG_INFO(Mod, "HTTP: no host_overrides.json - URLs unchanged");
}
#else
// bbport: the online module applies the user folder's host_overrides itself, to every URL the game
// sends; applying them here as well would rewrite them twice.
void LoadOverrides() {
    LOG_INFO(Mod, "HTTP: URL overrides left to bbport's online module");
}
#endif

// 0.0.0.0 is a server's "listen on everything", never an address to connect to. A game server
// started with it as its shadnet address (seen 2026-10-01 under Nucleus Co-op with
// NoDreamForHunter's server) puts it into ss.info, and every summon sign call then fails with
// "Could not establish connection". It can only have meant this PC.
std::string FixAnyAddress(std::string text) {
    for (const char* scheme : {"http://0.0.0.0", "https://0.0.0.0"}) {
        const std::string prefix = scheme;
        if (text.rfind(prefix, 0) == 0 &&
            (text.size() == prefix.size() || text[prefix.size()] == ':' ||
             text[prefix.size()] == '/')) {
            static bool logged = false;
            if (!logged) {
                logged = true;
                LOG_WARNING(Mod, "HTTP: the server list sends the game to 0.0.0.0 ({}) - using "
                                 "127.0.0.1 instead. Start the game server with a real shadnet "
                                 "address.",
                            text);
            }
            return text.replace(prefix.size() - 7, 7, "127.0.0.1");
        }
    }
    return text;
}

std::string Override(const char* url) {
    std::string text = FixAnyAddress(url != nullptr ? url : "");
    for (const auto& [prefix, replacement] : overrides) {
        if (text.rfind(prefix, 0) == 0) {
            return replacement + text.substr(prefix.size());
        }
    }
    return text;
}

// ---- Summon paths -------------------------------------------------------------------------------

bool Contains(const std::string& url, const char* part) {
    return url.find(part) != std::string::npos;
}
bool IsSummon(const std::string& url) {
    return Contains(url, "/summon_messenger/");
}
bool IsSummonCreate(const std::string& url) {
    return Contains(url, "/summon_messenger/create");
}

bool IsSummonSearch(const std::string& url) {
    return Contains(url, "/summon_messenger/request") || Contains(url, "/summon_messenger/get");
}

// Public servers (2026-10-09): The Hunter's Dream (and the other community servers) let mods in as
// long as the game's API calls are not changed. On them BBSC adds no headers, rewrites no sign and
// sends no deletes - the seamless broker extras exist only on a BBSC host's shadnet-p2p server.
bool IsPublicServer(const std::string& url) {
    static constexpr std::array<const char*, 4> Hosts{"thehuntersdream.com", "nodreamforthehunter.com",
                                                      "shadps4.net", "scej-network.jp"};
    const size_t scheme = url.find("://");
    const size_t start = scheme == std::string::npos ? 0 : scheme + 3;
    const std::string host = url.substr(start, url.find_first_of(":/", start) - start);
    for (const char* known : Hosts) {
        const size_t len = std::strlen(known);
        if (host.size() >= len && host.compare(host.size() - len, len, known) == 0) {
            return true;
        }
    }
    return false;
}

// "AreaId":<digits> -> the host's map, when connect-first has one. Returns true if changed.
bool RewriteAreaId(std::string& body) {
    const auto host_map = Core::Bloodborne::GetBbscConnectFirstAreaId();
    if (!host_map) {
        return false;
    }
    const std::string key = "\"AreaId\":";
    const size_t at = body.find(key);
    if (at == std::string::npos) {
        return false;
    }
    const size_t begin = at + key.size();
    size_t end = begin;
    while (end < body.size() && body[end] >= '0' && body[end] <= '9') {
        ++end;
    }
    const std::string original = body.substr(begin, end - begin);
    const std::string replacement = std::to_string(*host_map);
    if (end == begin || original == replacement) {
        return false;
    }
    body.replace(begin, end - begin, replacement);
    LOG_INFO(Mod, "HTTP: connect-first - sign AreaId {} -> {}", original, replacement);
    return true;
}

std::string JsonString(const std::string& body, const char* key) {
    const std::string needle = std::string("\"") + key + "\":\"";
    const size_t at = body.find(needle);
    if (at == std::string::npos) {
        return {};
    }
    const size_t begin = at + needle.size();
    const size_t end = body.find('"', begin);
    return end == std::string::npos ? std::string{} : body.substr(begin, end - begin);
}

std::string JsonNumber(const std::string& body, const char* key) {
    const std::string needle = std::string("\"") + key + "\":";
    const size_t at = body.find(needle);
    if (at == std::string::npos) {
        return {};
    }
    size_t end = at + needle.size();
    while (end < body.size() && (std::isdigit(static_cast<unsigned char>(body[end])) || body[end] == '-')) {
        ++end;
    }
    return body.substr(at + needle.size(), end - at - needle.size());
}

#ifdef _WIN32
// One plain POST with WinHTTP (the stale-record delete). Returns the status code, 0 on failure.
DWORD Post(const std::string& url, const std::string& body) {
    std::wstring wide(url.begin(), url.end());
    URL_COMPONENTS parts{sizeof(parts)};
    wchar_t host[256]{};
    wchar_t path[2048]{};
    parts.lpszHostName = host;
    parts.dwHostNameLength = 256;
    parts.lpszUrlPath = path;
    parts.dwUrlPathLength = 2048;
    if (!WinHttpCrackUrl(wide.c_str(), 0, 0, &parts)) {
        return 0;
    }
    DWORD status = 0;
    HINTERNET session = WinHttpOpen(L"BBSC", WINHTTP_ACCESS_TYPE_NO_PROXY, nullptr, nullptr, 0);
    HINTERNET connect = session ? WinHttpConnect(session, host, parts.nPort, 0) : nullptr;
    HINTERNET request =
        connect ? WinHttpOpenRequest(connect, L"POST", path, nullptr, nullptr, nullptr,
                                     parts.nScheme == INTERNET_SCHEME_HTTPS ? WINHTTP_FLAG_SECURE : 0)
                : nullptr;
    if (request != nullptr) {
        WinHttpSetTimeouts(request, 1000, 1000, 1000, 1500);
        const wchar_t* headers =
            L"Content-Type: application/json\r\nX-ShadPS4-Bloodborne-Seamless: 1\r\n";
        if (WinHttpSendRequest(request, headers, static_cast<DWORD>(-1),
                               const_cast<char*>(body.data()), static_cast<DWORD>(body.size()),
                               static_cast<DWORD>(body.size()), 0) &&
            WinHttpReceiveResponse(request, nullptr)) {
            DWORD size = sizeof(status);
            WinHttpQueryHeaders(request, WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
                                nullptr, &status, &size, nullptr);
        }
    }
    for (HINTERNET h : {request, connect, session}) {
        if (h != nullptr) {
            WinHttpCloseHandle(h);
        }
    }
    return status;
}
#else
// bbport: one plain HTTP POST over a socket (the stale-record delete goes to the summon broker,
// shadNet's WebAPI, over http). Returns the status code, 0 on failure; https is not done here.
DWORD Post(const std::string& url, const std::string& body) {
    constexpr std::string_view Scheme = "http://";
    if (url.rfind(Scheme, 0) != 0) {
        return 0;
    }
    const std::string rest = url.substr(Scheme.size());
    const size_t slash = rest.find('/');
    const std::string authority = rest.substr(0, slash);
    const std::string path = slash == std::string::npos ? "/" : rest.substr(slash);
    std::string host = authority, port = "80";
    if (const size_t colon = authority.rfind(':'); colon != std::string::npos) {
        host = authority.substr(0, colon);
        port = authority.substr(colon + 1);
    }
    addrinfo hints{};
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;
    addrinfo* found = nullptr;
    if (getaddrinfo(host.c_str(), port.c_str(), &hints, &found) != 0 || found == nullptr) {
        return 0;
    }
    const SOCKET s = socket(found->ai_family, found->ai_socktype, found->ai_protocol);
    const timeval timeout{1, 500'000};
    if (s != INVALID_SOCKET) {
        setsockopt(s, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout));
        setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
    }
    const bool connected =
        s != INVALID_SOCKET && connect(s, found->ai_addr, found->ai_addrlen) == 0;
    freeaddrinfo(found);
    if (!connected) {
        if (s != INVALID_SOCKET) {
            closesocket(s);
        }
        return 0;
    }
    const std::string request = "POST " + path + " HTTP/1.0\r\nHost: " + authority +
                                "\r\nContent-Type: application/json\r\n"
                                "X-ShadPS4-Bloodborne-Seamless: 1\r\nContent-Length: " +
                                std::to_string(body.size()) + "\r\nConnection: close\r\n\r\n" + body;
    DWORD status = 0;
    if (send(s, request.data(), request.size(), MSG_NOSIGNAL) == static_cast<ssize_t>(request.size())) {
        char reply[64]{};
        const ssize_t got = recv(s, reply, sizeof(reply) - 1, 0);
        // "HTTP/1.x NNN ..."
        if (got > 12 && std::strncmp(reply, "HTTP/", 5) == 0) {
            status = static_cast<DWORD>(std::atoi(reply + 9));
        }
    }
    closesocket(s);
    return status;
}
#endif

// The broker keeps Preparing/Claimed/Delivered records 15 minutes and Bloodborne reuses its
// SessionId/UserId after a restart, so the first seamless sign of this run removes any old one.
void ClearStaleRecord(const std::string& url, const std::string& body) {
    if (stale_cleared.exchange(true)) {
        return;
    }
    const std::string session = JsonString(body, "SessionId");
    const std::string user = JsonNumber(body, "UserId");
    if (session.empty() || user.empty()) {
        return;
    }
    std::string removal_url = url;
    removal_url.replace(removal_url.find("/summon_messenger/create"),
                        std::strlen("/summon_messenger/create"), "/summon_messenger/delete");
    const std::string removal = "{\"MessageId\":\"SummonDataRemoveRequest\",\"SessionId\":\"" +
                                session + "\",\"UserId\":" + user + ",\"Force\":true}";
    // It must finish before the new sign is created (the delete names the same session), so it
    // stays on this thread - the game's - with short timeouts (2026-10-08: up to 14 s before).
    const DWORD status = Post(removal_url, removal);
    LOG_INFO(Mod, "HTTP: stale summon cleanup for session {} user {}: status {}", session, user,
             status);
}

// ---- Stuck claims (2026-10-06) -------------------------------------------------------------------
// 4-player Nucleus test: one guest never joined and another waited minutes. In seamless mode the
// broker keeps a claimed sign 15 minutes (Preparing/Claimed/Delivered) and, every time that guest
// posts a sign again, hands back the OLD claim - from a host room that is gone or a join the game
// already gave up on. The host's searches list the same record, and its new claims are refused as
// conflicts. Nothing frees it but the 15-minute expiry or a forced delete, and the forced delete
// only ran once per game start. Now it runs again (on the next sign) when:
//   - the broker delivered a claim and no join followed within ClaimJoinWaitMs, or
//   - we were in a session (joining, guest or host) and are back to posting signs.
s32 SessionState() {
    const u64 manager = *reinterpret_cast<const u64*>(BbscMod::EbootAddress() + 0x05540290);
#ifndef _WIN32
    // bbport: the game's memory map instead of VirtualQuery.
    if (manager >= 0x10000 && Core::Memory::Instance()->IsValidMapping(manager + 0x124, 4)) {
        return *reinterpret_cast<const s32*>(manager + 0x124);
    }
    return -1;
#else
    MEMORY_BASIC_INFORMATION info{};
    constexpr DWORD Readable = PAGE_READONLY | PAGE_READWRITE | PAGE_WRITECOPY | PAGE_EXECUTE_READ |
                               PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY;
    if (manager >= 0x10000 && VirtualQuery(reinterpret_cast<void*>(manager + 0x124), &info,
                                           sizeof(info)) != 0 &&
        info.State == MEM_COMMIT && (info.Protect & Readable) != 0 &&
        (info.Protect & (PAGE_GUARD | PAGE_NOACCESS)) == 0) {
        return *reinterpret_cast<const s32*>(manager + 0x124);
    }
    return -1;
#endif
}

void WatchSessionForStaleClaims() {
    const s32 state = SessionState();
    if (state == 3 || state == 4 || state == 6) {
        was_in_session = true;
        if (claim_delivered_ms.exchange(0) != 0) {
            LOG_INFO(Mod, "HTTP: the delivered claim became a join (session state {})", state);
        }
        return;
    }
    if (state != 0) {
        return;
    }
    if (was_in_session.exchange(false)) {
        stale_cleared = false;
        LOG_INFO(Mod, "HTTP: session over - the next sign first clears our old broker record");
    }
    const s64 delivered = claim_delivered_ms.load();
    if (delivered != 0 && NowMs() - delivered > ClaimJoinWaitMs) {
        claim_delivered_ms = 0;
        stale_cleared = false;
        LOG_WARNING(Mod, "HTTP: a host's claim was delivered {} s ago and never became a join - "
                         "the next sign first clears it",
                    (NowMs() - delivered) / 1000);
    }
}

// ---- The wrappers -------------------------------------------------------------------------------

int PS4_SYSV_ABI CreateConnectionWithURL(int template_id, const char* url, bool keepalive) {
    const std::string target = Override(url);
    return original_create_connection(template_id, target.c_str(), keepalive);
}

int PS4_SYSV_ABI CreateRequestWithURL(int connection, s32 method, const char* url, u64 length) {
    const std::string target = Override(url);
    const int request = original_create_request(connection, method, target.c_str(), length);
    if (request > 0) {
        std::scoped_lock lock{state_mutex};
        request_urls[request] = target;
    }
    return request;
}

// A slot's value when it holds an emulator function (outside the eboot), else 0.
u64 CurrentSlot(u64 slot_offset) {
    const u64 base = BbscMod::EbootAddress();
    const u64 value = *reinterpret_cast<const volatile u64*>(base + slot_offset);
    return value != 0 && (value < base || value >= base + EbootSize) ? value : 0;
}

int PS4_SYSV_ABI SendRequest(int request, const void* data, u64 size) {
    std::string url;
    {
        std::scoped_lock lock{state_mutex};
        if (const auto it = request_urls.find(request); it != request_urls.end()) {
            url = it->second;
        }
    }
    WatchSessionForStaleClaims();
    if (!IsSummon(url)) {
        return original_send(request, data, size);
    }
    if (IsPublicServer(url)) {
        static std::atomic<bool> logged{false};
        if (!logged.exchange(true)) {
            LOG_INFO(Mod, "HTTP: summon requests go to a public server - sent unchanged (no "
                          "seamless headers, connect-first or cleanup)");
        }
        return original_send(request, data, size);
    }
    // Not wrapped, so the slots always hold the emulator's current functions: read them again at
    // use (review 2026-10-11 - the official shadPS4 links the imports again after start-up).
    if (const u64 add = CurrentSlot(SlotAddHeader); add != 0) {
        original_add_header = reinterpret_cast<AddHeaderFn>(add);
    }
    if (const u64 length = CurrentSlot(SlotSetContentLength); length != 0) {
        original_set_content_length = reinterpret_cast<SetContentLengthFn>(length);
    }
    if (original_add_header == nullptr || original_set_content_length == nullptr) {
        return original_send(request, data, size); // (review 2026-10-08) the slots never filled
    }
    original_add_header(request, "X-ShadPS4-Bloodborne-Seamless", "1", 0);
    if (IsSummonSearch(url)) {
        // bbport (issue #17): a host ringing a sign sends its placement to that sign's owner only
        // (its TargetUserId), with the header for the broker; nothing goes to the whole server.
        const std::string body = data != nullptr && size != 0
                                     ? std::string(static_cast<const char*>(data), static_cast<size_t>(size))
                                     : std::string{};
        std::string target_text = JsonNumber(body, "TargetUserId");
        if (target_text.empty()) {
            target_text = JsonString(body, "TargetUserId");
        }
        if (!target_text.empty()) {
            const s64 target = std::strtoll(target_text.c_str(), nullptr, 10);
            const auto placement = Core::Bloodborne::GetSeamlessHostPlacementHeader();
            if (placement && target > 0) {
                original_add_header(request, "X-ShadPS4-Bloodborne-Host-Placement",
                                    placement->c_str(), 0);
                BbscMod::RelaySendPlacementTo(target, *placement);
                LOG_INFO(Mod, "HTTP: ringing the sign of user {} - our placement {} sent to it",
                         target, *placement);
            } else {
                LOG_INFO(Mod, "HTTP: ringing a sign - no placement sent (target user {}, "
                              "placement {})",
                         target_text, placement ? "known" : "none");
            }
        }
        return original_send(request, data, size);
    }
    if (IsSummonCreate(url) && data != nullptr && size != 0) {
        std::string body(static_cast<const char*>(data), static_cast<size_t>(size));
        ClearStaleRecord(url, body);
        // bbport (issue #17): the UserId our sign is posted under; a host ringing it sends its
        // placement to that id.
        std::string user = JsonNumber(body, "UserId");
        if (user.empty()) {
            user = JsonString(body, "UserId");
        }
        if (!user.empty()) {
            const s64 id = std::strtoll(user.c_str(), nullptr, 10);
            if (id > 0 && own_sign_user.exchange(id) != id) {
                LOG_INFO(Mod, "HTTP: our sign's user id is {}", id);
            }
        }
        // A host's placement that has not been refreshed for a while is a host that stopped
        // looking: forget it, as the emulator did when a create reply carried none.
        const s64 received = placement_received_ms.load();
        const s64 stale = placement_directed.load() ? DirectedPlacementStaleMs : PlacementStaleMs;
        if (received != 0 && NowMs() - received > stale) {
            placement_received_ms = 0;
            placement_sender = 0;
            placement_directed = false;
            Core::Bloodborne::ClearSeamlessHostPlacementHeader();
            LOG_INFO(Mod, "HTTP: no word from that host for a while - the sign goes back to our "
                          "own map");
        }
        if (RewriteAreaId(body)) {
            original_set_content_length(request, body.size());
            // The emulator copies the body during the call, so a local buffer is fine.
            return original_send(request, body.data(), body.size());
        }
    }
    return original_send(request, data, size);
}

// A sign's reply is a bare {"ResKind":0,"MessageId":"SummonDataCreateResponse"} unless the broker
// delivers a host's claim with it, which adds the claim's members (the host's UserId among them).
int PS4_SYSV_ABI ReadData(int request, void* data, u64 size) {
    const int read = original_read_data(request, data, size);
    if (read > 0 && data != nullptr) {
        std::string url;
        {
            std::scoped_lock lock{state_mutex};
            if (const auto it = request_urls.find(request); it != request_urls.end()) {
                url = it->second;
            }
        }
        // Public servers (2026-10-10: a host's summon never reached the guest on The Hunter's
        // Dream): every summon reply that is not a bare create answer goes into the log.
        if (IsSummon(url) && IsPublicServer(url)) {
            const std::string_view reply(static_cast<const char*>(data), static_cast<size_t>(read));
            const size_t q = url.find('?');
            const size_t slash = url.rfind('/', q);
            const std::string what = url.substr(slash + 1, q == std::string::npos ? q : q - slash - 1);
            const bool bare = reply.find("\"SummonDataCreateResponse\"") != std::string_view::npos &&
                              reply.size() <= 60;
            static std::atomic<int> bare_logged{0};
            if (what == "get") {
                // Sign lists hold other players' signs: only their size.
                LOG_INFO(Mod, "HTTP: summon reply (get, {} bytes)", read);
            } else if (!bare || bare_logged.fetch_add(1) < 2) {
                std::string text(reply.substr(0, 400));
                for (char& c : text) {
                    if (static_cast<unsigned char>(c) < 0x20) {
                        c = '.';
                    }
                }
                LOG_INFO(Mod, "HTTP: summon reply ({}, {} bytes): {}", what, read, text);
            }
        }
        if (IsSummonCreate(url)) {
            const std::string_view reply(static_cast<const char*>(data), static_cast<size_t>(read));
            if (reply.find("\"UserId\"") != std::string_view::npos &&
                claim_delivered_ms.exchange(NowMs()) == 0) {
                LOG_INFO(Mod, "HTTP: a host's claim came with our sign ({} bytes) - waiting for the "
                              "join",
                         read);
            }
        }
    }
    return read;
}

int PS4_SYSV_ABI DeleteRequest(int request) {
    {
        std::scoped_lock lock{state_mutex};
        request_urls.erase(request);
    }
    return original_delete(request);
}

// Waits until the emulator has filled the slot (a host address, outside the eboot), then swaps
// it. The original goes into `original` BEFORE the slot points at the wrapper (review 2026-10-08:
// the game could call the wrapper before the original was stored). False if the slot never filled.
template <typename Fn>
bool Swap(u64 slot_offset, Fn wrapper, Fn& original, const char* name) {
    auto* slot = reinterpret_cast<u64*>(BbscMod::EbootAddress() + slot_offset);
    for (int i = 0; i < 60'000; ++i) {
        const u64 value = *slot;
        if (value != 0 && (value < BbscMod::EbootAddress() || value >= BbscMod::EbootAddress() + EbootSize)) {
            original = reinterpret_cast<Fn>(value);
            DWORD old = 0;
            VirtualProtect(slot, 8, PAGE_READWRITE, &old);
            *slot = reinterpret_cast<u64>(wrapper);
            DWORD ignored = 0;
            VirtualProtect(slot, 8, old, &ignored);
            BbscMod::GuardSlot(slot_offset, reinterpret_cast<u64>(wrapper),
                               reinterpret_cast<void**>(&original), name);
            return true;
        }
        Sleep(1);
    }
    return false;
}

// The two slots read, not swapped: waits for them as Swap does (they are filled at the same time).
u64 WaitForSlot(u64 slot_offset) {
    const auto* slot = reinterpret_cast<const u64*>(BbscMod::EbootAddress() + slot_offset);
    for (int i = 0; i < 60'000; ++i) {
        const u64 value = *slot;
        if (value != 0 && (value < BbscMod::EbootAddress() || value >= BbscMod::EbootAddress() + EbootSize)) {
            return value;
        }
        Sleep(1);
    }
    return 0;
}

} // namespace

namespace BbscMod {

// The relay asks before connecting (bbsc_relay.cpp): public servers run no BBSC relay.
bool IsPublicServerAddress(const std::string& url_or_host) {
    return IsPublicServer(url_or_host);
}

// A host's placement from the relay: what the broker's reply header carried in the emulator
// build. bbport (issue #17): a placement sent to the whole server is ignored, as BBSC's bbsc.dll of
// 2026-10-17 does ("an old host - it must update BBSC"): following any host on a busy server sent
// a guest's sign to a stranger's map.
void OnHostPlacement(const std::string& placement, u32 sender) {
    static std::atomic<bool> logged{false};
    if (!logged.exchange(true)) {
        LOG_INFO(Mod, "HTTP: placement broadcast from {:08x} ignored (an old host - it must "
                      "update BBSC): {}",
                 sender, placement);
    }
}

// bbport (issue #17): the placement of the host that rang our sign, sent to its UserId. Used only
// by a player who is not in a session yet (a guest waiting to be summoned).
void OnDirectedPlacement(s64 target_user, const std::string& placement, u32 sender) {
    const s64 own = own_sign_user.load();
    if (own == 0 || target_user != own) {
        return; // another player's sign
    }
    const s32 state = SessionState();
    if (state == 3 || state == 4 || state == 6) {
        return; // hosting, joining or already a guest
    }
    // Our host by who it is: its world flags are taken before the join load, and the guest locks
    // onto it among the other hosts on the server (bloodborne_re.cpp, BbscRangHost; BBSC 0.0.2).
    Core::Bloodborne::NoteBbscHostRangOurSign(sender);
    if (Core::Bloodborne::SetSeamlessHostPlacementHeader(placement)) {
        placement_directed = true;
        placement_sender = sender;
        placement_received_ms = NowMs();
        LOG_INFO(Mod, "HTTP: host {:08x} rang our sign (user {}) - placement {}", sender,
                 target_user, placement);
    }
}

void InstallHttpWrappers() {
    LoadOverrides();
    original_add_header = reinterpret_cast<AddHeaderFn>(WaitForSlot(SlotAddHeader));
    original_set_content_length =
        reinterpret_cast<SetContentLengthFn>(WaitForSlot(SlotSetContentLength));
    Swap<CreateConnectionFn>(SlotCreateConnection, &CreateConnectionWithURL,
                             original_create_connection, "CreateConnectionWithURL");
    Swap<CreateRequestFn>(SlotCreateRequest, &CreateRequestWithURL, original_create_request,
                          "CreateRequestWithURL");
    Swap<SendFn>(SlotSend, &SendRequest, original_send, "SendRequest");
    Swap<DeleteFn>(SlotDelete, &DeleteRequest, original_delete, "DeleteRequest");
    Swap<ReadDataFn>(SlotReadData, &ReadData, original_read_data, "ReadData");
    const bool ok = original_create_connection && original_create_request && original_add_header &&
                    original_set_content_length && original_send && original_delete &&
                    original_read_data;
    LOG_INFO(Mod, "HTTP: game's HTTP calls {} (URL overrides, seamless summon, connect-first, stale "
                  "cleanup)",
             ok ? "wrapped" : "NOT wrapped - an import slot was never filled");
}

} // namespace BbscMod
