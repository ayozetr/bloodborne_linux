#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Crash guards: the game's own code, where it reads through a pointer it never checks (game version 01.09).

- Online event without its data (0x1EB3D10, case 0). The game describes an event (r13: the event, its
  type the switch's value; r12: its data) and returns whether it could, the low byte of r12; an event
  type it does not know goes to 0x1EB3DD0: r12 = 0, "could not". Case 0 copies a string from r12 + 0x80
  without checking r12: a player on The Hunter's Dream crashed there ("read access to 00000000000000a0
  at guest offset 0x1eb56b7") right after the server's ss.info request timed out. Case 0 with no data now
  goes the same way as an unknown event.

Our own code goes in the free tail of the executable's last code page, past the game's code (which ends
at 0x50D96DC). From Supermedo's port (scripts/crash_guards.py, by ethan), by way of the Linux fork.
BB_CRASH_GUARDS=0 leaves them out (scripts/patches.py).
"""
import struct

CODE_END = 0x50D96DC               # the game's code ends here; the page's tail is free
CAVE = 0x50D9700
CAVE_END = (CODE_END + 0xFFF) & ~0xFFF
EVENT_CASE = 0x1EB3DE8             # sub r12, -0x80; lea rdi, [rbp-0xa0]
EVENT_CASE_BYTES = bytes.fromhex('4983ec80488dbd60ffffff')
EVENT_UNKNOWN = 0x1EB3DD0          # xor r12d, r12d; jmp (the function's end): "could not"


class Code:
    """Machine code placed at an image offset, with rip-relative jumps."""

    def __init__(self, offset):
        self.offset, self.data = offset, bytearray()

    @property
    def here(self):
        return self.offset + len(self.data)

    def raw(self, hexbytes):
        self.data += bytes.fromhex(hexbytes)

    def jmp(self, target):
        self.data += b'\xe9' + struct.pack('<i', target - (self.here + 5))


def code_writes():
    cave = Code(CAVE)
    cave.raw('4d85e4')                                   # test r12, r12
    cave.data += b'\x0f\x84' + struct.pack('<i', EVENT_UNKNOWN - (cave.here + 6))   # jz: as unknown
    cave.data += EVENT_CASE_BYTES                        # the case's own first instructions
    cave.jmp(EVENT_CASE + len(EVENT_CASE_BYTES))
    if cave.here > CAVE_END:
        raise ValueError('crash guards do not fit')
    site = Code(EVENT_CASE)
    site.jmp(CAVE)
    site.data += b'\x90' * (len(EVENT_CASE_BYTES) - len(site.data))
    return [(cave.offset, bytes(cave.data)), (site.offset, bytes(site.data))]


def applies(original):
    """Whether the executable is the one these sites were found in: original(offset, size) gives its
    memory image's bytes (zeros past its file data, where the cave is)."""
    return (original(EVENT_CASE, len(EVENT_CASE_BYTES)) == EVENT_CASE_BYTES
            and not any(original(CAVE, CAVE_END - CAVE)))
