#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Names for Seamless co-op's kit items while Seamless co-op is off.

BBSC gives every character five items of its own (the Hunt, Kin, Bloodlust and Duel Bells and the
Parting Blank) in goods slots the game leaves unused, and puts their texts into the game's text
table in memory while it runs (bbsc/, "The BBSC hunter's kit"). With Seamless co-op off nothing
does, and the items stay in the saves as "?GoodsName?". This layer writes their name, BBSC's
caption and a one-line help saying they need Seamless co-op into the game's item texts
(item.msgbnd.dcx, FMG 10 names, 20 help, 24 captions), in every language: only into slots the
game leaves empty, so no text of the game changes. With Seamless co-op on there is no layer, and
BBSC's own texts show as before. The names and captions are BBSC's, in the languages BBSC has them
in (bbsc_kit_texts.json, made from bbsc/translations by --update; English otherwise).
"""
import argparse
import hashlib
import json
import shutil
import struct
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quit_menu import bnd4_files, pack_dcx, read_fmg, rebuild_bnd4, unpack_dcx, write_fmg  # noqa: E402

NAMES, HELP, CAPTIONS = 10, 20, 24  # item.msgbnd.dcx files: goods names, help lines, captions
# bbsc/emulator/src/core/bbsc_messages.inc (BbscKit in bloodborne_re.cpp): goods id, name, caption.
KIT = {
    4016: ("Hunt Bell",
           "An old bell carried by the hunters of the\nworkshop, its toll heard across every world.\n\n"
           "Ring it, and hunters who answer with a\nKin Bell may join your hunt. Together you\n"
           "walk the night, through every lamp,\ndeath and dream, until the hunt is done."),
    4121: ("Kin Bell",
           "A small bell of the choir, its chime\nfaint, but true.\n\nHunters who hear a Hunt Bell may "
           "answer\nwith it, crossing into another world to\nstand at the side of kin. What is slain\n"
           "there is slain for both."),
    11201: ("Bloodlust Bell",
            "A bell that sounds only for the blood-drunk.\n\nNo maiden need ring for its toll to be\n"
            "heard: every hunter of the night is prey,\nalone or in company, wherever they walk.\n\n"
            "The hunt for hunters never ends."),
    4313: ("Duel Bell",
           "A cracked bell with a sour, discordant chime.\n\nRing it while hunting together, and the\n"
           "resonance binding the hunters turns to\nrivalry: they may strike one another as foes.\n\n"
           "Ring it again to restore the old bond.\nOnly the beckoner decides; a cooperator\n"
           "who rings it merely asks."),
    11251: ("Parting Blank",
            "A blank of silent powder.\n\nIts inaudible burst breaks the resonance\nbinding hunters of "
            "different worlds, and\neach returns to their own night."),
}
# The help line, by the game's text folder (English for the others).
OFF_HELP = {  # one line: the inventory list shows only the first line of an item's help
    'engus': "Needs BBSC on (the launcher's Online page).",
    'spaes': "Requiere BBSC (página Online del lanzador).",
    'itait': "Richiede BBSC (pagina Online del launcher).",
    'frafr': "Nécessite BBSC (page En ligne du lanceur).",
    'deude': "Benötigt BBSC (Online-Seite des Launchers).",
    'porbr': "Requer o BBSC (página Online do launcher).",
    'rusru': "Нужен BBSC (страница «Онлайн» в лаунчере).",
    'zhocn': "需要开启 BBSC（启动器的“联机”页面）。",
}
OFF_HELP.update(spaar=OFF_HELP['spaes'], porpt=OFF_HELP['porbr'], enggb=OFF_HELP['engus'])
# BBSC's translations (bbsc/translations/<code>.json) by the game's text folders.
TRANSLATION_FOLDERS = {'es': ('spaes', 'spaar'), 'fr': ('frafr',), 'de': ('deude',), 'it': ('itait',),
                       'pt': ('porbr', 'porpt'), 'ru': ('rusru',)}
TEXTS_FILE = Path(__file__).resolve().with_suffix('.json')


def translated():
    """{text folder: {goods id: (name, caption)}} from bbsc_kit_texts.json; {} without it."""
    try:
        data = json.loads(TEXTS_FILE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return {folder: {int(goods): tuple(texts) for goods, texts in kit.items()}
            for folder, kit in data.items()}


def update_texts(translations):
    """Writes bbsc_kit_texts.json from BBSC's translations folder (English keys)."""
    data = {}
    for code, folders in TRANSLATION_FOLDERS.items():
        table = json.loads((translations / f'{code}.json').read_text(encoding='utf-8'))
        # Its keys and texts write a line break as a backslash and n.
        def tr(text):
            return table.get(text.replace('\n', '\\n'), text.replace('\n', '\\n')).replace('\\n', '\n')
        kit = {str(goods): [tr(name), tr(caption)] for goods, (name, caption) in KIT.items()}
        for folder in folders:
            data[folder] = kit
    TEXTS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


def item_texts(archive, language, texts=None):
    """item.msgbnd.dcx with the kit's texts in the slots the game leaves empty; None if none is."""
    texts = texts or KIT
    bnd = unpack_dcx(archive)
    files = {file_id: bnd[offset:offset + length] for _, offset, length, file_id in bnd4_files(bnd)}
    if not {NAMES, HELP, CAPTIONS} <= files.keys():
        raise ValueError('item texts without the goods name, help or caption files')
    help_line = OFF_HELP.get(language, OFF_HELP['engus'])
    replace = {}
    for file_id in (NAMES, HELP, CAPTIONS):
        strings = read_fmg(files[file_id])
        changes = {goods: (name if file_id == NAMES else help_line if file_id == HELP else caption)
                   for goods, (name, caption) in texts.items() if strings.get(goods) is None}
        if changes:
            strings.update(changes)
            replace[file_id] = write_fmg(files[file_id], strings)
    return pack_dcx(archive, rebuild_bnd4(bnd, replace)) if replace else None


def write_layer(game, out):
    msg = game / 'dvdroot_ps4' / 'msg'
    languages = translated()
    written = 0
    for folder in sorted(p for p in msg.iterdir() if p.is_dir()):
        source = folder / 'item.msgbnd.dcx'
        if not source.is_file():
            continue
        language = folder.name.casefold()
        archive = item_texts(source.read_bytes(), language, languages.get(language))
        if archive is None:
            continue
        target = out / 'dvdroot_ps4' / 'msg' / folder.name / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive)
        written += 1
    if not written:
        raise ValueError('no item texts to fill in the game')
    print(f'Seamless co-op kit: item texts for {written} languages', file=sys.stderr)


def layer_key(game):
    """What the layer is made from: these scripts and the game files they read."""
    digest = hashlib.sha256()
    here = Path(__file__).resolve().parent
    for script in (here / 'bbsc_kit_texts.py', here / 'quit_menu.py', TEXTS_FILE):
        if script.is_file():
            digest.update(script.read_bytes())
    msg = game / 'dvdroot_ps4' / 'msg'
    if msg.is_dir():
        for source in sorted(folder / 'item.msgbnd.dcx' for folder in msg.iterdir() if folder.is_dir()):
            if source.is_file():
                stat = source.stat()
                digest.update(f'{source.resolve()}\0{stat.st_size}\0{stat.st_mtime_ns}\0'.encode())
    return digest.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('game', type=Path, nargs='?', help='game folder (with dvdroot_ps4)')
    p.add_argument('--out', type=Path, help='mod layer folder to write (replaced)')
    p.add_argument('--bbsc', default='0', help='1: Seamless co-op is on (BBSC shows its own texts)')
    p.add_argument('--update', type=Path, metavar='TRANSLATIONS',
                   help='rewrite bbsc_kit_texts.json from bbsc/translations')
    a = p.parse_args()
    if a.update:
        update_texts(a.update)
        return
    if not a.game or not a.out:
        p.error('the game folder and --out are needed')
    stamp = a.out.with_name(a.out.name + '.source')  # beside the layer, not a game file in it
    if a.bbsc == '1':
        shutil.rmtree(a.out, ignore_errors=True)
        stamp.unlink(missing_ok=True)
        print('')
        return
    # Made once per game folder.
    key = layer_key(a.game)
    try:
        reuse = stamp.read_text() == key
    except OSError:
        reuse = False
    if not reuse:
        shutil.rmtree(a.out, ignore_errors=True)
        try:
            write_layer(a.game, a.out)
            stamp.write_text(key)
        except BaseException:
            shutil.rmtree(a.out, ignore_errors=True)  # no half-written layer
            raise
    # The layer for mods.py --ui-mods (run.sh), under the mods: a mod's own item texts win.
    print(a.out)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, struct.error, zlib.error) as error:
        # Optional: the game starts with the game's own texts.
        print(f'Seamless co-op kit: item texts: {error}; the game starts without them', file=sys.stderr)
        print('')
