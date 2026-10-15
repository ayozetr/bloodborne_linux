// SPDX-FileCopyrightText: Copyright 2026 CLS_AMG
// SPDX-License-Identifier: GPL-2.0-or-later

// bbport: the Linux counterpart of emulator/mod/bbsc_mod.cpp - BBSC as a library (libbbsc.so)
// that bb-probe loads into the game's process (BB_BBSC_LIB) instead of a DLL injected into
// shadPS4. The steps are the DLL's, and the patch site logic below is its code unchanged:
//   1. wait until every byte patch site reads back as the bytes that must be there (all of them
//      before writing any - another game or version is left alone);
//   2. write the byte patches (core/bbsc_patch_tables.h);
//   3. install every hook with core/bloodborne_re.cpp, compiled into this library with BBSC_MOD;
//   4. keep watching: a patch site written back is written again.
// What differs on Linux: the game is always at 0x800000000 (bbport, as the shadp2p fork); memory
// questions are answered from bbport's own map of the game's memory (runtime_memory_vma_info, no
// system call); the log goes to <user dir>/bbsc/logs/ and its warnings to the game's log; the F1 /
// L3+R3 cinematic camera and BBSC's own Discord status are not in this build (bbport has its own
// Discord status, and L3+R3 opens bbport's menu).

#include <dlfcn.h>
#include <sys/mman.h>
#include <unistd.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <filesystem>
#include <mutex>
#include <string>
#include <vector>

#include "linux/bbsc_win32.h"

#include "common/logging/log.h"
#include "common/memory_patcher.h"
#include "common/path_util.h"
#include "core/bbsc_cinematic.h"
#include "core/bbsc_patch_tables.h"
#include "core/bloodborne_re.h"
#include "core/debugger.h"
#include "core/libraries/np/np_matching2/np_matching2_mm.h"
#include "core/memory.h"

// bbport's runtime (bb-probe exports it): the game's memory map.
extern "C" int runtime_memory_vma_info(uintptr_t address, int* prot, int* type, uintptr_t* end);

using namespace Core::Bbsc::PatchTables;

// Keep it equal to "version" in mod.json and to the Windows mod it plays with.
#define BBSC_VERSION "0.0.1"

namespace BbscMod {
void LogPlain(const char* text);
u64 EbootAddress();
void StartRelay();
void StartP2PChannel(); // bbsc_channel.cpp
bool GameServerIsPublic(std::string* host_out); // bbsc_relay.cpp
void InstallHttpWrappers();
} // namespace BbscMod

namespace {

constexpr u64 ForkEbootBase = 0x800000000ULL; // bbport and the shadp2p fork
u64 EbootBase = 0;
constexpr u64 EbootSize = 0x056D4000ULL; // CUSA03173 01.09 image size
// The image's code (its first PT_LOAD): made writable as shadPS4 maps it, since the shared hook
// code writes some code bytes directly.
constexpr u64 EbootCodeSize = 0x050DC000ULL;
constexpr DWORD WaitForImageMs = 180'000;
constexpr DWORD SettleMs = 20;
constexpr DWORD WatchMs = 500;

std::filesystem::path mod_dir;  // where libbbsc.so and its LICENSE/NOTICE/SUPPORTERS are
std::filesystem::path data_dir; // <user dir>/bbsc: logs, captures
FILE* log_file = nullptr;
std::mutex log_mutex;

// The newest `keep` files of a folder with this extension stay; older ones (earlier game starts)
// go. Each start writes a log and a capture of its own.
void KeepNewest(const std::filesystem::path& folder, const char* extension, size_t keep) {
    std::error_code ignored;
    std::vector<std::filesystem::directory_entry> files;
    for (const auto& entry : std::filesystem::directory_iterator(folder, ignored)) {
        if (entry.is_regular_file(ignored) && entry.path().extension() == extension) {
            files.push_back(entry);
        }
    }
    if (files.size() <= keep) {
        return;
    }
    std::sort(files.begin(), files.end(), [](const auto& a, const auto& b) {
        std::error_code e;
        return a.last_write_time(e) > b.last_write_time(e);
    });
    for (size_t i = keep; i < files.size(); ++i) {
        std::filesystem::remove(files[i].path(), ignored);
    }
}

void OpenLog() {
    Dl_info info{};
    if (dladdr(reinterpret_cast<void*>(&OpenLog), &info) != 0 && info.dli_fname != nullptr) {
        mod_dir = std::filesystem::path{info.dli_fname}.parent_path();
    }
    // The game's user folder (run.sh exports it as BB_GPU_USER_DIR). Not the working directory's
    // "user": in the AppImage that is inside its read-only mount, and BBSC installs none of its
    // hooks without a capture folder (InstallReverseEngineeringTrace) - with its death patch
    // still in, a death then never reloads. The temporary folder when the user folder is not
    // writable either.
    const char* user = std::getenv("BB_USER_DIR");
    if (user == nullptr || *user == '\0') {
        user = std::getenv("BB_GPU_USER_DIR");
    }
    data_dir = std::filesystem::path{user != nullptr && *user != '\0' ? user : "user"} / "bbsc";
    std::error_code ignored;
    std::filesystem::create_directories(data_dir / "captures" / "bloodborne-re", ignored);
    if (ignored) {
        data_dir = std::filesystem::temp_directory_path(ignored) / "bbport-bbsc";
        std::filesystem::create_directories(data_dir / "captures" / "bloodborne-re", ignored);
    }
    std::filesystem::create_directories(data_dir / "logs", ignored);
    KeepNewest(data_dir / "logs", ".log", 4); // with this one, 5
    KeepNewest(data_dir / "captures" / "bloodborne-re", ".jsonl", 4);
    const std::time_t now = std::time(nullptr);
    std::tm local{};
    localtime_r(&now, &local);
    char name[96];
    std::snprintf(name, sizeof(name), "bbsc-mod-%04d%02d%02d-%02d%02d%02d-%d.log",
                  local.tm_year + 1900, local.tm_mon + 1, local.tm_mday, local.tm_hour,
                  local.tm_min, local.tm_sec, static_cast<int>(getpid()));
    log_file = std::fopen((data_dir / "logs" / name).c_str(), "w");
    std::printf("BBSC: log %s\n", (data_dir / "logs" / name).c_str());
}

// ---- Memory --------------------------------------------------------------------------------------

// The game's own memory is in bbport's map; anything else (the image, host memory a game pointer
// should never reach) is checked with mincore, which fails on an unmapped page.
bool HostMapped(u64 address, size_t size) {
    const u64 page = static_cast<u64>(sysconf(_SC_PAGESIZE));
    const u64 first = address & ~(page - 1);
    const u64 last = (address + size - 1) & ~(page - 1);
    std::vector<unsigned char> pages((last - first) / page + 1);
    return mincore(reinterpret_cast<void*>(first), last - first + page, pages.data()) == 0;
}

bool Readable(u64 address, size_t size) {
    if (address == 0 || address + size < address) {
        return false;
    }
    if (EbootBase != 0 && address >= EbootBase && address + size <= EbootBase + EbootSize) {
        return true;
    }
    u64 at = address;
    const u64 end = address + size;
    while (at < end) {
        int prot = 0, type = 0;
        uintptr_t region_end = 0;
        if (!runtime_memory_vma_info(at, &prot, &type, &region_end)) {
            return HostMapped(at, end - at);
        }
        if ((prot & 1) == 0) { // PS4 CPU read
            return false;
        }
        at = region_end;
    }
    return true;
}

bool MatchesAt(u64 base, u64 offset, const u8* bytes, size_t size) {
    const u64 address = base + offset;
    return Readable(address, size) &&
           std::memcmp(reinterpret_cast<const void*>(address), bytes, size) == 0;
}

bool Matches(u64 offset, const u8* bytes, size_t size) {
    const u64 address = EbootBase + offset;
    return Readable(address, size) &&
           std::memcmp(reinterpret_cast<const void*>(address), bytes, size) == 0;
}

void Write(u64 offset, const u8* bytes, size_t size) {
    void* address = reinterpret_cast<void*>(EbootBase + offset);
    DWORD old = 0;
    if (!VirtualProtect(address, size, PAGE_EXECUTE_READWRITE, &old)) {
        return;
    }
    std::memcpy(address, bytes, size);
}

// ---- Byte patches (bbsc_mod.cpp, unchanged) ------------------------------------------------------

struct Site {
    const char* name;
    u64 offset;
    std::array<u8, 6> original{};
    std::array<u8, 6> patched{};
    size_t size;
    Group group;
};

template <size_t N>
std::array<u8, 6> Pad(const std::array<u8, N>& bytes) {
    std::array<u8, 6> out{};
    std::memcpy(out.data(), bytes.data(), N);
    return out;
}

constexpr size_t SiteCount =
    Retargets.size() + EntryReturns.size() + ByteEdits.size() + WideEdits.size() + EntryJumps.size();
std::array<Site, SiteCount> sites{};
std::mutex patch_mutex;
bool patches_ready = false;
bool session_on = true; // session groups: off while a suspension runs
bool role_on = false;   // role groups (lamp): on while hosting

void BuildSites() {
    size_t i = 0;
    for (const auto& e : Retargets) {
        sites[i++] = {e.name, e.site, Pad(EncodeRel32(e.opcode, e.site, e.original)),
                      Pad(EncodeRel32(e.opcode, e.site, e.target)), 5, e.group};
    }
    for (const auto& e : EntryReturns) {
        std::array<u8, 6> ret{};
        ret[0] = 0xC3;
        sites[i++] = {e.name, e.site, e.prologue, ret, 1, e.group};
    }
    for (const auto& e : ByteEdits) {
        sites[i++] = {e.name, e.site, Pad(e.original), Pad(e.replacement), 2, e.group};
    }
    for (const auto& e : WideEdits) {
        sites[i++] = {e.name, e.site, Pad(e.original), Pad(e.replacement), 4, e.group};
    }
    for (const auto& e : EntryJumps) {
        sites[i++] = {e.name, e.site, Pad(e.prologue), Pad(EncodeRel32(0xE9, e.site, e.target)), 5,
                      e.group};
    }
}

bool AllSitesKnown(const Site** first_bad) {
    for (const Site& s : sites) {
        if (!GroupEnabled(s.group)) {
            continue;
        }
        if (s.offset + s.size > EbootSize ||
            (!Matches(s.offset, s.original.data(), s.size) &&
             !Matches(s.offset, s.patched.data(), s.size))) {
            *first_bad = &s;
            return false;
        }
    }
    return true;
}

bool Wanted(const Site& s) {
    if (!GroupEnabled(s.group)) {
        return false;
    }
    if (IsRoleGroup(s.group)) {
        return role_on;
    }
    if (IsSessionGroup(s.group)) {
        return session_on;
    }
    return true;
}

int SyncSites() {
    int count = 0;
    for (const Site& s : sites) {
        if (!GroupEnabled(s.group)) {
            continue;
        }
        const auto& want = Wanted(s) ? s.patched : s.original;
        if (!Matches(s.offset, want.data(), s.size)) {
            Write(s.offset, want.data(), s.size);
            ++count;
        }
    }
    return count;
}

// ---- Start-up ------------------------------------------------------------------------------------

// BBSC's license, notice and supporters travel with it (next to libbbsc.so); missing or changed,
// BBSC stays off and says why, as the Windows mod does.
bool NoticesPresent() {
    const auto holds = [](const char* name, const char* text) {
        FILE* file = std::fopen((mod_dir / name).c_str(), "rb");
        if (file == nullptr) {
            return false;
        }
        std::string content(64 * 1024, '\0');
        content.resize(std::fread(content.data(), 1, content.size(), file));
        std::fclose(file);
        return content.find(text) != std::string::npos;
    };
    return holds("LICENSE.txt", "GNU GENERAL PUBLIC LICENSE") &&
           holds("NOTICE.txt", "github.com/Classmg22/BBSC") &&
           holds("SUPPORTERS.txt", "BBSC SUPPORTERS");
}

DWORD WINAPI Worker(void*) {
    OpenLog();
    BbscMod::LogPlain("BBSC mod loaded - version " BBSC_VERSION " (bbport, Linux)");
    if (!NoticesPresent()) {
        LOG_ERROR(Mod, "LICENSE.txt / NOTICE.txt / SUPPORTERS.txt missing or changed in {} - BBSC "
                       "is off",
                  mod_dir.string());
        return 0;
    }
    LOG_INFO(Mod, "BBSC mod in pid {}", static_cast<int>(getpid()));
    {
        std::string server;
        if (BbscMod::GameServerIsPublic(&server)) {
            setenv("BBSC_MOD_SEAMLESS", "0", 1);
            setenv("SHADPS4_BBSC_FIVE_HUNTERS", "0", 1);
            LOG_INFO(Mod, "Public game server ({}): vanilla summons - seamless summon patches and the "
                          "5-hunter search off (the session itself stays seamless)",
                     server);
        }
    }
    BuildSites();

    // bbport loads the game at the fork's address before any of its code runs.
    EbootBase = ForkEbootBase;
    const DWORD started = GetTickCount();
    if (mprotect(reinterpret_cast<void*>(EbootBase), EbootCodeSize,
                 PROT_READ | PROT_WRITE | PROT_EXEC) == 0) {
        LOG_INFO(Mod, "Game code made writable, as shadPS4 maps it");
    }
    const Site* bad = nullptr;
    while (!AllSitesKnown(&bad)) {
        if (GetTickCount() - started > WaitForImageMs) {
            LOG_ERROR(Mod,
                      "No Bloodborne CUSA03173 01.09 image after {} s (first unknown site: {} at "
                      "{:#x}) - not this game or not this version; nothing was changed",
                      WaitForImageMs / 1000, bad ? bad->name : "?", bad ? bad->offset : 0);
            return 0;
        }
        Sleep(1);
    }
    Sleep(SettleMs);
    const DWORD verified = GetTickCount() - started;

    MemoryPatcher::g_eboot_address = EbootBase;
    MemoryPatcher::g_eboot_image_size = EbootSize;
    MemoryPatcher::g_game_serial = "CUSA03173";

    // Wozzardman's seamless patches first: one of them (0x019471B1) is also in BBSC's list, and it
    // checks for the original bytes.
    Core::Bloodborne::InstallSeamlessCoopPatches();

    int written = 0;
    {
        std::scoped_lock lock{patch_mutex};
        patches_ready = true;
        written = SyncSites();
    }
    LOG_INFO(Mod, "Image verified after {} ms: {} byte patch sites written", verified, written);

    Core::Bloodborne::InstallReverseEngineeringTrace();
    BbscMod::StartRelay();
    BbscMod::StartP2PChannel();
    BbscMod::InstallHttpWrappers();
    LOG_INFO(Mod, "BBSC mod ready after {} ms", GetTickCount() - started);

    for (;;) {
        Sleep(WatchMs);
        std::scoped_lock lock{patch_mutex};
        if (const int redone = SyncSites(); redone != 0) {
            LOG_WARNING(Mod, "{} patch site(s) had changed back - written again", redone);
        }
    }
}

} // namespace

// ---- Logging -------------------------------------------------------------------------------------

namespace BbscMod {

void LogLine(char level, const char* category, const std::string& text) {
    std::scoped_lock lock{log_mutex};
    // The game's log gets the mod's own lines and every warning or error.
    if (level == 'W' || level == 'E' || std::strcmp(category, "Mod") == 0) {
        std::printf("BBSC: %c %s: %s\n", level, category, text.c_str());
    }
    if (log_file == nullptr) {
        return;
    }
    timespec now{};
    clock_gettime(CLOCK_REALTIME, &now);
    std::tm local{};
    localtime_r(&now.tv_sec, &local);
    std::fprintf(log_file, "[%02d:%02d:%02d.%03ld] %c %s: %s\n", local.tm_hour, local.tm_min,
                 local.tm_sec, now.tv_nsec / 1'000'000, level, category, text.c_str());
    std::fflush(log_file);
}

void LogPlain(const char* text) {
    LogLine('I', "Mod", text);
}

u64 EbootAddress() {
    return EbootBase;
}

// Import slots swapped for wrappers (bbsc_http.cpp, bbsc_channel.cpp): put back if anything links
// them again (bbport links the imports once, before the game runs; kept as the Windows mod has it).
namespace {
struct GuardedSlot {
    u64 slot_offset;
    u64 wrapper;
    void** original;
    const char* name;
    int rewritten = 0;
};
std::mutex guarded_mutex;
std::vector<GuardedSlot> guarded_slots;

DWORD WINAPI SlotGuardThread(void*) {
    for (;;) {
        Sleep(5);
        std::scoped_lock lock{guarded_mutex};
        for (auto& guarded : guarded_slots) {
            auto* slot = reinterpret_cast<volatile u64*>(EbootBase + guarded.slot_offset);
            const u64 value = *slot;
            if (value == guarded.wrapper || value == 0 ||
                (value >= EbootBase && value < EbootBase + EbootSize)) {
                continue;
            }
            *reinterpret_cast<void* volatile*>(guarded.original) = reinterpret_cast<void*>(value);
            DWORD old = 0;
            VirtualProtect(const_cast<u64*>(slot), 8, PAGE_READWRITE, &old);
            *slot = guarded.wrapper;
            if (++guarded.rewritten <= 3) {
                LOG_INFO(Mod, "Import {} was linked again - wrapper put back ({}x)", guarded.name,
                         guarded.rewritten);
            }
        }
    }
}
} // namespace

void GuardSlot(u64 slot_offset, u64 wrapper, void** original, const char* name) {
    std::scoped_lock lock{guarded_mutex};
    if (guarded_slots.empty()) {
        CreateThread(nullptr, 0, SlotGuardThread, nullptr, 0, nullptr);
    }
    guarded_slots.push_back({slot_offset, wrapper, original, name});
}

void StartDiscordStatus() {} // bbport has its own Discord status

} // namespace BbscMod

// ---- What bloodborne_re.cpp asks the emulator for ----------------------------------------------

namespace Core {

bool MemoryManager::IsValidMapping(u64 address, u64 size) {
    return Readable(address, size == 0 ? 1 : size);
}

// The PS4 protection bits (1 read, 2 write, 4 execute) of the region at address. bbport's map
// gives where the region ends; its start is reported as the address's own page.
s32 MemoryManager::QueryProtection(u64 address, void** start, void** end, u32* prot) {
    const u64 page = static_cast<u64>(sysconf(_SC_PAGESIZE));
    if (EbootBase != 0 && address >= EbootBase && address < EbootBase + EbootSize) {
        *start = reinterpret_cast<void*>(EbootBase);
        *end = reinterpret_cast<void*>(EbootBase + EbootSize);
        *prot = address < EbootBase + EbootCodeSize ? 7u : 3u;
        return 0;
    }
    int region_prot = 0, type = 0;
    uintptr_t region_end = 0;
    if (!runtime_memory_vma_info(address, &region_prot, &type, &region_end)) {
        return -1;
    }
    *start = reinterpret_cast<void*>(address & ~(page - 1));
    *end = reinterpret_cast<void*>(region_end);
    *prot = static_cast<u32>(region_prot) & 7u;
    return 0;
}

namespace Debugger {
int GetCurrentPid() {
    return static_cast<int>(getpid());
}
} // namespace Debugger

namespace Bbsc {

void InstallPersistentSessionPatches() {} // applied by Worker

void SetPersistentSessionPatches(bool enabled) {
    std::scoped_lock lock{patch_mutex};
    if (!patches_ready || session_on == enabled) {
        return;
    }
    session_on = enabled;
    const int count = SyncSites();
    LOG_INFO(Debug, "BBSC persistence {} ({} session sites; echoes, lamp, fog walls and deaths "
                    "untouched)",
             enabled ? "re-applied" : "suspended", count);
}

void SetHostLampPatches(bool hosting) {
    std::scoped_lock lock{patch_mutex};
    if (!patches_ready || role_on == hosting) {
        return;
    }
    role_on = hosting;
    const int count = SyncSites();
    LOG_INFO(Debug, "BBSC lamp: {} ({} sites)",
             hosting ? "prompt allowed (hosting a session)"
                     : "vanilla gates (solo or guest - a guest never gets the lamp)",
             count);
}

// The cinematic camera is not in the Linux build: it stays off.
CinematicInput TakeCinematicInput() {
    return CinematicInput{};
}
void CinematicForceOff() {}
void CinematicForceOn() {}

} // namespace Bbsc
} // namespace Core

namespace Common::FS {
std::filesystem::path GetUserPath(PathType type) {
    return type == PathType::CapturesDir ? data_dir / "captures" : data_dir;
}
} // namespace Common::FS

namespace Libraries::Np::NpMatching2 {
int BbscReplayRoomMembers(bool) {
    return 0; // the online module's room cache is out of reach here
}
} // namespace Libraries::Np::NpMatching2

// bb-probe calls this once the game is loaded, linked and patched, before it runs any of it.
extern "C" __attribute__((visibility("default"))) void bbsc_start(void) {
    CreateThread(nullptr, 0, Worker, nullptr, 0, nullptr);
}
