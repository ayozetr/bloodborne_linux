#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Import Bloodborne saves from another build: shadPS4, another port's folder, a PS4 save exported
decrypted (Apollo Save Tool, Save Wizard), a copy on a USB stick.

    save_import.py --user USER_DIR [--game GAME_DIR] SOURCE
    save_import.py --user USER_DIR [--game GAME_DIR] --export ARCHIVE.zip

Every build keeps the game's save folder SPRJ0005 the same way (userdata0000..0010 and backup*
files, read and written by the game itself), so the files need no conversion: they are copied in
as user 1's saves, under the game's save id (param.sfo's INSTALL_DIR_SAVEDATA, else TITLE_ID; the
same rule as src/probe.c). The saves already there are first copied to
USER_DIR/savedata-backups/<date>/, and the new ones are staged next to them and swapped in, so a
failed copy leaves them as they were. A console's own USB copy (sdimg_SPRJ0005) is encrypted with
that console's keys and cannot be read: it has to be exported decrypted on the PS4.

--export writes the saves in use into a .zip, in a folder named as a PS4 export
(CUSA00207_SPRJ0005/userdata0000...): a backup, or the saves for another computer. Such a .zip
is a SOURCE too; only its save files are read out of it, by name, whatever paths it holds.

Idea and rules from Awaken's BloodBorneButPc (SaveImport.cs).
"""
import argparse
from datetime import datetime
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare import sfo  # noqa: E402

SAVE_DIR = 'SPRJ0005'
# The game's system save, always written next to the character slots.
SYSTEM_FILE = 'userdata0010'
# A save file is a few MB; anything much bigger in an archive is not one.
MAX_SAVE_FILE = 64 << 20
# Folders that hold no saves: game files (thousands of folders in a dump) and our own backups.
SKIPPED = {'dvdroot_ps4', 'sce_sys', 'savedata-backups', 'shader_cache', 'mods'}
# The launcher's automatic copies in savedata-backups (auto_backup); the others are imports'.
AUTO_PREFIX = 'auto-'


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


def saves_in_use(user_dir, game_dir=None):
    """The save folder the game uses (user 1's SPRJ0005), or None without saves."""
    try:
        folder = Path(user_dir).expanduser() / 'savedata/1' / save_id(user_dir, game_dir) / SAVE_DIR
    except SaveImportError:
        return None
    return folder if save_files(folder) else None


def export_saves(user_dir, archive, game_dir=None):
    """Writes the saves in use into the .zip archive (replaced whole, or left as it was on an
    error); returns how many files went in."""
    folder = saves_in_use(user_dir, game_dir)
    if folder is None:
        raise SaveImportError('there are no saves to export yet')
    archive = Path(archive).expanduser()
    inside = f'{folder.parent.name}_{SAVE_DIR}'
    temp = archive.with_name(archive.name + '.part')
    try:
        with zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) as out:
            for path in save_files(folder):
                out.write(path, f'{inside}/{path.name}')
        os.replace(temp, archive)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise
    return len(save_files(folder))


def auto_backup(user_dir, keep, game_dir=None, now=None):
    """The launcher's automatic copy before a game: the saves in use go to
    USER_DIR/savedata-backups/auto-<date>/<id>/SPRJ0005 (imported back like any folder) and only
    the `keep` newest automatic copies stay. Saves unchanged since the newest copy are not copied
    again, so starting the game a few times without playing keeps the older copies. Returns the
    new copy's folder, or None (no saves, or nothing changed)."""
    folder = saves_in_use(user_dir, game_dir)
    if folder is None:
        return None
    backups = Path(user_dir).expanduser() / 'savedata-backups'
    copies = sorted(p for p in backups.glob(AUTO_PREFIX + '*') if p.is_dir())

    def state(files):
        return [(p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in files]
    if copies and state(save_files(copies[-1] / folder.parent.name / SAVE_DIR)) == state(save_files(folder)):
        return None
    copy = backups / (AUTO_PREFIX + (now or datetime.now()).strftime('%Y-%m-%d_%H%M%S'))
    staging = copy.with_name('.' + copy.name + '.part')
    shutil.rmtree(staging, ignore_errors=True)
    target = staging / folder.parent.name / SAVE_DIR
    target.mkdir(parents=True)
    try:
        for path in save_files(folder):
            shutil.copy2(path, target / path.name)
        staging.rename(copy)
    except OSError:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    copies.append(copy)
    for old in copies[:-max(1, keep)]:
        shutil.rmtree(old, ignore_errors=True)
    return copy


def unpack_export(archive, into):
    """The save files of a .zip (an export, or a PS4 export zipped) written flat into the folder
    `into`, with their dates; returns it. By the names of the files only: no path in the archive
    can place anything outside `into`."""
    try:
        with zipfile.ZipFile(archive) as source:
            folders = {}
            for member in source.infolist():
                parts = member.filename.replace('\\', '/').split('/')
                name = parts[-1]
                if member.is_dir() or not name.startswith(('userdata', 'backup')):
                    continue
                folders.setdefault('/'.join(parts[:-1]), []).append((name, member))
            # Its save folder: as is_save_folder, the newest when there are several.
            usable = {folder: files for folder, files in folders.items()
                      if (folder.upper().endswith(SAVE_DIR) or any(n == SYSTEM_FILE for n, _m in files))
                      and any(n.startswith('userdata') for n, _m in files)}
            if not usable:
                raise SaveImportError(f'{archive} has no Bloodborne save files (userdata)')
            files = max(usable.values(), key=lambda fs: max(m.date_time for _n, m in fs))
            into = Path(into)
            into.mkdir(parents=True, exist_ok=True)
            for name, member in files:
                if member.file_size > MAX_SAVE_FILE:
                    raise SaveImportError(f'{member.filename} is too big to be a save file')
                target = into / name
                with source.open(member) as data, open(target, 'wb') as out:
                    shutil.copyfileobj(data, out)
                stamp = time.mktime(member.date_time + (0, 0, -1))
                os.utime(target, (stamp, stamp))
    except (zipfile.BadZipFile, zipfile.LargeZipFile) as error:
        raise SaveImportError(f'{archive}: {error}') from error
    return into


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--user', required=True, help='the user folder (saves, shader cache)')
    parser.add_argument('--game', help='the game folder (its param.sfo gives the save id)')
    parser.add_argument('source', nargs='?',
                        help='a save folder, a folder to search for one, or an exported .zip')
    parser.add_argument('--export', metavar='ARCHIVE', help='write the saves in use into this .zip')
    a = parser.parse_args()
    if game_running():
        print('Failed: close the game first', file=sys.stderr)
        return 1
    if a.export:
        try:
            count = export_saves(a.user, a.export, a.game)
        except (SaveImportError, OSError) as error:
            print(f'Export failed: {error}', file=sys.stderr)
            return 1
        print(f'Exported {count} save files into {a.export}')
        return 0
    if not a.source:
        parser.error('a source to import, or --export')
    if zipfile.is_zipfile(a.source):
        with tempfile.TemporaryDirectory() as unpacked:
            try:
                folder = unpack_export(a.source, Path(unpacked) / SAVE_DIR)
                target, backup = import_saves(folder, a.user, a.game)
            except (SaveImportError, OSError) as error:
                print(f'Import failed: {error}', file=sys.stderr)
                return 1
        print(f'Imported {a.source} into {target}')
        if backup:
            print(f'Previous saves backed up in {backup}')
        return 0
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
