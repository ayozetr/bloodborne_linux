#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""The gestures menu without the motion-control icons, for this launch: Dommo's "Stripped down
gesture menu" (Nexus Mods, Bloodborne mod 30), as the edits of assets/menu_prompts/gesturetop.json
on the player's own menu/gesturetop.gfx.

    gestures_menu.py <game> --out <dir> [--on 0|1]

Prints the layer folder for mods.py --ui-mods (run.sh), or nothing when it is off or the game's
file is not the one the edits were made for (the game then keeps its own menu). Made once per
game file; the button prompts themselves are drawn live by the port (bbport_button_prompts).
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATCH = ROOT / 'assets' / 'menu_prompts' / 'gesturetop.json'


def apply_gestures(original, patch_path=PATCH):
    """The game's gesturetop.gfx with the edits of gesturetop.json."""
    patch = json.loads(Path(patch_path).read_text())
    if hashlib.sha256(original).hexdigest() != patch['original_sha256']:
        raise ValueError('menu/gesturetop.gfx is not the one the gestures patch was made for')
    out, at = bytearray(), 0
    for offset, length, data in patch['edits']:
        out += original[at:offset] + bytes.fromhex(data)
        at = offset + length
    out += original[at:]
    if hashlib.sha256(out).hexdigest() != patch['result_sha256']:
        raise ValueError('gestures patch gave an unexpected result')
    return bytes(out)


def game_file(game, relative):
    """A file under the game's dvdroot_ps4/menu, whatever the case of its name."""
    folder = Path(game) / 'dvdroot_ps4'
    for part in ('menu', relative):
        match = [p for p in folder.iterdir() if p.name.casefold() == part] if folder.is_dir() else []
        if not match:
            raise FileNotFoundError(f'{relative} not found in the game')
        folder = match[0]
    return folder


def layer(game, out):
    """<out>/gestures-<key>/dvdroot_ps4/menu/gesturetop.gfx, made once per game file and patch."""
    base = game_file(game, 'gesturetop.gfx')
    stat = base.stat()
    digest = hashlib.sha256()
    for path in (Path(__file__), PATCH):
        digest.update(path.read_bytes())
    digest.update(f'{base}\0{stat.st_size}\0{stat.st_mtime_ns}'.encode())
    key = digest.hexdigest()[:16]
    folder = Path(out) / f'gestures-{key}'
    target = folder / 'dvdroot_ps4' / 'menu' / base.name
    if not target.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(target.name + '.part')
        partial.write_bytes(apply_gestures(base.read_bytes()))
        os.replace(partial, target)
    # Older results (another game folder, another patch) are dropped.
    for entry in Path(out).iterdir():
        if entry.name.startswith('gestures-') and entry != folder:
            shutil.rmtree(entry, ignore_errors=True)
    return folder


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game', type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--on', choices=('0', '1'), default='0')
    args = parser.parse_args(argv)
    if args.on != '1':
        print('')
        return
    try:
        args.out.mkdir(parents=True, exist_ok=True)
        print(layer(args.game, args.out))
    except (OSError, ValueError, KeyError) as error:
        print(f'Gestures menu: {error}; the game keeps its own', file=sys.stderr)
        print('')


if __name__ == '__main__':
    main()
