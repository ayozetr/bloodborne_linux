from paths import ROOT
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

import menu_prompts
import menu_textures as mt


def fake_common(textures):
    """A PS4 TPF in a DCX holding `textures` (name -> (width, height)), BC7, data all zero but
    for one marker byte per texture."""
    names = list(textures)
    count = len(names)
    table = 16 + 0x24 * count
    name_data, name_at = b'', []
    for name in names:
        name_at.append(table + len(name_data))
        name_data += name.encode('utf-16-le') + b'\0\0'
    data_at = table + len(name_data)
    entries, blobs = b'', b''
    for i, name in enumerate(names):
        w, h = textures[name]
        size = max(w // 4, 8) * max(h // 4, 8) * mt.BLOCK  # whole 8x8-block tiles
        blob = bytearray(size)
        blob[0] = i + 1
        entries += struct.pack('<IIBBBBHHiiiii', data_at + len(blobs), size, 0x66, 0, 1, 0, w, h,
                               1, 0xD, name_at[i], 0, mt.BC7)
        blobs += bytes(blob)
    tpf = b'TPF\0' + struct.pack('<II', 0, count) + bytes([4, 0, 1, 0]) + entries + name_data + blobs
    header = bytearray(0x4c)
    header[0:4], header[0x28:0x2c] = b'DCX\0', b'DFLT'
    return mt.write_dcx(tpf, header)


def pixels(image):
    raw = image.convert('RGBA').tobytes()
    return [tuple(raw[i:i + 4]) for i in range(0, len(raw), 4)]


class TextureTests(unittest.TestCase):
    def test_tile_order_is_a_permutation_with_morton_tiles(self):
        order = mt.tile_order(16, 8)
        self.assertEqual(sorted(order), list(range(128)))
        self.assertEqual(order[:4], [0, 1, 16, 17])  # x, then y, inside the first tile
        self.assertEqual(order[64], 8)  # the second tile starts 8 blocks to the right

    def test_bc7_round_trip_keeps_a_key_icon(self):
        image = menu_prompts.key_icon(menu_prompts.DEFAULT_KEYS, 'circle')
        back = mt.decode(32, 32, mt.encode(image))
        pairs = list(zip(pixels(image), pixels(back)))
        # Transparency everywhere, colour where it shows (mode 6 has one colour line per block:
        # a cap's border, fill and letter share blocks); see-through corners stay so.
        self.assertLess(sum(abs(p[3] - q[3]) for p, q in pairs) / len(pairs), 4)
        shown = [abs(a - b) for p, q in pairs if p[3] > 128 for a, b in zip(p[:3], q[:3])]
        self.assertLess(sum(shown) / len(shown), 16)
        self.assertEqual(back.getpixel((0, 31))[3], 0)


class PromptTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        sizes = {slot: (32, 32) for slot in menu_prompts.ICONS}
        sizes[menu_prompts.ATLAS] = (1024, 512)
        sizes['MENU_Icon_00001'] = (64, 64)
        self.base = fake_common(sizes)

    def test_xbox_prompts_are_dommos_blocks_and_nothing_else_changes(self):
        tpf, _ = mt.read_dcx(menu_prompts.build_common(self.base, 'xbox', {}))
        old, _ = mt.read_dcx(self.base)
        textures = mt.textures(tpf)
        self.assertEqual(len(tpf), len(old))
        expected = mt.dds_blocks((menu_prompts.ASSETS / 'xbox' / 'KG_OK.dds').read_bytes())
        self.assertEqual(mt.blocks(tpf, textures['KG_OK']), expected)
        other = textures['MENU_Icon_00001']
        self.assertEqual(tpf[other['offset']:other['offset'] + other['size']],
                         old[other['offset']:other['offset'] + other['size']])
        # Only the strip's blocks of the atlas change.
        atlas = textures[menu_prompts.ATLAS]
        which, _ = mt.rect_blocks(atlas, *menu_prompts.ATLAS_STRIP)
        changed = [i for i, (a, b) in enumerate(zip(mt.blocks(old, atlas), mt.blocks(tpf, atlas))) if a != b]
        self.assertTrue(set(changed) <= set(which))

    def test_ab_swap_swaps_the_cross_and_circle_glyphs(self):
        config = self.root / 'bbport.ini'
        config.write_text('pad.cross=b\npad.circle=a\n')
        self.assertTrue(menu_prompts.ab_swapped(config))
        config.write_text('pad.cross=b\n')
        self.assertFalse(menu_prompts.ab_swapped(config))
        self.assertFalse(menu_prompts.ab_swapped(None))
        plain, _ = mt.read_dcx(menu_prompts.build_common(self.base, 'switch', {}))
        swapped, _ = mt.read_dcx(menu_prompts.build_common(self.base, 'switch', {}, swap_ab=True))
        textures = mt.textures(swapped)
        self.assertEqual(mt.blocks(swapped, textures['KG_OK']), mt.blocks(plain, textures['KG_Cancel']))
        self.assertEqual(mt.blocks(swapped, textures['KG_Cancel']), mt.blocks(plain, textures['KG_OK']))
        self.assertEqual(mt.blocks(swapped, textures['KG_R_U']), mt.blocks(plain, textures['KG_R_U']))

    def test_launcher_swap_binds_what_the_runtime_reads(self):
        launcher = (ROOT / 'launcher' / 'bbport_launcher.py').read_text()
        self.assertIn('("cross", "Крест", "Space", "a")', launcher)
        self.assertIn('("circle", "Круг", "Left Shift", "b")', launcher)
        self.assertIn('self.set_control("pad", "cross", "b" if swap else None)', launcher)
        self.assertIn('self.set_control("pad", "circle", "a" if swap else None)', launcher)

    def test_keyboard_prompts_follow_the_bound_keys(self):
        config = self.root / 'bbport.ini'
        config.write_text('key.cross=Return, Space\nkey.circle=\n')
        keys = menu_prompts.key_bindings(config)
        self.assertEqual((keys['cross'], keys['circle'], keys['square']), ('Return', '', 'E'))
        self.assertEqual([menu_prompts.key_label(k) for k in ('Return', '', 'e', 'Left Shift', 'Up')],
                         ['Enter', '–', 'E', 'Shift', '↑'])
        tpf, _ = mt.read_dcx(menu_prompts.build_common(self.base, 'keyboard', keys))
        textures = mt.textures(tpf)
        self.assertNotEqual(mt.blocks(tpf, textures['KG_Cancel']), mt.blocks(tpf, textures['KG_OK']))

    def test_runtime_default_keys_match(self):
        source = (ROOT / 'src' / 'runtime_pad.c').read_text()
        for name, key in menu_prompts.DEFAULT_KEYS.items():
            scancode = {'Space': 'SPACE', 'Left Shift': 'LSHIFT', 'Return': 'RETURN', 'Tab': 'TAB',
                        'Backspace': 'BACKSPACE', 'Up': 'UP', 'Down': 'DOWN', 'Left': 'LEFT',
                        'Right': 'RIGHT'}.get(key, key)
            self.assertIn(f'{{IN_{name.upper()},SDL_SCANCODE_{scancode}}}', source)

    def test_prompts_follow_the_controller_type(self):
        cases = {'xbox360': 'xbox', 'xboxone': 'xbox', 'ps4': 'playstation', 'ps5': 'playstation',
                 'switchpro': 'switch', 'joyconpair': 'switch', '': 'xbox', None: 'keyboard'}
        for kind, expected in cases.items():
            with self.subTest(kind=kind):
                self.assertEqual(menu_prompts.prompts_for(kind), expected)

    def test_gestures_patch_needs_the_games_file(self):
        original = b'0123456789'
        patch = dict(original_sha256=hashlib.sha256(original).hexdigest(),
                     result_sha256=hashlib.sha256(b'01ab456789!').hexdigest(),
                     edits=[[2, 2, '6162'], [10, 0, '21']])
        assets = self.root / 'assets'
        assets.mkdir()
        (assets / 'gesturetop.json').write_text(json.dumps(patch))
        with mock.patch.object(menu_prompts, 'ASSETS', assets):
            self.assertEqual(menu_prompts.apply_gestures(original), b'01ab456789!')
            with self.assertRaises(ValueError):
                menu_prompts.apply_gestures(b'another file')

    def test_command_caches_and_cleans(self):
        game = self.root / 'game' / 'dvdroot_ps4' / 'menu'
        game.mkdir(parents=True)
        (game / 'common.tpf.dcx').write_bytes(self.base)
        out = self.root / 'out'
        import contextlib
        import io
        for prompts in ('switch', 'switch', 'xbox'):
            printed = io.StringIO()
            with contextlib.redirect_stdout(printed):
                menu_prompts.main([str(self.root / 'game'), '--out', str(out), '--prompts', prompts])
            folder = Path(printed.getvalue().strip())
            self.assertTrue((folder / 'dvdroot_ps4/menu/common.tpf.dcx').is_file())
        self.assertEqual([p.name for p in (out / 'menu-prompts').iterdir()], [folder.name])
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            menu_prompts.main([str(self.root / 'game'), '--out', str(out)])
        self.assertEqual(printed.getvalue().strip(), '')


if __name__ == '__main__':
    unittest.main()
