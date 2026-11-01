# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""FromSoftware's archive formats as the game ships them: DCX (DFLT: zlib) and BND4 with 0x24-byte
entries. Used by the layers that change a game file for a launch (scripts/fov.py). From the Linux
fork (its scripts/quit_menu.py)."""
import struct
import zlib


def unpack_dcx(data):
    if data[:4] != b'DCX\0' or data[0x28:0x2C] != b'DFLT':
        raise ValueError('not a DFLT DCX archive')
    return zlib.decompress(data[0x4C:])


def pack_dcx(template, body):
    packed = zlib.compress(body, 9)
    header = bytearray(template[:0x4C])
    struct.pack_into('>II', header, 0x1C, len(body), len(packed))
    return bytes(header) + packed


def bnd4_files(data):
    """[(entry offset, data offset, size, file id)] of a BND4 with 0x24-byte entries."""
    if data[:4] != b'BND4':
        raise ValueError('not a BND4 archive')
    count, = struct.unpack_from('<I', data, 0x0C)
    size, = struct.unpack_from('<Q', data, 0x20)
    if size != 0x24:
        raise ValueError(f'unsupported BND4 entry size {size:#x}')
    out = []
    for i in range(count):
        entry = 0x40 + i * size
        length, = struct.unpack_from('<Q', data, entry + 0x08)
        offset, = struct.unpack_from('<I', data, entry + 0x18)
        file_id, = struct.unpack_from('<I', data, entry + 0x1C)
        out.append((entry, offset, length, file_id))
    return out


def rebuild_bnd4(data, replace):
    """The BND4 with files {id: bytes} replaced; data re-laid out with the original alignment."""
    files = bnd4_files(data)
    start = min(offset for _, offset, _, _ in files)
    out = bytearray(data[:start])
    for entry, offset, length, file_id in sorted(files, key=lambda f: f[1]):
        body = replace.get(file_id, data[offset:offset + length])
        out += b'\0' * (-len(out) % 16)
        struct.pack_into('<QQI', out, entry + 0x08, len(body), len(body), len(out))
        out += body
    return bytes(out)
