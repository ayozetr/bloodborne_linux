#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""The Xbox and Switch button art of the Linux fork (assets/menu_prompts: Dommo's "DS3 Style"
prompts, Nexus Bloodborne mod 30) for the port's live button prompts (gpu/shim/bbport_button_prompts):
each KG_*.dds (BC7, 32x32) as raw RGBA, <out>/<xbox|switch>/KG_*.rgba, 32 * 32 * 4 bytes.
Prints <out> (run.sh exports it as BB_PROMPT_ART), or nothing when Pillow cannot read them.
Files already there and newer than their source are kept."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'assets' / 'menu_prompts'
SIZE = 32


def convert(source, out):
    from PIL import Image
    written = 0
    for style in ('xbox', 'switch'):
        for dds in sorted((source / style).glob('KG_*.dds')):
            target = out / style / (dds.stem + '.rgba')
            if target.is_file() and target.stat().st_mtime >= dds.stat().st_mtime:
                continue
            image = Image.open(dds).convert('RGBA')
            if image.size != (SIZE, SIZE):
                raise ValueError(f'{dds.name}: {image.size[0]}x{image.size[1]}, not {SIZE}x{SIZE}')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(image.tobytes())
            written += 1
    return written


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--source', type=Path, default=SOURCE)
    args = parser.parse_args()
    try:
        convert(args.source, args.out)
    except Exception as error:  # Pillow missing or an unreadable file: the prompts keep their letters
        print(f'Button prompts: the Xbox and Switch art not prepared ({error})', file=sys.stderr)
        return 0
    print(args.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
