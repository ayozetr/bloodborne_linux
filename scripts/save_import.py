#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Import Bloodborne saves from another build: shadPS4, another port's folder, a PS4 save exported
decrypted (Apollo Save Tool, Save Wizard), a copy on a USB stick.

    save_import.py --user USER_DIR [--game GAME_DIR] SOURCE

Every build keeps the game's save folder SPRJ0005 the same way (userdata0000..0010 and backup*
files, read and written by the game itself), so the files need no conversion: they are copied in
as user 1's saves, under the game's save id (param.sfo's INSTALL_DIR_SAVEDATA, else TITLE_ID; the
same rule as src/probe.c). The saves already there are first copied to
USER_DIR/savedata-backups/<date>/, and the new ones are staged next to them and swapped in, so a
failed copy leaves them as they were. A console's own USB copy (sdimg_SPRJ0005) is encrypted with
that console's keys and cannot be read: it has to be exported decrypted on the PS4.

Idea and rules from Awaken's BloodBorneButPc (SaveImport.cs).
"""
import argparse
from datetime import datetime
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare import sfo  # noqa: E402

SAVE_DIR = 'SPRJ0005'
# The game's system save, always written next to the character slots.
SYSTEM_FILE = 'userdata0010'
# Folders that hold no saves: game files (thousands of folders in a dump) and our own backups.
SKIPPED = {'dvdroot_ps4', 'sce_sys', 'savedata-backups', 'shader_cache', 'mods'}


class SaveImportError(Exception):
    pass


def save_files(folder):
    """The game's save files in folder (userdata*, backup*), sorted."""
    try:
        return sorted(p for p in Path(folder).iterdir()
                      if p.is_file() and p.name.startswith(('userdata', 'backup')))
    except OSError:
        return []


def is_save_folder(folder):
    """SPRJ0005 itself, an export named after it (CUSA00207_SPRJ0005), or any folder with the
    game's system save, holding userdata files."""
    folder = Path(folder)
    named = folder.name.upper().endswith(SAVE_DIR) or (folder / SYSTEM_FILE).is_file()
    return named and any(p.name.startswith('userdata') for p in save_files(folder))


def find(root, depth=7):
    """Save folders under root (root itself included), newest first: [(folder, newest mtime)]."""
    found = []

    def walk(folder, left):
        if is_save_folder(folder):
            found.append((folder, max(p.stat().st_mtime for p in save_files(folder))))
            return
        if left == 0:
            return
        try:
            children = sorted(p for p in folder.iterdir() if p.is_dir() and not p.is_symlink())
        except OSError:
            return
        for child in children:
            if child.name not in SKIPPED and not child.name.endswith('.sce_sys'):
                walk(child, left - 1)

    walk(Path(root), depth)
    return sorted(found, key=lambda item: item[1], reverse=True)


def encrypted_ps4_save(root, depth=7):
    """A console's USB copy (sdimg_*) under root: encrypted, no PC tool opens it."""
    def walk(folder, left):
        try:
            entries = list(folder.iterdir())
        except OSError:
            return False
        if any(p.is_file() and p.name.startswith('sdimg_') for p in entries):
            return True
        return left > 0 and any(walk(p, left - 1) for p in entries
                                if p.is_dir() and not p.is_symlink() and p.name not in SKIPPED)
    return walk(Path(root), depth)


def save_id(user_dir, game_dir=None):
    """The folder the runtime keeps this game's saves under (src/probe.c): param.sfo's
    INSTALL_DIR_SAVEDATA, else TITLE_ID; without a readable game, the one saves already use."""
    if game_dir:
        try:
            info = sfo((Path(game_dir) / 'sce_sys/param.sfo').read_bytes())
        except (OSError, ValueError, IndexError):
            info = {}
        for key in ('INSTALL_DIR_SAVEDATA', 'TITLE_ID'):
            value = str(info.get(key, '')).strip('\0').strip()
            if value:
                return value
    user = Path(user_dir) / 'savedata/1'
    if user.is_dir():
        for title in sorted(user.iterdir()):
            if (title / SAVE_DIR).is_dir():
                return title.name
    raise SaveImportError('the game folder is not set and there are no saves yet to tell the game id')


def game_running():
    """bb-probe (the game) is running: its saves must not change under it."""
    for comm in Path('/proc').glob('[0-9]*/comm'):
        try:
            if comm.read_text().strip() == 'bb-probe':
                return True
        except OSError:
            continue
    return False


def import_saves(source, user_dir, game_dir=None, now=None):
    """Copies source's save files in as user 1's saves; returns (target, backup folder or None)."""
    source = Path(source).expanduser()
    if not is_save_folder(source):
        raise SaveImportError(f'{source} has no Bloodborne save files (userdata)')
    user_dir = Path(user_dir).expanduser()
    target = user_dir / 'savedata/1' / save_id(user_dir, game_dir) / SAVE_DIR
    if source.resolve() == target.resolve():
        raise SaveImportError('those are already the saves in use')
    backup = None
    if save_files(target):
        stamp = (now or datetime.now()).strftime('%Y-%m-%d_%H%M%S')
        backup = user_dir / 'savedata-backups' / stamp
        shutil.copytree(target.parent, backup / target.parent.name, symlinks=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = target.with_name(SAVE_DIR + '.importing')
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir()
    try:
        # Only the save files: a shadPS4 folder's sce_sys inside is its own bookkeeping, and
        # ours (SPRJ0005.sce_sys, the save list's title and date) is kept.
        for path in save_files(source):
            shutil.copy2(path, staging / path.name)
        old = target.with_name(SAVE_DIR + '.old')
        shutil.rmtree(old, ignore_errors=True)
        if target.exists():
            target.rename(old)
        staging.rename(target)
        shutil.rmtree(old, ignore_errors=True)
    except OSError:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    # The runtime writes the save list's details (param.bin) there when the game saves.
    target.with_name(SAVE_DIR + '.sce_sys').mkdir(exist_ok=True)
    return target, backup


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--user', required=True, help='the user folder (saves, shader cache)')
    parser.add_argument('--game', help='the game folder (its param.sfo gives the save id)')
    parser.add_argument('source', help='a save folder, or a folder to search for one')
    a = parser.parse_args()
    if game_running():
        print('Import failed: close the game first', file=sys.stderr)
        return 1
    found = find(a.source)
    if not found:
        reason = ('it is a PS4 USB copy (sdimg_*), encrypted with the console\'s keys: export it '
                  'decrypted on the PS4 (Apollo Save Tool) or with Save Wizard'
                  if encrypted_ps4_save(a.source) else 'no Bloodborne saves (SPRJ0005, userdata*)')
        print(f'Import failed: {reason}', file=sys.stderr)
        return 1
    try:
        target, backup = import_saves(found[0][0], a.user, a.game)
    except (SaveImportError, OSError) as error:
        print(f'Import failed: {error}', file=sys.stderr)
        return 1
    print(f'Imported {found[0][0]} into {target}')
    if backup:
        print(f'Previous saves backed up in {backup}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
