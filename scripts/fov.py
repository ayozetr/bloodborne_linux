#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Field of view (bbport.ini fov, degrees; unset or 43 = the game's): the game's camera table with
every camera's field of view scaled, as a layer for mods.py --ui-mods (run.sh). Prints the layer's
folder, or an empty line when there is none.

The cameras come from LockCamParam in param/gameparam/gameparam.parambnd.dcx, the same
LOCK_CAM_PARAM_ST as Dark Souls III's: each row is camDistTarget, rotRangeMinX,
lockRotXShiftRatio, chrOrgOffset_Y, chrLockRangeMaxRadius, then camFovY, the vertical field of
view in degrees, at +0x14. The normal camera has 43; a few areas set their own (48). Every row is
scaled by fov / 43, so those keep their difference. The game reads the table at start: a change
needs a restart. A mod that replaces gameparam.parambnd.dcx is laid above this layer and wins.
From Supermedo/bloodborne_pc b75e811 (Ethan Murphy).
"""
import argparse
import hashlib
import shutil
import struct
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quit_menu import bnd4_files, pack_dcx, rebuild_bnd4, unpack_dcx  # noqa: E402

GAME_FOV = 43.0     # camFovY of the game's normal camera
FOV_RANGE = (30, 90)
ARCHIVE = Path('dvdroot_ps4') / 'param' / 'gameparam' / 'gameparam.parambnd.dcx'
TABLE = 'LockCamParam.param'
CAM_FOV_Y = 0x14


def bnd4_name(data, entry):
    """The file name of a BND4 entry, without its folders."""
    offset, = struct.unpack_from('<I', data, entry + 0x20)
    if data[0x30]:  # UTF-16 names
        end = offset
        while data[end:end + 2] != b'\0\0':
            end += 2
        name = data[offset:end].decode('utf-16-le')
    else:
        name = data[offset:data.index(b'\0', offset)].decode('shift-jis')
    return name.replace('\\', '/').rsplit('/', 1)[-1]


def param_rows(param):
    """Data offsets of a PARAM's rows (64-bit row table at 0x40, as in this game's params)."""
    if param[0x0C:0x0C + 17] != b'LOCK_CAM_PARAM_ST':
        raise ValueError('LockCamParam is not a LOCK_CAM_PARAM_ST table')
    count, = struct.unpack_from('<H', param, 0x0A)
    rows = [struct.unpack_from('<Q', param, 0x40 + i * 24 + 8)[0] for i in range(count)]
    if not rows or any(r + CAM_FOV_Y + 4 > len(param) for r in rows):
        raise ValueError('LockCamParam rows out of range')
    return rows


def scaled_table(param, fov):
    """The table with every camFovY scaled by fov / GAME_FOV, and how many rows changed."""
    out = bytearray(param)
    changed = 0
    for row in param_rows(param):
        value, = struct.unpack_from('<f', param, row + CAM_FOV_Y)
        if not 10.0 <= value <= 120.0:
            raise ValueError(f'LockCamParam camFovY {value} is not a field of view')
        struct.pack_into('<f', out, row + CAM_FOV_Y, min(150.0, value * fov / GAME_FOV))
        changed += 1
    return bytes(out), changed


def scaled_archive(archive, fov):
    bnd = unpack_dcx(archive)
    for entry, offset, length, file_id in bnd4_files(bnd):
        if bnd4_name(bnd, entry) == TABLE:
            table, changed = scaled_table(bnd[offset:offset + length], fov)
            return pack_dcx(archive, rebuild_bnd4(bnd, {file_id: table})), changed
    raise ValueError(f'{TABLE} not found')


def setting(config):
    """bbport.ini fov in degrees, clamped to FOV_RANGE; None when unset, not a number or 43."""
    try:
        lines = Path(config).read_text(encoding='utf-8').splitlines()
    except (OSError, TypeError):
        return None
    for line in lines:
        key, sep, value = line.partition('=')
        if sep and key.strip() == 'fov':
            try:
                fov = float(value.strip())
            except ValueError:
                return None
            fov = min(max(fov, FOV_RANGE[0]), FOV_RANGE[1])
            return None if fov == GAME_FOV else fov
    return None


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('game', type=Path, help='game folder (with dvdroot_ps4)')
    p.add_argument('--out', type=Path, required=True, help='mod layer folder to write (replaced)')
    p.add_argument('--config', help='bbport.ini: fov')
    a = p.parse_args()
    stamp = a.out.with_name(a.out.name + '.source')  # beside the layer, not a game file in it
    fov = setting(a.config)
    if fov is None:
        shutil.rmtree(a.out, ignore_errors=True)
        stamp.unlink(missing_ok=True)
        print('')
        return
    data = (a.game / ARCHIVE).read_bytes()
    target = a.out / ARCHIVE
    # Repacking takes a few seconds: the layer is kept while the setting and the game file match.
    key = f'{fov:g} {hashlib.sha256(data).hexdigest()}'
    try:
        reuse = target.is_file() and stamp.read_text() == key
    except OSError:
        reuse = False
    if reuse:
        print(f'Field of view: {fov:g} degrees (kept)', file=sys.stderr)
    else:
        shutil.rmtree(a.out, ignore_errors=True)
        try:
            archive, changed = scaled_archive(data, fov)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive)
            stamp.write_text(key)
        except BaseException:
            shutil.rmtree(a.out, ignore_errors=True)  # no half-written layer
            stamp.unlink(missing_ok=True)
            raise
        print(f'Field of view: {fov:g} degrees ({changed} cameras)', file=sys.stderr)
    print(a.out)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, struct.error, zlib.error) as error:
        # Optional: the game starts with its own field of view.
        print(f'Field of view: {error}; the game keeps its own', file=sys.stderr)
        print('')
