// SPDX-FileCopyrightText: Copyright 2026 CLS_AMG
// SPDX-License-Identifier: GPL-2.0-or-later

#include "core/bbsc_memscan.h"

#ifdef _WIN32
#include <windows.h>
#else
// bbport: the Linux search.
#include <cinttypes>
#include <cstdio>
#include <fcntl.h>
#include <sys/uio.h>
#include <unistd.h>
#endif

#include <algorithm>
#include <cstring>

namespace Core::Bbsc {

namespace {

#ifdef _WIN32
// One region. The emulator changes page protection all the time (GPU tracking), so a page that was
// readable a moment ago may fault now: the search runs under SEH and a fault just ends the region.
void SearchRegion(const std::uint8_t* start, std::size_t size, const std::uint8_t* needle,
                  std::size_t length, std::vector<std::uint64_t>& hits, std::size_t max_hits) {
    __try {
        const std::uint8_t* end = start + size;
        const std::uint8_t* at = start;
        while (hits.size() < max_hits && end - at >= static_cast<std::ptrdiff_t>(length)) {
            at = static_cast<const std::uint8_t*>(
                std::memchr(at, needle[0], static_cast<std::size_t>(end - at) - length + 1));
            if (at == nullptr) {
                break;
            }
            if (std::memcmp(at, needle, length) == 0) {
                hits.push_back(reinterpret_cast<std::uint64_t>(at));
            }
            ++at;
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
    }
}
#else
// bbport: one region, copied in slices through process_vm_readv on this process: a page the GPU
// side just protected, or a region unmapped meanwhile, only fails that read (as the SEH guard on
// Windows) instead of faulting. Consecutive slices overlap by the needle's length.
// process_vm_readv cannot read a driver's mapping (VM_IO / VM_PFNMAP): on AMD the game's memory is a
// GPU dma-buf (gpu/shim/bbport_guest_memory.cpp), and the item tables were never found there
// (issue #9). /proc/self/mem reads those through the driver's own access, so a failed slice is
// read again that way.
void SearchRegion(std::uint64_t start, std::uint64_t end, const std::uint8_t* needle,
                  std::size_t length, std::vector<std::uint8_t>& buffer, int mem,
                  std::vector<std::uint64_t>& hits, std::size_t max_hits) {
    const pid_t self = getpid();
    std::uint64_t at = start;
    while (at < end && hits.size() < max_hits) {
        const auto want =
            static_cast<std::size_t>(std::min<std::uint64_t>(buffer.size(), end - at));
        iovec local{buffer.data(), want};
        iovec remote{reinterpret_cast<void*>(at), want};
        ssize_t got = process_vm_readv(self, &local, 1, &remote, 1, 0);
        if (got <= 0 && mem >= 0) {
            got = pread(mem, buffer.data(), want, static_cast<off_t>(at));
        }
        if (got <= 0) {
            at = (at & ~std::uint64_t{0xFFF}) + 0x1000; // an unreadable page: the next one
            continue;
        }
        const auto size = static_cast<std::size_t>(got);
        const std::uint8_t* data = buffer.data();
        const std::uint8_t* scan = data;
        while (size >= length && hits.size() < max_hits) {
            if (scan > data + size - length) {
                break;
            }
            const auto left = static_cast<std::size_t>(data + size - length + 1 - scan);
            scan = static_cast<const std::uint8_t*>(std::memchr(scan, needle[0], left));
            if (scan == nullptr) {
                break;
            }
            if (std::memcmp(scan, needle, length) == 0) {
                hits.push_back(at + static_cast<std::uint64_t>(scan - data));
            }
            ++scan;
        }
        at += at + size >= end || size < length ? size : size - length + 1;
    }
}
#endif

} // namespace

std::vector<std::uint64_t> FindInMemory(std::span<const std::uint8_t> needle, std::uint64_t lo,
                                        std::uint64_t hi, std::size_t max_hits) {
    std::vector<std::uint64_t> hits;
#ifdef _WIN32
    if (needle.empty()) {
        return hits;
    }
    constexpr DWORD Readable = PAGE_READONLY | PAGE_READWRITE | PAGE_WRITECOPY | PAGE_EXECUTE_READ |
                               PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY;
    std::uint64_t at = lo;
    while (at < hi && hits.size() < max_hits) {
        MEMORY_BASIC_INFORMATION info{};
        if (VirtualQuery(reinterpret_cast<void*>(at), &info, sizeof(info)) == 0) {
            break;
        }
        const auto start = reinterpret_cast<std::uint64_t>(info.BaseAddress);
        const std::uint64_t end = start + info.RegionSize;
        if (info.State == MEM_COMMIT && (info.Protect & Readable) != 0 &&
            (info.Protect & (PAGE_GUARD | PAGE_NOACCESS)) == 0) {
            SearchRegion(reinterpret_cast<const std::uint8_t*>(start), info.RegionSize,
                         needle.data(), needle.size(), hits, max_hits);
        }
        if (end <= at) {
            break;
        }
        at = end;
    }
#else
    if (needle.empty()) {
        return hits;
    }
    // The readable mappings in [lo, hi), from /proc/self/maps.
    FILE* maps = std::fopen("/proc/self/maps", "r");
    if (maps == nullptr) {
        return hits;
    }
    std::vector<std::uint8_t> buffer(std::size_t{1} << 20);
    const int mem = open("/proc/self/mem", O_RDONLY | O_CLOEXEC);
    char line[512];
    while (hits.size() < max_hits && std::fgets(line, sizeof(line), maps) != nullptr) {
        std::uint64_t start = 0;
        std::uint64_t end = 0;
        char prot[5] = {};
        if (std::sscanf(line, "%" SCNx64 "-%" SCNx64 " %4s", &start, &end, prot) != 3 ||
            prot[0] != 'r' || end <= lo || start >= hi) {
            continue;
        }
        SearchRegion(std::max(start, lo), std::min(end, hi), needle.data(), needle.size(), buffer,
                     mem, hits, max_hits);
    }
    if (mem >= 0) {
        close(mem);
    }
    std::fclose(maps);
#endif
    return hits;
}

} // namespace Core::Bbsc
