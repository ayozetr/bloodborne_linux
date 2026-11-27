#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Checks a built AppImage before it is published:

- its version (X-AppImage-Version in the .desktop file) is the launcher's (launcher/bbport_update.py);
- no program or library in it uses BMI2 instructions (shlx, sarx, shrx, rorx, pdep, pext, mulx)
  unless packaging/bmi2-allowed.txt lists it. Those are libraries that pick their code by the CPU
  at run time. Anything else with BMI2 stops at once ("illegal instruction") on CPUs without it:
  AMD FX and Phenom, Intel before Haswell (issue #39, when the AppImage took CachyOS's x86-64-v3
  libraries);
- the port's own files are there (bb-probe, libbbgpu, the launcher, the FSR 4.1.1 build's tools).

    python3 packaging/check-appimage.py dist/Bloodborne-bbport-x86_64.AppImage

Needs objdump (binutils). Exits 1 with a list of what is wrong.
"""
import concurrent.futures
import fnmatch
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BMI2 = re.compile(rb'\s(shlx|sarx|shrx|rorx|pdep|pext|mulx)\s')
NEEDED = ['bb-probe', 'libbbgpu.so', 'bbport_launcher.py',
          'dxil-spirv', 'fsr4cap.exe', 'spirv-dis', 'spirv-as']


def allowed_patterns():
    lines = (ROOT / 'packaging' / 'bmi2-allowed.txt').read_text(encoding='utf-8').splitlines()
    return [line.split('#')[0].strip() for line in lines if line.split('#')[0].strip()]


def launcher_version():
    text = (ROOT / 'launcher' / 'bbport_update.py').read_text(encoding='utf-8')
    return re.search(r'^VERSION = "([^"]+)"', text, re.M).group(1)


def is_elf(path):
    try:
        with open(path, 'rb') as f:
            return f.read(4) == b'\x7fELF'
    except OSError:
        return False


def bmi2_count(path):
    out = subprocess.run(['objdump', '-d', '--no-show-raw-insn', str(path)],
                         capture_output=True).stdout
    return len(BMI2.findall(out))


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-3].strip(), file=sys.stderr)
        return 2
    appimage = Path(argv[1]).resolve()
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([str(appimage), '--appimage-extract'], cwd=tmp, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        root = Path(tmp) / 'squashfs-root'
        root = root.resolve()

        desktops = list(root.glob('*.desktop'))
        version = None
        for desktop in desktops:
            match = re.search(r'^X-AppImage-Version=(.+)$', desktop.read_text(encoding='utf-8'), re.M)
            version = match and match.group(1).strip()
        expected = launcher_version()
        if version != expected:
            problems.append(f'version: the AppImage says {version!r}, the launcher {expected!r}')

        names = {p.name for p in root.rglob('*')}
        for needed in NEEDED:
            if needed not in names:
                problems.append(f'missing: {needed}')

        elfs = [p for p in root.rglob('*') if p.is_file() and not p.is_symlink() and is_elf(p)]
        patterns = allowed_patterns()
        with concurrent.futures.ThreadPoolExecutor(os.cpu_count() or 4) as pool:
            counts = dict(zip(elfs, pool.map(bmi2_count, elfs)))
        with_bmi2 = sorted((p for p, n in counts.items() if n), key=lambda p: p.name)
        for path in with_bmi2:
            rel = path.relative_to(root)
            allowed = any(fnmatch.fnmatch(path.name, pattern) for pattern in patterns)
            print(f'{"allowed" if allowed else "NOT ALLOWED"}: {rel} ({counts[path]} BMI2 instructions)')
            if not allowed:
                problems.append(f'BMI2 in {rel} ({counts[path]} instructions): not in '
                                'packaging/bmi2-allowed.txt')
        print(f'{len(elfs)} programs and libraries checked, {len(with_bmi2)} with BMI2; version {version}')

    for problem in problems:
        print(f'error: {problem}', file=sys.stderr)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
