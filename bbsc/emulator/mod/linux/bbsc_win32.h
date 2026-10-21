// SPDX-License-Identifier: GPL-2.0-or-later
// bbport: the handful of Win32 and Winsock names the BBSC mod uses, on Linux. BSD sockets under
// their Winsock names (as bbbridge's port), POSIX threads, mprotect, a monotonic clock. Only what
// the mod's files call; anything that differs in meaning is handled in the file itself (#ifdef).
#pragma once

#include <arpa/inet.h>
#include <cerrno>
#include <cstdint>
#include <ctime>
#include <netdb.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <thread>
#include <unistd.h>

using DWORD = std::uint32_t;
using BOOL = int;
using HANDLE = void*;
using LPVOID = void*;
using SOCKET = int;
#ifndef TRUE
#define TRUE 1
#define FALSE 0
#endif
#define WINAPI
#define MAX_PATH 4096
#define INVALID_SOCKET (-1)
#define SOCKET_ERROR (-1)
#define INVALID_HANDLE_VALUE (reinterpret_cast<HANDLE>(-1))

// Memory protection: only the constants the mod passes.
constexpr DWORD PAGE_NOACCESS = 0x01, PAGE_READONLY = 0x02, PAGE_READWRITE = 0x04,
                PAGE_EXECUTE = 0x10, PAGE_EXECUTE_READ = 0x20, PAGE_EXECUTE_READWRITE = 0x40;

inline int BbscPosixProt(DWORD protect) {
    switch (protect) {
    case PAGE_NOACCESS:
        return PROT_NONE;
    case PAGE_READONLY:
        return PROT_READ;
    case PAGE_READWRITE:
        return PROT_READ | PROT_WRITE;
    case PAGE_EXECUTE:
    case PAGE_EXECUTE_READ:
        return PROT_READ | PROT_EXEC;
    default:
        return PROT_READ | PROT_WRITE | PROT_EXEC;
    }
}

// The pages under [address, address + size) get `protect`. The previous protection is not known
// here: it is reported as read/write/execute, which is what restoring it then sets (the game's
// image is made read/write/execute at start anyway, as shadPS4 maps it).
inline BOOL VirtualProtect(void* address, std::size_t size, DWORD protect, DWORD* old) {
    const auto page = static_cast<std::uintptr_t>(sysconf(_SC_PAGESIZE));
    const auto start = reinterpret_cast<std::uintptr_t>(address) & ~(page - 1);
    const auto end = reinterpret_cast<std::uintptr_t>(address) + size;
    if (old != nullptr) {
        *old = PAGE_EXECUTE_READWRITE;
    }
    return mprotect(reinterpret_cast<void*>(start), end - start, BbscPosixProt(protect)) == 0;
}

inline HANDLE GetCurrentProcess() {
    return nullptr;
}
// x86: instruction fetches see stores without a flush.
inline BOOL FlushInstructionCache(HANDLE, const void*, std::size_t) {
    return TRUE;
}
inline DWORD GetCurrentProcessId() {
    return static_cast<DWORD>(getpid());
}

inline std::uint64_t GetTickCount64() {
    timespec now{};
    clock_gettime(CLOCK_MONOTONIC, &now);
    return static_cast<std::uint64_t>(now.tv_sec) * 1000 + static_cast<std::uint64_t>(now.tv_nsec) / 1'000'000;
}
inline DWORD GetTickCount() {
    return static_cast<DWORD>(GetTickCount64());
}
inline void Sleep(DWORD ms) {
    timespec span{static_cast<time_t>(ms / 1000), static_cast<long>(ms % 1000) * 1'000'000};
    while (nanosleep(&span, &span) != 0 && errno == EINTR) {
    }
}

// A detached thread running a DWORD WINAPI f(void*); the handle only says it started.
inline HANDLE CreateThread(void*, std::size_t, DWORD (*start)(void*), void* argument, DWORD,
                           DWORD*) {
    try {
        std::thread([start, argument] { start(argument); }).detach();
    } catch (...) {
        return nullptr;
    }
    return reinterpret_cast<HANDLE>(1);
}
inline BOOL CloseHandle(HANDLE) {
    return TRUE;
}

// Winsock.
struct WSADATA {};
#define MAKEWORD(a, b) static_cast<unsigned short>((a) | ((b) << 8))
inline int WSAStartup(unsigned short, WSADATA*) {
    return 0;
}
// BBSC 0.0.2's relay: the error of the last socket call, and shutdown's "both ways".
inline int WSAGetLastError() {
    return errno;
}
#define SD_BOTH SHUT_RDWR
// shutdown first: a thread blocked in recv on the socket wakes up (close alone leaves it there).
inline int closesocket(SOCKET s) {
    shutdown(s, SHUT_RDWR);
    return close(s);
}
