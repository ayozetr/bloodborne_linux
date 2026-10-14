#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Install Bloodborne from your own PS4 package files (.pkg): the game, its updates and add-ons.

    pkg_install.py --dest DIR GAME.pkg [UPDATE.pkg ...] [DLC.pkg ...]

Each package is told apart by its header (the content ID) and its param.sfo, not by its file name:
the game (category gd) goes to DIR/<title ID>, updates (gp) are merged into it oldest first, and
add-ons (ac) go to DIR/DLC/<label> (the launcher's DLC folder). The packages are extracted with
pkgextract (github.com/paulomanrique/ps4-pkg-extractor, Unlicense) into a new folder under DIR, so
nothing already there is replaced: a game folder that exists stops the install. game_check.py
checks the result (the 1.09 executable, the shaders unpack).

The last lines are GAME_DIR=<path> and, with add-ons, DLC_DIR=<path>, for the launcher.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from game_check import explain, problem  # noqa: E402
from prepare import sfo  # noqa: E402

PKG_MAGIC = b'\x7fCNT'
# The content ID (UP9000-CUSA00900_00-BLOODBORNE000000): the publisher, the title ID and the
# package's label, at 0x40 in the header.
CONTENT_ID = slice(0x40, 0x40 + 36)


class InstallError(Exception):
    pass


def content_id(pkg):
    """The package's content ID; InstallError when the file is not a PS4 package."""
    with open(pkg, 'rb') as stream:
        header = stream.read(0x80)
    if len(header) < 0x80 or header[:4] != PKG_MAGIC:
        raise InstallError(f'{pkg} is not a PS4 package (.pkg)')
    value = header[CONTENT_ID].rstrip(b'\0').decode('ascii', 'replace')
    if len(value) != 36 or value[6] != '-' or value[16] != '_' or value[19] != '-':
        raise InstallError(f'{pkg}: unexpected content ID {value!r}')
    return value


def extractor_path(explicit=None):
    """pkgextract: explicit, BB_PKGEXTRACT (the AppImage's copy), build.sh's, else on PATH."""
    for candidate in (explicit, os.environ.get('BB_PKGEXTRACT'),
                      Path(__file__).resolve().parent.parent / 'out/pkgextract/bin/pkgextract'):
        if candidate and Path(candidate).is_file():
            return str(candidate)
    found = shutil.which('pkgextract')
    if not found:
        raise InstallError('pkgextract not found (build.sh builds it when cargo is installed)')
    return found


def extract(extractor, pkg, out, log):
    """pkgextract into a folder that does not exist yet (its -f would delete one that does)."""
    if out.exists():
        raise InstallError(f'{out} exists')
    log(f'Install: extracting {Path(pkg).name}')
    run = subprocess.run([extractor, '-o', str(out), str(pkg)], stdin=subprocess.DEVNULL,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if run.returncode != 0:
        tail = '\n'.join(run.stdout.strip().splitlines()[-5:])
        raise InstallError(f'pkgextract failed on {Path(pkg).name}:\n{tail}')
    try:
        return sfo((out / 'sce_sys/param.sfo').read_bytes())
    except (OSError, ValueError, IndexError) as error:
        raise InstallError(f'{Path(pkg).name}: no readable sce_sys/param.sfo ({error})') from error


def merge(source, target):
    """An update over the game: its files replace the game's (eboot.bin and sce_sys too)."""
    for path in sorted(source.rglob('*')):
        destination = target / path.relative_to(source)
        if path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(path, destination)


def install(pkgs, dest, extractor=None, log=print):
    """Installs the packages into dest; returns (game folder, DLC folder or None)."""
    dest = Path(dest).expanduser().resolve()
    pkgs = [Path(p).expanduser().resolve() for p in pkgs]
    ids = {pkg: content_id(pkg) for pkg in pkgs}
    titles = {cid[7:16] for cid in ids.values()}
    if len(titles) != 1:
        raise InstallError('the packages are of different titles: ' + ', '.join(sorted(titles)))
    title = titles.pop()
    game_dir = dest / title
    if game_dir.exists():
        raise InstallError(f'{game_dir} already exists: choose another folder, or move it away')
    dest.mkdir(parents=True, exist_ok=True)
    needed = sum(pkg.stat().st_size for pkg in pkgs)
    free = shutil.disk_usage(dest).free
    if free < needed * 1.05:
        raise InstallError(f'not enough space in {dest}: {needed / 2**30:.1f} GiB needed, '
                           f'{free / 2**30:.1f} GiB free')
    extractor = extractor_path(extractor)
    work = dest / f'.bbport-install-{os.getpid()}'
    work.mkdir()
    try:
        games, updates, addons = [], [], []
        for number, pkg in enumerate(pkgs):
            out = work / str(number)
            info = extract(extractor, pkg, out, log)
            category = str(info.get('CATEGORY', ''))
            entry = (str(info.get('APP_VER', '')), ids[pkg][20:], out, pkg)
            if category == 'gd':
                games.append(entry)
            elif category.startswith('gp'):
                updates.append(entry)
            elif category == 'ac':
                addons.append(entry)
            else:
                raise InstallError(f'{pkg.name}: unexpected package category {category!r}')
        if len(games) != 1:
            raise InstallError(f'{len(games)} game packages given: one is needed (category gd)')
        os.replace(games[0][2], game_dir)
        log(f'Install: game {title} version {games[0][0]} in {game_dir}')
        for version, _label, out, pkg in sorted(updates):
            merge(out, game_dir)
            log(f'Install: update {version} ({pkg.name}) merged')
        dlc_dir = None
        if addons:
            dlc_dir = dest / 'DLC'
            dlc_dir.mkdir(exist_ok=True)
            for _version, label, out, pkg in addons:
                target = dlc_dir / label
                if target.exists():
                    log(f'Install: add-on {label} already in {dlc_dir}, kept as it was')
                    continue
                os.replace(out, target)
                log(f'Install: add-on {label} in {target}')
    finally:
        shutil.rmtree(work, ignore_errors=True)
    found = problem(game_dir)
    if found:
        log('Install: ' + explain(*found))
    else:
        log('Install: the game is ready (Bloodborne 1.09)')
    return game_dir, dlc_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--dest', required=True, help='the folder to install into')
    parser.add_argument('--extractor', help='pkgextract (default: BB_PKGEXTRACT, build.sh, PATH)')
    parser.add_argument('pkgs', nargs='+', help='the game, update and add-on packages')
    a = parser.parse_args()
    try:
        game_dir, dlc_dir = install(a.pkgs, a.dest, a.extractor,
                                    lambda line: print(line, flush=True))
    except (InstallError, OSError) as error:
        print(f'Install failed: {error}', file=sys.stderr)
        return 1
    print(f'GAME_DIR={game_dir}')
    if dlc_dir:
        print(f'DLC_DIR={dlc_dir}')
    return 0 if not problem(game_dir) else 3


if __name__ == '__main__':
    sys.exit(main())
