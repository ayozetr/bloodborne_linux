#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Trophies: the game's list from its own dump, and the ones the player has earned.

The dump's sce_sys/trophy/trophy00.trp holds the icons (PNG) and the trophy lists (TROPCONF.ESFM,
TROP.ESFM and TROP_xx.ESFM per language). The lists are encrypted: AES-128-CBC with a key made by
encrypting the game's NP communication id (sce_sys/npbind.dat, NPWR05818_00) with the PS4's trophy
key, which the player supplies (shadPS4's TrophyKey). Without it, only the icons are known.

`trophies.py prepare --game DIR --user DIR [--language N]` (key in BB_TROPHY_KEY) writes
DIR/trophies/<NP communication id>/: icons/ (the PNGs, and TROPxxx.rgba for the overlay's notice:
width and height as little-endian u32, then 128x128 RGBA, made with Pillow), and trophies.tsv for
the runtime (id, grade P/G/S/B or -, hidden 1/0, name, detail); prints that directory. The runtime appends what the game unlocks
to earned.tsv there (id, Unix time) and shows it in the overlay (src/runtime_services.c).
"""
import argparse
import os
from pathlib import Path
import re
import struct
import sys
import xml.etree.ElementTree as ET

TRP_MAGIC = 0xDCA24D00
NOTICE_ICON = 128  # pixels, the overlay's icon (gpu/shim/bbport_overlay.cpp)
GRADES = {'P': 'platinum', 'G': 'gold', 'S': 'silver', 'B': 'bronze'}


# ---- AES-128 (FIPS-197), enough for CBC decryption and the key's one encrypted block --------

def _xtime(a):
    return ((a << 1) ^ 0x1B) & 0xFF if a & 0x80 else a << 1


def _mul(a, b):
    result = 0
    while b:
        if b & 1:
            result ^= a
        a, b = _xtime(a), b >> 1
    return result


def _sbox():
    box, inverse = [0] * 256, [0] * 256
    p = q = 1
    while True:
        p = p ^ ((p << 1) & 0xFF) ^ (0x1B if p & 0x80 else 0)  # p * 3
        q ^= q << 1
        q ^= q << 2
        q ^= q << 4
        q &= 0xFF
        if q & 0x80:
            q ^= 0x09                                           # q / 3
        x = q ^ ((q << 1 | q >> 7) & 0xFF) ^ ((q << 2 | q >> 6) & 0xFF) \
            ^ ((q << 3 | q >> 5) & 0xFF) ^ ((q << 4 | q >> 4) & 0xFF)
        box[p] = x ^ 0x63
        if p == 1:
            break
    box[0] = 0x63
    for i, v in enumerate(box):
        inverse[v] = i
    return box, inverse


SBOX, INV_SBOX = _sbox()


def _expand_key(key):
    words = [list(key[i:i + 4]) for i in range(0, 16, 4)]
    rcon = 1
    for i in range(4, 44):
        word = list(words[i - 1])
        if i % 4 == 0:
            word = [SBOX[b] for b in word[1:] + word[:1]]
            word[0] ^= rcon
            rcon = _xtime(rcon)
        words.append([a ^ b for a, b in zip(words[i - 4], word)])
    return [sum(words[r * 4:r * 4 + 4], []) for r in range(11)]


def _add(state, round_key):
    return [a ^ b for a, b in zip(state, round_key)]


def aes_encrypt_block(key, block):
    keys = _expand_key(key)
    s = _add(list(block), keys[0])
    for r in range(1, 11):
        s = [SBOX[b] for b in s]
        s = [s[(i + 4 * (i % 4)) % 16] for i in range(16)]           # ShiftRows
        if r != 10:
            m = []
            for c in range(4):
                a = s[c * 4:c * 4 + 4]
                m += [_mul(a[0], 2) ^ _mul(a[1], 3) ^ a[2] ^ a[3],
                      a[0] ^ _mul(a[1], 2) ^ _mul(a[2], 3) ^ a[3],
                      a[0] ^ a[1] ^ _mul(a[2], 2) ^ _mul(a[3], 3),
                      _mul(a[0], 3) ^ a[1] ^ a[2] ^ _mul(a[3], 2)]
            s = m
        s = _add(s, keys[r])
    return bytes(s)


def _decrypt_block(keys, block):
    s = _add(list(block), keys[10])
    for r in range(9, -1, -1):
        s = [s[(i - 4 * (i % 4)) % 16] for i in range(16)]           # InvShiftRows
        s = [INV_SBOX[b] for b in s]
        s = _add(s, keys[r])
        if r != 0:
            m = []
            for c in range(4):
                a = s[c * 4:c * 4 + 4]
                m += [_mul(a[0], 14) ^ _mul(a[1], 11) ^ _mul(a[2], 13) ^ _mul(a[3], 9),
                      _mul(a[0], 9) ^ _mul(a[1], 14) ^ _mul(a[2], 11) ^ _mul(a[3], 13),
                      _mul(a[0], 13) ^ _mul(a[1], 9) ^ _mul(a[2], 14) ^ _mul(a[3], 11),
                      _mul(a[0], 11) ^ _mul(a[1], 13) ^ _mul(a[2], 9) ^ _mul(a[3], 14)]
            s = m
    return bytes(s)


def aes_cbc_decrypt(key, iv, data):
    keys = _expand_key(key)
    out = bytearray()
    previous = iv
    for i in range(0, len(data) - len(data) % 16, 16):
        block = data[i:i + 16]
        out += bytes(a ^ b for a, b in zip(_decrypt_block(keys, block), previous))
        previous = block
    return bytes(out)


# ---- The dump's files --------------------------------------------------------------------

def read_trp(path):
    """{entry name: bytes} of a TRP file (sce_sys/trophy/trophy00.trp)."""
    data = Path(path).read_bytes()
    magic, _version, _size, count, entry_size = struct.unpack('>IIQII', data[:24])
    if magic != TRP_MAGIC or entry_size < 48:
        raise ValueError(f'{path}: not a trophy file')
    entries = {}
    for i in range(count):
        entry = data[0x60 + i * entry_size:0x60 + (i + 1) * entry_size]
        name = entry[:32].split(b'\0')[0].decode('ascii', 'replace')
        offset, length = struct.unpack('>QQ', entry[32:48])
        entries[name] = data[offset:offset + length]
    return entries


def np_comm_id(game):
    """The game's NP communication id (NPWR05818_00) from sce_sys/npbind.dat, or None."""
    try:
        data = (Path(game) / 'sce_sys' / 'npbind.dat').read_bytes()
    except OSError:
        return None
    found = re.search(rb'NPWR\d{5}_\d{2}', data)
    return found.group().decode() if found else None


def parse_key(text):
    """The trophy key from 32 hex digits (spaces and a 0x prefix allowed), or None."""
    text = re.sub(r'\s+', '', str(text or '')).removeprefix('0x')
    return bytes.fromhex(text) if re.fullmatch(r'[0-9A-Fa-f]{32}', text) else None


def decrypt_esfm(data, key, comm_id):
    """The XML of an ESFM entry: its first 16 bytes are the IV."""
    title_key = aes_encrypt_block(key, comm_id.encode().ljust(16, b'\0')[:16])
    xml = aes_cbc_decrypt(title_key, data[:16], data[16:])
    end = xml.rfind(b'>')
    return xml[:end + 1] if end >= 0 else b''


def parse_sfm(xml):
    """(title, {id: {grade, hidden, name, detail}}) of a decrypted trophy list."""
    text = xml.decode('utf-8', 'replace')
    start = text.find('<trophyconf')
    if start < 0:
        raise ValueError('not a trophy list (wrong trophy key?)')
    root = ET.fromstring(text[start:])
    trophies = {}
    for node in root.iter('trophy'):
        trophies[int(node.get('id'))] = {
            'grade': node.get('ttype', '-'),
            'hidden': node.get('hidden', 'no') == 'yes',
            'name': (node.findtext('name') or '').strip(),
            'detail': (node.findtext('detail') or '').strip(),
        }
    return (root.findtext('title-name') or '').strip(), trophies


def trophy_list(entries, key=None, comm_id=None, language=None):
    """{id: {grade, hidden, name, detail}} from a TRP's entries: names in the game language
    (TROP_xx, xx the PS4 language number) or the default list; without a key, the icons' ids."""
    icons = sorted(int(n[4:7]) for n in entries if re.fullmatch(r'TROP\d{3}\.PNG', n))
    trophies = {i: {'grade': '-', 'hidden': False, 'name': '', 'detail': ''} for i in icons}
    if key is None or comm_id is None:
        return trophies
    _title, config = parse_sfm(decrypt_esfm(entries['TROPCONF.ESFM'], key, comm_id))
    trophies.update(config)
    names = f'TROP_{language:02d}.ESFM' if language is not None else None
    for entry in (names, 'TROP.ESFM'):
        if entry in entries:
            _title, texts = parse_sfm(decrypt_esfm(entries[entry], key, comm_id))
            for i, text in texts.items():
                trophies.setdefault(i, dict(text)).update(name=text['name'], detail=text['detail'])
            break
    return trophies


# ---- The player's data -------------------------------------------------------------------

def trophy_dir(user, comm_id):
    return Path(user) / 'trophies' / comm_id


def read_earned(directory):
    """{id: Unix time} from earned.tsv (the first time each was unlocked)."""
    earned = {}
    try:
        lines = (Path(directory) / 'earned.tsv').read_text(encoding='utf-8').splitlines()
    except OSError:
        return earned
    for line in lines:
        fields = line.split('\t')
        if len(fields) >= 2 and fields[0].isdigit() and fields[1].isdigit():
            earned.setdefault(int(fields[0]), int(fields[1]))
    return earned


def read_list(directory):
    """{id: {grade, hidden, name, detail}} from trophies.tsv."""
    trophies = {}
    try:
        lines = (Path(directory) / 'trophies.tsv').read_text(encoding='utf-8').splitlines()
    except OSError:
        return trophies
    for line in lines:
        fields = line.split('\t')
        if len(fields) == 5 and fields[0].isdigit():
            trophies[int(fields[0])] = {'grade': fields[1], 'hidden': fields[2] == '1',
                                        'name': fields[3], 'detail': fields[4]}
    return trophies


def write_rgba(png, target, size=NOTICE_ICON):
    """The overlay's raw icon (TROPxxx.rgba) from a PNG; False without Pillow or for a damaged
    PNG."""
    try:
        from PIL import Image
    except ImportError:
        return False
    import io
    try:
        with Image.open(io.BytesIO(png)) as image:
            pixels = image.convert('RGBA').resize((size, size), Image.LANCZOS).tobytes()
    except (OSError, ValueError):  # a damaged icon: the overlay draws a cup instead
        return False
    temp = Path(str(target) + '.tmp')
    temp.write_bytes(struct.pack('<II', size, size) + pixels)
    os.replace(temp, target)
    return True


def _clean(text):
    return ' '.join(str(text).split())


def prepare(game, user, key=None, language=None):
    """Writes the trophy directory for a game (icons, trophies.tsv); returns it, or None when the
    dump has no trophies. A wrong key raises ValueError."""
    comm_id = np_comm_id(game)
    trp = Path(game) / 'sce_sys' / 'trophy' / 'trophy00.trp'
    if comm_id is None or not trp.is_file():
        return None
    entries = read_trp(trp)
    trophies = trophy_list(entries, key, comm_id, language)
    directory = trophy_dir(user, comm_id)
    icons = directory / 'icons'
    icons.mkdir(parents=True, exist_ok=True)
    for name, data in entries.items():
        if name.endswith('.PNG'):
            target = icons / name
            if not target.is_file() or target.stat().st_size != len(data):
                target.write_bytes(data)
            raw = icons / (name[:-4] + '.rgba')
            if re.fullmatch(r'TROP\d{3}\.PNG', name) and not raw.is_file():
                write_rgba(data, raw)
    lines = [f'{i}\t{t["grade"]}\t{int(t["hidden"])}\t{_clean(t["name"])}\t{_clean(t["detail"])}'
             for i, t in sorted(trophies.items())]
    temp = directory / 'trophies.tsv.tmp'
    temp.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    os.replace(temp, directory / 'trophies.tsv')
    return directory


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--game', required=True)
    p.add_argument('--user', required=True)
    p.add_argument('--language', type=int, help='PS4 language number (1 English, 3 Spanish, ...)')
    a = parser.parse_args()
    key = parse_key(os.environ.get('BB_TROPHY_KEY'))
    try:
        directory = prepare(a.game, a.user, key, a.language)
    except (OSError, ValueError, ET.ParseError) as error:
        print(f'Trophies: {error}', file=sys.stderr)
        directory = None
        if key is not None:  # the icons without the names
            try:
                directory = prepare(a.game, a.user, None, a.language)
                print('Trophies: names unavailable; check the trophy key', file=sys.stderr)
            except (OSError, ValueError):
                pass
    if directory is not None:
        print(directory)


if __name__ == '__main__':
    main()
