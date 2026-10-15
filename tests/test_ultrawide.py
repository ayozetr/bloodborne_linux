from paths import ROOT
import struct
import tempfile
import unittest
from pathlib import Path

import hud_layout
from patches import (CAMERA_ASPECT, EBOOT_BASE, HUD_PROJECTION_WIDTH, MARKER_BIAS, OUTPUT_SIZE,
                     ULTRAWIDE_TEMPLATE, compile_patches, hud_canvas, scaled_sizes, ui_size,
                     ultrawide_writes)

XML = ROOT / 'patches/Bloodborne.xml'
SEGMENTS = [(0, 0x6000000)]


def apply(writes):
    image = {}
    for offset, data in writes:
        for i, byte in enumerate(data):
            image[offset + i] = byte
    return image


def value(image, offset, size=4):
    return bytes(image[offset + i] for i in range(size))


class UltrawideTests(unittest.TestCase):
    def test_canvas(self):
        self.assertEqual(hud_canvas((3440, 1440)), (2580, 1080))
        self.assertEqual(hud_canvas((2560, 1080)), (2560, 1080))
        # 16:9 and narrower keep the game's own coordinates.
        self.assertEqual(hud_canvas((3840, 2160)), OUTPUT_SIZE)
        self.assertEqual(hud_canvas((1920, 1200)), OUTPUT_SIZE)

    def test_2560x1080_matches_the_community_patch(self):
        ours = apply(ultrawide_writes(XML, (2560, 1080), '01.09', SEGMENTS))
        theirs = apply(compile_patches(XML, [ULTRAWIDE_TEMPLATE], '01.09', SEGMENTS))
        # Scene and UI viewport sizes come from resolution_writes instead.
        for offset, byte in ours.items():
            self.assertEqual(theirs[offset], byte, hex(offset + EBOOT_BASE))

    def test_3440x1440_values(self):
        image = apply(ultrawide_writes(XML, (3440, 1440), '01.09', SEGMENTS))
        aspect, = struct.unpack('<f', value(image, CAMERA_ASPECT))
        width, = struct.unpack('<f', value(image, HUD_PROJECTION_WIDTH))
        self.assertAlmostEqual(aspect, 3440 / 1440, places=5)
        self.assertEqual(width, 2580.0)
        for site in MARKER_BIAS:
            bias, = struct.unpack('<f', value(image, site))
            self.assertAlmostEqual(bias, 0.5 * 1920 / 2580, places=6)

    def test_32_9_has_its_own_canvas(self):
        # Kyo's 32:9 patches keep 1080 high and 3840/5120 wide against it (a squeezed HUD).
        image = apply(ultrawide_writes(XML, (5120, 1440), '01.09', SEGMENTS))
        width, = struct.unpack('<f', value(image, HUD_PROJECTION_WIDTH))
        self.assertEqual(width, 3840.0)
        aspect, = struct.unpack('<f', value(image, CAMERA_ASPECT))
        self.assertAlmostEqual(aspect, 32 / 9, places=5)

    def test_aspect_patch_off_keeps_the_16_9_ui(self):
        self.assertEqual(ui_size({}, (3440, 1440)), (2580, 1080))
        self.assertEqual(ui_size({'aspect_patch': '0'}, (3440, 1440)), OUTPUT_SIZE)

    def test_scene_of_the_canvas_size_is_drawn_smaller(self):
        # Native AA at 2560x1080: a scene the size of the HUD canvas would be taken for UI draws.
        self.assertEqual(scaled_sizes({'output_res': '2560x1080', 'preset': '0'}),
                         ((2556, 1078), (2560, 1080)))
        self.assertEqual(scaled_sizes({'output_res': '2560x1080', 'preset': '0', 'aspect_patch': '0'}),
                         ((2560, 1080), (2560, 1080)))


class HudLayoutTests(unittest.TestCase):
    def test_position_from_the_settings(self):
        with tempfile.TemporaryDirectory() as folder:
            ini = Path(folder) / 'bbport.ini'
            self.assertEqual(hud_layout.hud_position(ini), 1.0)  # no file: the screen edges
            ini.write_text('output_res=3440x1440\nhud_position=25\n')
            self.assertEqual(hud_layout.hud_position(ini), 0.25)
            ini.write_text('hud_position=250\n')
            self.assertEqual(hud_layout.hud_position(ini), 1.0)

    def test_layer_builds_on_the_prompts_layer(self):
        # A menu movie from an earlier layer (menu_prompts.py's gestures menu) replaces the game's.
        backdrop = movie(solid_shape(1, 0, 1920), place(1, 1))
        with tempfile.TemporaryDirectory() as folder:
            game, prompts, out = (Path(folder) / name for name in ('game', 'prompts', 'out'))
            for root, data in ((game, movie(solid_shape(1, 0, 600), place(1, 1))), (prompts, backdrop)):
                (root / 'dvdroot_ps4' / 'menu').mkdir(parents=True)
                (root / 'dvdroot_ps4' / 'menu' / 'gesturetop.gfx').write_bytes(data)
            self.assertEqual(hud_layout.write_layer(game, out, 2580, 330, [prompts]), 1)
            self.assertEqual((out / 'dvdroot_ps4' / 'menu' / 'gesturetop.gfx').read_bytes(),
                             hud_layout.layout(backdrop, 2580))
            self.assertEqual(hud_layout.write_layer(game, out / 'alone', 2580, 330), 0)
    def test_matrix_round_trip(self):
        for matrix in [(None, None, (0, 0)), (None, None, (-6600, 2988)),
                       ((65536, 65536), None, (3704, 2988)), ((-65536, 65536), (12, -7), (1, -1))]:
            data = hud_layout.write_matrix(matrix)
            self.assertEqual(hud_layout.read_matrix(data, 0)[0], matrix)

    def test_moves_named_placements(self):
        # A movie with PlayerHUD (sprite 2, holding Soul) and AutoSaveIcon on the root timeline.
        def place(depth, character, x, name):
            body = bytes([0x26]) + struct.pack('<HH', depth, character)
            body += hud_layout.write_matrix((None, None, (x * 20, 0))) + name.encode() + b'\0'
            return hud_layout.tag(26, body)
        sprite = hud_layout.tag(39, struct.pack('<HH', 2, 1) + place(1, 1, 1357, 'Soul') +
                                hud_layout.tag(1, b'') + hud_layout.tag(0, b''))
        rect = hud_layout.Writer()
        rect.unsigned(16, 5)
        for v in (0, 1920 * 20, 0, 1080 * 20):
            rect.unsigned(v, 16)
        body = rect.bytes() + b'\0\x1e\1\0' + sprite + place(1, 2, 185, 'PlayerHUD') + \
            place(2, 3, 1767, 'AutoSaveIcon') + hud_layout.tag(1, b'') + hud_layout.tag(0, b'')
        movie = b'GFX\x0b' + struct.pack('<I', 8 + len(body)) + body
        out = hud_layout.layout(movie, 2580, 330)
        self.assertEqual(struct.unpack_from('<I', out, 4)[0], len(out))
        start = hud_layout.stage_start(out)
        found = {}
        for code, _, b, length in hud_layout.tags(out, start, len(out)):
            if code == 26:
                _, span, name = hud_layout.place_fields(out, b, code)
                found[name] = hud_layout.read_matrix(out, span[0])[0][2][0] / 20
            if code == 39:
                for c2, _, b2, _ in hud_layout.tags(out, b + 4, b + length):
                    if c2 == 26:
                        _, span, name = hud_layout.place_fields(out, b2, c2)
                        found[name] = hud_layout.read_matrix(out, span[0])[0][2][0] / 20
        self.assertEqual(found, {'Soul': 1357 + 660, 'PlayerHUD': 185 - 330, 'AutoSaveIcon': 1767 + 330})


def movie(*root_tags):
    rect = hud_layout.Writer()
    rect.unsigned(16, 5)
    for v in (0, 1920 * 20, 0, 1080 * 20):
        rect.unsigned(v, 16)
    body = rect.bytes() + b'\x00\x1e\x01\x00' + b''.join(root_tags) + hud_layout.tag(1, b'') + hud_layout.tag(0, b'')
    return b'GFX\x0b' + struct.pack('<I', 8 + len(body)) + body


def solid_shape(shape, x0, x1):
    bounds = hud_layout.Writer()
    bounds.unsigned(17, 5)
    for v in (x0 * 20, x1 * 20, 0, 1080 * 20):
        bounds.unsigned(v & 0x1FFFF, 17)
    # One solid black fill, no line styles, no records.
    return hud_layout.tag(2, struct.pack('<H', shape) + bounds.bytes() + b'\x01\x00\x00\x00\x00\x00\x00')


def place(depth, character, x=0, y=0, name=None):
    flags = 0x06 | (0x20 if name else 0)
    body = bytes([flags]) + struct.pack('<HH', depth, character)
    body += hud_layout.write_matrix((None, None, (round(x * 20), round(y * 20))))
    return hud_layout.tag(26, body + (name.encode() + b'\x00' if name else b''))


def root_x(data, name_or_depth):
    found = {}
    for code, _, body, _ in hud_layout.tags(data, hud_layout.stage_start(data), len(data)):
        if code == 26:
            character, span, name = hud_layout.place_fields(data, body, code)
            depth, = struct.unpack_from('<H', data, body + 1)
            found[name or depth] = hud_layout.read_matrix(data, span[0])[0]
    return found[name_or_depth]


class BackdropTests(unittest.TestCase):
    def test_full_screen_backdrop_is_widened_around_the_centre(self):
        data = movie(solid_shape(1, 0, 1920), solid_shape(2, 0, 600), place(1, 1), place(2, 2))
        out = hud_layout.layout(data, 2580)
        scale, _, (tx, _) = root_x(out, 1)
        factor = 2580 / 1920 * 1.01
        self.assertAlmostEqual(scale[0] / 65536, factor, places=3)
        self.assertAlmostEqual(tx / 20 + 960 * factor, 960, delta=1)  # centred
        self.assertEqual(root_x(out, 2), root_x(data, 2))  # a small shape stays

    def test_nothing_to_widen(self):
        self.assertIsNone(hud_layout.layout(movie(solid_shape(1, 0, 600), place(1, 1)), 2580))


if __name__ == '__main__':
    unittest.main()
