// SPDX-FileCopyrightText: Copyright 2026 bbport contributors
// SPDX-License-Identifier: GPL-2.0-or-later
/* runtime_movbe.c: the movbe forms the game uses, run on registers and a buffer. */
#include "runtime_movbe.h"
#include <stdio.h>
#include <string.h>

static int failures;
#define CHECK(cond)                                                                              \
    do {                                                                                         \
        if (!(cond)) {                                                                           \
            printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);                               \
            ++failures;                                                                          \
        }                                                                                        \
    } while (0)

enum { RAX, RCX, RDX, RBX, RSP, RBP, RSI, RDI, R8, R9, R10, R11, R12, R13, R14, R15 };

int main(void) {
    uint8_t memory[64];
    uint64_t regs[16];
    const uint64_t base = (uint64_t)(uintptr_t)memory;

    /* movbe eax, [rcx+4] (0f 38 f0 41 04): the game's DCX header read (issue #39). */
    {
        static const uint8_t code[] = {0x0f, 0x38, 0xf0, 0x41, 0x04};
        memset(regs, 0, sizeof(regs));
        memcpy(memory + 4, "\x00\x01\x10\x00", 4);
        regs[RCX] = base;
        regs[RAX] = 0xffffffffffffffffull;
        CHECK(runtime_movbe_run(code, regs, 0) == 5);
        CHECK(regs[RAX] == 0x00011000); /* upper half cleared */
    }
    /* movbe [rax+r12*4-0x10], r9d (46 0f 38 f1 4c a0 f0): a store, REX.R and REX.X, disp8. */
    {
        static const uint8_t code[] = {0x46, 0x0f, 0x38, 0xf1, 0x4c, 0xa0, 0xf0};
        memset(regs, 0, sizeof(regs));
        memset(memory, 0, sizeof(memory));
        regs[RAX] = base + 0x10;
        regs[R12] = 2;
        regs[R9] = 0xaabbccdd11223344ull;
        CHECK(runtime_movbe_run(code, regs, 0) == 7);
        CHECK(memcmp(memory + 8, "\x11\x22\x33\x44", 4) == 0); /* big-endian */
        CHECK(regs[R9] == 0xaabbccdd11223344ull); /* the source is left as it was */
    }
    /* movbe rdx, [r13+0x100] (49 0f 38 f0 95 00 01 00 00): 64-bit, REX.B, disp32. */
    {
        static const uint8_t code[] = {0x49, 0x0f, 0x38, 0xf0, 0x95, 0x00, 0x01, 0x00, 0x00};
        memset(regs, 0, sizeof(regs));
        memcpy(memory + 8, "\x01\x02\x03\x04\x05\x06\x07\x08", 8);
        regs[R13] = base + 8 - 0x100;
        CHECK(runtime_movbe_run(code, regs, 0) == 9);
        CHECK(regs[RDX] == 0x0102030405060708ull);
    }
    /* movbe [rsp+8], ecx (0f 38 f1 4c 24 08): rsp base through a SIB with no index. */
    {
        static const uint8_t code[] = {0x0f, 0x38, 0xf1, 0x4c, 0x24, 0x08};
        memset(regs, 0, sizeof(regs));
        memset(memory, 0, sizeof(memory));
        regs[RSP] = base;
        regs[RCX] = 0x12345678;
        CHECK(runtime_movbe_run(code, regs, 0) == 6);
        CHECK(memcmp(memory + 8, "\x12\x34\x56\x78", 4) == 0);
    }
    /* movbe esi, [rbp+0] (0f 38 f0 75 00): rbp needs a displacement byte. */
    {
        static const uint8_t code[] = {0x0f, 0x38, 0xf0, 0x75, 0x00};
        memset(regs, 0, sizeof(regs));
        memcpy(memory, "\xde\xad\xbe\xef", 4);
        regs[RBP] = base;
        CHECK(runtime_movbe_run(code, regs, 0) == 5);
        CHECK(regs[RSI] == 0xdeadbeef);
    }
    /* movbe ax, [rip+0x10] (66 0f 38 f0 05 10 00 00 00): 16 bits keep the rest, rip-relative. */
    {
        static const uint8_t code[] = {0x66, 0x0f, 0x38, 0xf0, 0x05, 0x10, 0x00, 0x00, 0x00};
        memset(regs, 0, sizeof(regs));
        memcpy(memory + 0x20, "\xab\xcd", 2);
        regs[RAX] = 0x1111111111111111ull;
        const uint64_t rip = base + 0x20 - 0x10 - sizeof(code);
        CHECK(runtime_movbe_run(code, regs, rip) == 9);
        CHECK(regs[RAX] == 0x111111111111abcdull);
    }
    /* Not a movbe: nothing is run. */
    {
        static const uint8_t crc32[] = {0xf2, 0x0f, 0x38, 0xf1, 0xc1};
        static const uint8_t ud2[] = {0x0f, 0x0b};
        static const uint8_t reg_form[] = {0x0f, 0x38, 0xf0, 0xc1};
        memset(regs, 0, sizeof(regs));
        CHECK(runtime_movbe_run(crc32, regs, 0) == 0);
        CHECK(runtime_movbe_run(ud2, regs, 0) == 0);
        CHECK(runtime_movbe_run(reg_form, regs, 0) == 0);
    }
    printf("movbe: %s\n", failures ? "FAILED" : "all passed");
    return failures != 0;
}
