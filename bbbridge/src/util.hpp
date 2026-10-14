// Shared helpers: logging, endpoints, Winsock, tolerant JSON field access.
#pragma once

#ifdef _WIN32
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#else
// Linux: BSD sockets under Winsock's names, so the bridge's code is the same on both.
#include <arpa/inet.h>
#include <netdb.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <unistd.h>

#include <cerrno>
#include <chrono>
#include <ctime>
#include <thread>

using SOCKET = int;
constexpr SOCKET INVALID_SOCKET = -1;
constexpr int SD_BOTH = SHUT_RDWR;
// Closing a socket does not wake a thread blocked in accept() or recvfrom() on it on Linux
// (Windows does): shutdown() first, which does, also for listening and unconnected UDP sockets.
inline int closesocket(SOCKET s) {
    ::shutdown(s, SHUT_RDWR);
    return ::close(s);
}
inline int WSAGetLastError() { return errno; }
inline void Sleep(unsigned ms) { std::this_thread::sleep_for(std::chrono::milliseconds(ms)); }
inline void localtime_s(std::tm* out, const std::time_t* t) { localtime_r(t, out); }
#endif

#include <cstdint>
#include <filesystem>
#include <functional>
#include <string>

#include "nlohmann/json.hpp"

namespace bb {

using json = nlohmann::json;

constexpr const char* kVersion = "0.3.2";

// ---- logging: "HH:MM:SS [bbbridge] msg" to stdout, the log file and the app ----
void log(const std::string& msg);
std::string fmt(const char* format, ...);
void set_log_sink(std::function<void(const std::string&)> sink);   // the app's log panel
void set_log_file(const std::wstring& path);                        // keeps the previous as *.prev.log

double now();   // seconds, monotonic

// ---- endpoints ----
struct Endpoint {
    std::string ip;
    int port = 0;
    bool valid() const { return !ip.empty() && port > 0 && port <= 65535; }
    bool operator==(const Endpoint& o) const { return ip == o.ip && port == o.port; }
    bool operator!=(const Endpoint& o) const { return !(*this == o); }
    bool operator<(const Endpoint& o) const { return ip != o.ip ? ip < o.ip : port < o.port; }
    std::string str() const { return ip + ":" + std::to_string(port); }
};

bool net_init();
sockaddr_in to_sockaddr(const Endpoint& e);
Endpoint from_sockaddr(const sockaddr_in& a);
std::string detect_lan_addr();
std::string resolve_ipv4(const std::string& host);   // "" when it fails

// ---- JSON as Python's dict.get(): tolerant of missing keys, null, numbers as strings ----
// Templates, so they serve json and ordered_json (settings files keep their key order).
template <typename J>
bool jhas(const J& j, const char* key) {   // present and not null
    if (!j.is_object()) return false;
    auto it = j.find(key);
    return it != j.end() && !it->is_null();
}

template <typename J>
int64_t jint(const J& j, const char* key, int64_t def = 0) {
    if (!jhas(j, key)) return def;
    const auto& v = j.at(key);
    try {
        if (v.is_number_integer()) return v.template get<int64_t>();
        if (v.is_number_unsigned()) return static_cast<int64_t>(v.template get<uint64_t>());
        if (v.is_number_float()) return static_cast<int64_t>(v.template get<double>());
        if (v.is_boolean()) return v.template get<bool>() ? 1 : 0;
        if (v.is_string()) {
            const std::string s = v.template get<std::string>();
            return s.empty() ? def : std::stoll(s);
        }
    } catch (...) {
    }
    return def;
}

template <typename J>
std::string jstr(const J& j, const char* key, const std::string& def = "") {
    if (!jhas(j, key)) return def;
    const auto& v = j.at(key);
    if (v.is_string()) return v.template get<std::string>();
    if (v.is_number_integer()) return std::to_string(v.template get<int64_t>());
    if (v.is_number_unsigned()) return std::to_string(v.template get<uint64_t>());
    return v.dump();
}

std::string narrow(const std::wstring& w);
std::wstring widen(const std::string& s);
// A file name kept as UTF-16/32 text (std::wstring) as a path to open: on Linux file names are bytes,
// UTF-8 here.
std::filesystem::path fspath(const std::wstring& w);
// Replaces `to` with `from` in one step (MoveFileExW with MOVEFILE_REPLACE_EXISTING, rename()).
bool replace_file(const std::wstring& from, const std::wstring& to);

}  // namespace bb
