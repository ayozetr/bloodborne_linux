// SPDX-FileCopyrightText: Copyright 2026 bbport contributors
// SPDX-License-Identifier: GPL-2.0-or-later
/* MOVBE on processors without it (runtime_movbe.c). */
#ifndef BBPORT_RUNTIME_MOVBE_H
#define BBPORT_RUNTIME_MOVBE_H
#include <stdint.h>

/* Runs the movbe in `code` (at address `rip`) on `regs` (rax 0 ... r15 15) and its memory:
 * its length, or 0 when `code` is no movbe (nothing is changed then). */
int runtime_movbe_run(const uint8_t *code, uint64_t regs[16], uint64_t rip);
/* The SIGILL handler's part: the movbe at *rip run and *rip moved past it (1), or 0. */
int runtime_movbe_fault(uint64_t regs[16], uint64_t *rip);
/* BB_MOVBE_TRAP=file: the listed movbe of the image made ud2 (while it is still writable). */
void runtime_movbe_bind(unsigned char *image, uint64_t size);
/* Whether this processor has MOVBE (CPUID 1, ECX bit 22). */
int runtime_movbe_supported(void);
#endif
