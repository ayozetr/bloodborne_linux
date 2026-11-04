// SPDX-FileCopyrightText: Copyright 2026 bbport contributors
// SPDX-License-Identifier: GPL-2.0-or-later
/* MOVBE on processors without it. The game's code was built for the PS4's CPU (AMD Jaguar) and
 * has 987 movbe (a load or store with its bytes swapped: the big-endian headers of the game's
 * files, network data). AMD's FX processors (Bulldozer to Piledriver) have every other instruction
 * the game uses, but not this one: the first movbe stopped the game with SIGILL (issue #39). The
 * SIGILL handler (probe.c) does it here instead and resumes after it; on a processor with MOVBE
 * this code never runs.
 *
 * BB_MOVBE_TRAP=file (testing on any processor): the image offsets of movbe in the file
 * (one hex number per line, tools/movbe_sites.py) become ud2, which this code runs as the movbe
 * that was there, as a processor without MOVBE would. */
#define _GNU_SOURCE
#include "runtime_movbe.h"
#include "../gpu/shim/bb_env.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

/* x86 register numbers (rax 0 ... r15 15). */
enum { RSP = 4, RBP = 5 };

int runtime_movbe_run(const uint8_t *code, uint64_t regs[16], uint64_t rip) {
    const uint8_t *p = code;
    int rex = 0, operand16 = 0;
    for (;; ++p) {
        if (p - code >= 4) return 0;
        if (*p == 0x66) operand16 = 1;
        else break;
    }
    if ((*p & 0xf0) == 0x40) rex = *p++;
    if (p[0] != 0x0f || p[1] != 0x38 || (p[2] != 0xf0 && p[2] != 0xf1)) return 0;
    const int store = p[2] == 0xf1;
    p += 3;
    const uint8_t modrm = *p++;
    const int mod = modrm >> 6, rm = modrm & 7;
    const int reg = ((modrm >> 3) & 7) | (rex & 4 ? 8 : 0);
    if (mod == 3) return 0; /* the register form does not exist */
    uint64_t address = 0;
    int rip_relative = 0;
    if (rm == 4) {
        const uint8_t sib = *p++;
        const int scale = sib >> 6, index = ((sib >> 3) & 7) | (rex & 2 ? 8 : 0);
        const int base = (sib & 7) | (rex & 1 ? 8 : 0);
        if (index != RSP) address += regs[index] << scale;
        if ((base & 7) == RBP && mod == 0) {
            int32_t disp;
            memcpy(&disp, p, 4);
            p += 4;
            address += (uint64_t)(int64_t)disp;
        } else {
            address += regs[base];
        }
    } else if (rm == 5 && mod == 0) {
        rip_relative = 1;
    } else {
        address = regs[rm | (rex & 1 ? 8 : 0)];
    }
    if (mod == 1) {
        address += (uint64_t)(int64_t)(int8_t)*p++;
    } else if (mod == 2 || rip_relative) {
        int32_t disp;
        memcpy(&disp, p, 4);
        p += 4;
        address += (uint64_t)(int64_t)disp;
    }
    const int length = (int)(p - code);
    if (rip_relative) address += rip + (uint64_t)length;
    uint8_t *memory = (uint8_t *)(uintptr_t)address;
    if (rex & 8) {
        uint64_t value;
        if (store) {
            value = __builtin_bswap64(regs[reg]);
            memcpy(memory, &value, 8);
        } else {
            memcpy(&value, memory, 8);
            regs[reg] = __builtin_bswap64(value);
        }
    } else if (operand16) {
        uint16_t value;
        if (store) {
            value = __builtin_bswap16((uint16_t)regs[reg]);
            memcpy(memory, &value, 2);
        } else {
            memcpy(&value, memory, 2);
            regs[reg] = (regs[reg] & ~(uint64_t)0xffff) | __builtin_bswap16(value);
        }
    } else {
        uint32_t value;
        if (store) {
            value = __builtin_bswap32((uint32_t)regs[reg]);
            memcpy(memory, &value, 4);
        } else {
            memcpy(&value, memory, 4);
            regs[reg] = __builtin_bswap32(value); /* a 32-bit result clears the upper half */
        }
    }
    return length;
}

/* BB_MOVBE_TRAP: the replaced instructions, by image offset. */
typedef struct {
    uint64_t offset;
    uint8_t code[16];
} Trapped;
static Trapped *trapped;
static size_t trapped_count;
static uintptr_t trapped_image;

static int by_offset(const void *a, const void *b) {
    const uint64_t x = ((const Trapped *)a)->offset, y = ((const Trapped *)b)->offset;
    return x < y ? -1 : x > y;
}

void runtime_movbe_bind(unsigned char *image, uint64_t size) {
    const char *path = bb_env("BB_MOVBE_TRAP");
    if (!path || !path[0]) return;
    FILE *f = fopen(path, "r");
    if (!f) {
        printf("MOVBE: BB_MOVBE_TRAP=%s cannot be read\n", path);
        return;
    }
    size_t capacity = 0, skipped = 0;
    char line[64];
    const uint64_t page = (uint64_t)sysconf(_SC_PAGESIZE);
    while (fgets(line, sizeof(line), f)) {
        char *end;
        const uint64_t offset = strtoull(line, &end, 16);
        if (end == line) continue;
        if (offset + 16 > size) {
            ++skipped;
            continue;
        }
        Trapped t = {.offset = offset};
        memcpy(t.code, image + offset, sizeof(t.code));
        const uint8_t *op = t.code + ((t.code[0] & 0xf0) == 0x40); /* past a REX prefix */
        if (op[0] != 0x0f || op[1] != 0x38 || (op[2] != 0xf0 && op[2] != 0xf1)) {
            ++skipped;
            continue;
        }
        if (trapped_count == capacity) {
            capacity = capacity ? capacity * 2 : 1024;
            trapped = realloc(trapped, capacity * sizeof(*trapped));
            if (!trapped) {
                fclose(f);
                trapped_count = 0;
                return;
            }
        }
        trapped[trapped_count++] = t;
        const uint64_t first = offset & ~(page - 1);
        mprotect(image + first, (size_t)((offset + 2 + page - 1) / page * page - first), PROT_READ | PROT_WRITE | PROT_EXEC);
        image[offset] = 0x0f;
        image[offset + 1] = 0x0b; /* ud2 */
    }
    fclose(f);
    qsort(trapped, trapped_count, sizeof(*trapped), by_offset);
    trapped_image = (uintptr_t)image;
    printf("MOVBE: BB_MOVBE_TRAP: %zu movbe made ud2 and run by the port (%zu lines skipped)\n", trapped_count,
           skipped);
}

int runtime_movbe_supported(void) {
    unsigned a, b, c, d;
    __asm__("cpuid" : "=a"(a), "=b"(b), "=c"(c), "=d"(d) : "a"(1), "c"(0));
    return (c >> 22) & 1;
}

/* How many the port ran (the log says it every 10 s). */
static volatile uint64_t emulated;

int runtime_movbe_fault(uint64_t regs[16], uint64_t *rip) {
    const uint8_t *code = (const uint8_t *)(uintptr_t)*rip;
    if (trapped_count && code[0] == 0x0f && code[1] == 0x0b) {
        const Trapped key = {.offset = *rip - trapped_image};
        const Trapped *t = bsearch(&key, trapped, trapped_count, sizeof(*trapped), by_offset);
        if (t) code = t->code;
    }
    const int length = runtime_movbe_run(code, regs, *rip);
    if (!length) return 0;
    *rip += (uint64_t)length;
    const uint64_t total = __atomic_add_fetch(&emulated, 1, __ATOMIC_RELAXED);
    /* In the log: the first one, then how many every 10 s (a signal each: a cost if many). */
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    static int64_t next_report;
    static uint64_t reported;
    int64_t due = __atomic_load_n(&next_report, __ATOMIC_RELAXED);
    if (total == 1 || (now.tv_sec >= due &&
                       __atomic_compare_exchange_n(&next_report, &due, (int64_t)now.tv_sec + 10, 0,
                                                   __ATOMIC_RELAXED, __ATOMIC_RELAXED))) {
        if (total == 1) __atomic_store_n(&next_report, (int64_t)now.tv_sec + 10, __ATOMIC_RELAXED);
        char line[96] = "MOVBE: run by the port: ";
        size_t at = strlen(line);
        char digits[24];
        size_t n = 0;
        uint64_t value = total - __atomic_exchange_n(&reported, total, __ATOMIC_RELAXED);
        do digits[n++] = (char)('0' + value % 10); while ((value /= 10) && n < sizeof(digits));
        while (n) line[at++] = digits[--n];
        static const char tail[] = " (this processor has no MOVBE)\n";
        memcpy(line + at, tail, sizeof(tail) - 1);
        ssize_t written = write(1, line, at + sizeof(tail) - 1);
        (void)written;
    }
    return 1;
}
