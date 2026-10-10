#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Button prompts and the gestures menu for this launch, made from the player's own game files.

    menu_prompts.py <game> --out <out> --prompts playstation|xbox|switch|keyboard
                    [--gestures 0|1] [--config bbport.ini]

prints the folders (os.pathsep-separated) that mods.py lays under the mods (--ui-mods):
- Xbox and Switch: the icons of Dommo's "DS3 Style" prompts (Nexus, Bloodborne mod 30) from
  assets/menu_prompts, put into the game's menu/common.tpf.dcx.
- keyboard: icons drawn for the keys bbport.ini binds (key.<input>=, else the defaults); needs
  Pillow. Which textures to draw (the KG_* icons and three atlas spots) follows Abken's KBM
  Icons Generator (Nexus, Bloodborne mod 537); nothing of it is used.
- --gestures 1: Dommo's "Stripped down gesture menu" (no motion-control icons), as edits of the
  game's menu/gesturetop.gfx.
Only the prompt textures change; every other texture is the game's, untouched. Results are
kept in <out>/menu-prompts, keyed by their inputs (game file, keys, these scripts and assets), so
a launch with the same choice is instant.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'assets' / 'menu_prompts'

# The prompt textures of menu/common.tpf.dcx and the PS4 input each shows (KG_OK is circle and
# KG_Cancel cross, Japanese style); clusters list (up, down, left, right).
ICONS = {
    'KG_OK': 'circle', 'KG_Cancel': 'cross', 'KG_R_U': 'triangle', 'KG_R_L': 'square',
    'KG_L1': 'l1', 'KG_R1': 'r1', 'KG_L2': 'l2', 'KG_R2': 'r2', 'KG_L3': 'l3', 'KG_R3': 'r3',
    'KG_Start': 'options', 'KG_TP_L': 'touchpad', 'KG_TP_R': 'touchpad_right',
    'KG_LS': ('move_up', 'move_down', 'move_left', 'move_right'),
    'KG_RS': ('look_up', 'look_down', 'look_left', 'look_right'),
    'KG_L_U': 'up', 'KG_L_D': 'down', 'KG_L_LR': (None, None, 'left', 'right'),
    'KG_L_UD': ('up', 'down', None, None), 'KG_L_UDLR': ('up', 'down', 'left', 'right'),
}
# The shared UI atlas also has big circle, cross and L3 prompts (26x26 at these spots); the
# block-aligned strip around them is all that is replaced in it.
ATLAS = 'MENU_Common_00091'
ATLAS_WIDTH = 1024
ATLAS_STRIP = (660, 120, 92, 32)
ATLAS_GLYPHS = {'KG_OK': (661, 123), 'KG_Cancel': (694, 123), 'KG_L3': (726, 123)}
# The keyboard's default keys (src/runtime_pad.c bind_defaults; the launcher's CONTROLS).
DEFAULT_KEYS = {
    'cross': 'Space', 'circle': 'Left Shift', 'square': 'E', 'triangle': 'Q', 'l1': '1',
    'r1': '3', 'l2': 'R', 'r2': 'F', 'l3': 'Z', 'r3': 'C', 'options': 'Return',
    'touchpad': 'Tab', 'touchpad_right': 'Backspace', 'up': 'I', 'down': 'K', 'left': 'J',
    'right': 'L', 'move_up': 'W', 'move_down': 'S', 'move_left': 'A', 'move_right': 'D',
    'look_up': 'Up', 'look_down': 'Down', 'look_left': 'Left', 'look_right': 'Right',
}
PROMPTS = ('playstation', 'xbox', 'switch', 'keyboard')
# DejaVu Sans Bold: next to the scripts in packaged builds (packaging/appimage-sharun.sh), else
# the system's; Pillow's own font otherwise (it lacks the arrows).
FONTS = (ROOT / 'fonts' / 'DejaVuSans-Bold.ttf', Path('/usr/share/fonts/TTF/DejaVuSans-Bold.ttf'),
         Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
         Path('/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf'),
         Path('/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf'))
# SDL key names (as bbport.ini has them) shortened to fit a key cap.
KEY_LABELS = {
    'space': 'Space', 'left shift': 'Shift', 'right shift': 'Shift', 'left ctrl': 'Ctrl',
    'right ctrl': 'Ctrl', 'left alt': 'Alt', 'right alt': 'AltGr', 'return': 'Enter',
    'keypad enter': 'Enter', 'backspace': '⌫', 'tab': 'Tab', 'escape': 'Esc', 'up': '↑',
    'down': '↓', 'left': '←', 'right': '→', 'capslock': 'Caps', 'delete': 'Del',
    'insert': 'Ins', 'home': 'Home', 'end': 'End', 'pageup': 'PgUp', 'pagedown': 'PgDn',
}


def prompts_for(pad_type):
    """The prompts for an SDL gamepad type (xbox360, xboxone, ps4, ps5, switchpro, joyconpair,
    ...; "" for a generic gamepad, None without one: the keyboard's)."""
    if pad_type is None:
        return 'keyboard'
    kind = pad_type.casefold()
    if kind.startswith('ps'):
        return 'playstation'
    if kind.startswith(('switch', 'joycon', 'gamecube')):
        return 'switch'
    # Xbox pads, the Steam Deck and most generic PC gamepads are labelled A/B/X/Y.
    return 'xbox'


def key_bindings(config):
    """input -> its first key (SDL name; '' unbound), from bbport.ini over the defaults."""
    keys = dict(DEFAULT_KEYS)
    try:
        lines = Path(config).read_text().splitlines() if config else []
    except OSError:
        lines = []
    for line in lines:
        name, _, value = line.partition('=')
        name = name.strip()
        if name.startswith('key.') and name[4:] in keys:
            keys[name[4:]] = value.split(',')[0].strip()
    return keys


def key_label(key):
    if not key:
        return '–'
    label = KEY_LABELS.get(key.casefold())
    if label:
        return label
    if key.casefold().startswith('keypad '):
        return 'Num' + key[7:]
    return key.upper() if len(key) == 1 else key[:5]


def _font(size):
    from PIL import ImageFont
    for path in FONTS:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size)


def _cap(draw, box, label, scale):
    """One key cap with its label, fitted into box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=max(2, (y1 - y0) // 5), fill=(58, 58, 58, 238),
                           outline=(170, 170, 170, 220), width=max(1, scale))
    size = int((y1 - y0) * 0.7)
    while size > 4:
        font = _font(size)
        left, top, right, bottom = draw.textbbox((0, 0), label, font=font)
        if right - left <= (x1 - x0) - 4 * scale:
            break
        size -= 1
    draw.text(((x0 + x1 - (right - left)) / 2 - left, (y0 + y1 - (bottom - top)) / 2 - top), label,
              font=font, fill=(216, 214, 210, 255))


def key_icon(keys, inputs):
    """A 32x32 prompt: one key cap, or a cluster (up, down, left, right; None left out)."""
    from PIL import Image, ImageDraw
    scale = 4
    size = 32 * scale
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    if isinstance(inputs, str):
        _cap(draw, (0, 3 * scale, size, size - 3 * scale), key_label(keys[inputs]), scale)
    else:
        up, down, left, right = inputs
        if up and down and left and right:  # a T: up above, left/down/right below
            w, h = (size - 2 * scale) // 3, 15 * scale
            spots = {'up': ((size - w) // 2, scale), 'left': (0, 16 * scale),
                     'down': ((size - w) // 2, 16 * scale), 'right': (size - w, 16 * scale)}
        elif left and right:  # a pair side by side
            w, h = 16 * scale, 24 * scale
            spots = {'left': (0, 4 * scale), 'right': (16 * scale, 4 * scale)}
        else:  # a pair one above the other
            w, h = 22 * scale, 16 * scale
            spots = {'up': (5 * scale, 0), 'down': (5 * scale, 16 * scale)}
        for name, which in zip(('up', 'down', 'left', 'right'), (up, down, left, right)):
            if which:
                x, y = spots[name]
                _cap(draw, (x, y, x + w - scale // 2, y + h - scale // 2), key_label(keys[which]), scale)
    return image.resize((32, 32), Image.LANCZOS)


def keyboard_assets(keys):
    """{slot: RGBA 32x32} and the atlas strip (at the game's scale) for keyboard prompts."""
    from PIL import Image
    icons = {slot: key_icon(keys, inputs) for slot, inputs in ICONS.items()}
    x0, y0, w, h = ATLAS_STRIP
    strip = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for slot, (x, y) in ATLAS_GLYPHS.items():
        strip.alpha_composite(icons[slot].resize((26, 26), Image.LANCZOS), (x - x0, y - y0))
    return icons, strip


def build_common(base, prompts, keys):
    """The game's menu/common.tpf.dcx (bytes `base`) with `prompts` (xbox, switch, keyboard)."""
    import menu_textures as mt
    tpf, header = mt.read_dcx(base)
    tpf = bytearray(tpf)
    textures = mt.textures(tpf)
    if prompts == 'keyboard':
        icons, strip = keyboard_assets(keys)
        blocks = {slot: mt.encode(image) for slot, image in icons.items()}
        strip = mt.encode(strip)
    else:
        folder = ASSETS / prompts
        blocks = {slot: mt.dds_blocks((folder / f'{slot}.dds').read_bytes()) for slot in ICONS}
        strip = mt.dds_blocks((folder / 'atlas.dds').read_bytes())
    for slot, new in blocks.items():
        texture = textures[slot]
        if len(new) != (texture['width'] // 4) * (texture['height'] // 4):
            raise ValueError(f'{slot}: unexpected size')
        mt.put_blocks(tpf, texture, dict(enumerate(new)))
    atlas = textures[ATLAS]
    if atlas['width'] != ATLAS_WIDTH:
        raise ValueError(f'{ATLAS} is {atlas["width"]} wide, expected {ATLAS_WIDTH}')
    which, rect = mt.rect_blocks(atlas, *ATLAS_STRIP)
    if rect != ATLAS_STRIP or len(which) != len(strip):
        raise ValueError('unexpected atlas strip')
    mt.put_blocks(tpf, atlas, dict(zip(which, strip)))
    return mt.write_dcx(bytes(tpf), header)


def apply_gestures(original):
    """Dommo's gestures menu: the edits of assets/menu_prompts/gesturetop.json."""
    patch = json.loads((ASSETS / 'gesturetop.json').read_text())
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


def sources(*extra):
    """A hash of what the results are made from: these scripts and the files used."""
    digest = hashlib.sha256()
    for path in (Path(__file__), Path(__file__).with_name('menu_textures.py'), *extra):
        digest.update(path.read_bytes())
    return digest.hexdigest()


def cached(out, key, relative, make):
    """<out>/menu-prompts/<key>/dvdroot_ps4/menu/<relative>, made once by make()."""
    folder = Path(out) / 'menu-prompts' / key
    target = folder / 'dvdroot_ps4' / 'menu' / relative
    if not target.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(target.name + '.part')
        partial.write_bytes(make())
        os.replace(partial, target)
    return folder


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game', type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--prompts', choices=PROMPTS, default='playstation')
    parser.add_argument('--gestures', choices=('0', '1'), default='0')
    parser.add_argument('--config')
    args = parser.parse_args(argv)
    folders, used = [], set()
    if args.prompts != 'playstation':
        base = game_file(args.game, 'common.tpf.dcx')
        stat = base.stat()
        keys = key_bindings(args.config) if args.prompts == 'keyboard' else {}
        labels = sorted((name, key_label(key)) for name, key in keys.items())
        used_assets = sorted((ASSETS / args.prompts).glob('*.dds')) if args.prompts != 'keyboard' else []
        key = hashlib.sha256(json.dumps([sources(*used_assets), args.prompts, labels, str(base),
                                         stat.st_size, stat.st_mtime_ns]).encode()).hexdigest()[:16]
        folders.append(cached(args.out, f'prompts-{key}', 'common.tpf.dcx',
                              lambda: build_common(base.read_bytes(), args.prompts, keys)))
        used.add(f'prompts-{key}')
    if args.gestures == '1':
        base = game_file(args.game, 'gesturetop.gfx')
        stat = base.stat()
        key = hashlib.sha256(json.dumps([sources(ASSETS / 'gesturetop.json'), str(base), stat.st_size,
                                         stat.st_mtime_ns]).encode()).hexdigest()[:16]
        folders.append(cached(args.out, f'gestures-{key}', 'gesturetop.gfx',
                              lambda: apply_gestures(base.read_bytes())))
        used.add(f'gestures-{key}')
    # Older results (other keys, other game folders) are dropped.
    cache = Path(args.out) / 'menu-prompts'
    if cache.is_dir():
        for entry in cache.iterdir():
            if entry.name not in used:
                shutil.rmtree(entry, ignore_errors=True)
    print(os.pathsep.join(str(f) for f in folders))


if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        main()
    except (OSError, ValueError) as error:
        print(f'Button prompts: {error}; the game\'s own are used', file=sys.stderr)
        print('')
