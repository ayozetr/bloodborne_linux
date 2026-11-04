#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""The image offsets of the movbe in the game's code, one per line, for BB_MOVBE_TRAP
(src/runtime_movbe.c): a game run with them made ud2 tests the port's movbe on any processor.

    python3 tools/movbe_sites.py out/eboot.elf > out/movbe-sites.txt
    BB_MOVBE_TRAP=out/movbe-sites.txt bash run.sh

Needs objdump (binutils)."""
import struct
import subprocess
import sys
import tempfile


def code_segments(elf):
    phoff, = struct.unpack_from('<Q', elf, 0x20)
    phentsize, phnum = struct.unpack_from('<HH', elf, 0x36)
    for i in range(phnum):
        kind, flags, offset, vaddr, _, filesz = struct.unpack_from('<IIQQQQ', elf, phoff + i * phentsize)
        if kind == 1 and flags & 1:
            yield vaddr, elf[offset:offset + filesz]


def main():
    elf = open(sys.argv[1], 'rb').read()
    for vaddr, code in code_segments(elf):
        with tempfile.NamedTemporaryFile() as f:
            f.write(code)
            f.flush()
            listing = subprocess.run(
                ['objdump', '-D', '--insn-width=16', '-b', 'binary', '-m', 'i386:x86-64',
                 f'--adjust-vma={vaddr:#x}', f.name], check=True, capture_output=True, text=True).stdout
        for line in listing.splitlines():
            fields = line.split('\t')
            if len(fields) >= 3 and fields[2].startswith('movbe'):
                print(fields[0].strip().rstrip(':'))


if __name__ == '__main__':
    main()
