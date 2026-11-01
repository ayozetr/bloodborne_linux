# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""FromSoftware's archive formats as the game ships them: DCX (DFLT: zlib), BND4 with 0x24-byte
entries and FMG text tables. Used by the layers that change a game file for a launch
(scripts/fov.py, scripts/bbsc_kit_texts.py). From the Linux fork (its scripts/quit_menu.py)."""
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


def read_fmg(data):
    """{id: text or None} of an FMG (version 2: 64-bit string offsets)."""
    groups, = struct.unpack_from('<I', data, 0x0C)
    offsets, = struct.unpack_from('<Q', data, 0x18)
    strings = {}
    for g in range(groups):
        index, first, last, _ = struct.unpack_from('<iiii', data, 0x28 + 16 * g)
        for k, string_id in enumerate(range(first, last + 1)):
            at, = struct.unpack_from('<q', data, offsets + 8 * (index + k))
            if at <= 0:
                strings[string_id] = None
                continue
            end = at
            while data[end:end + 2] != b'\0\0':
                end += 2
            strings[string_id] = data[at:end].decode('utf-16-le')
    return strings


def write_fmg(template, strings):
    """An FMG like `template` (its header flags) holding `strings`."""
    ids = sorted(strings)
    groups = []
    for string_id in ids:
        if groups and groups[-1][2] == string_id - 1:
            groups[-1][2] = string_id
        else:
            groups.append([sum(g[2] - g[1] + 1 for g in groups), string_id, string_id])
    offsets_at = 0x28 + 16 * len(groups)
    text_at = offsets_at + 8 * len(ids)
    texts = bytearray()
    slots = []
    for string_id in ids:
        if strings[string_id] is None:
            slots.append(0)
            continue
        slots.append(text_at + len(texts))
        texts += strings[string_id].encode('utf-16-le') + b'\0\0'
    out = bytearray(template[:0x28])
    struct.pack_into('<I', out, 0x0C, len(groups))
    struct.pack_into('<I', out, 0x10, len(ids))
    struct.pack_into('<Q', out, 0x18, offsets_at)
    for index, first, last in groups:
        out += struct.pack('<iiii', index, first, last, 0)
    for slot in slots:
        out += struct.pack('<q', slot)
    out += texts
    out += b'\0' * (4 + (-(len(out) + 4) % 4))  # the game's files end in zeros like this
    struct.pack_into('<I', out, 0x04, len(out))
    return bytes(out)
