from paths import ROOT
import contextlib
import io
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock

import patches
import quit_menu as qm

XML = ROOT / 'patches/Bloodborne.xml'


def original_image():
    """image_bytes(start, end) of an eboot holding the 01.09 bytes Quit to Desktop checks."""
    image = {}
    for offset, expected in qm.ORIGINAL.items():
        for i, byte in enumerate(bytes.fromhex(expected.replace(' ', ''))):
            image[offset + i] = byte
    return lambda start, end: bytes(image.get(i, 0) for i in range(start, end))


def elf(vaddr, data, memsz):
    """A minimal ELF64 with one PT_LOAD of `data` at `vaddr`."""
    header = bytearray(0x40)
    header[:4] = b'\x7fELF'
    struct.pack_into('<Q', header, 0x20, 0x40)
    struct.pack_into('<HH', header, 0x36, 56, 1)
    ph = struct.pack('<IIQQQQQQ', 1, 5, 0x40 + 56, vaddr, vaddr, len(data), memsz, 0x1000)
    return bytes(header) + ph + data


def fmg(strings):
    template = bytearray(0x28)
    template[0x08] = 1  # header flags, kept by write_fmg
    return qm.write_fmg(bytes(template), strings)


def menu_archive(files):
    """menu.msgbnd.dcx: a DFLT DCX holding a BND4 of {id: bytes}."""
    count = len(files)
    bnd = bytearray(0x40 + 0x24 * count)
    bnd[:4] = b'BND4'
    struct.pack_into('<I', bnd, 0x0C, count)
    struct.pack_into('<Q', bnd, 0x20, 0x24)
    for i, (file_id, body) in enumerate(sorted(files.items())):
        bnd += b'\0' * (-len(bnd) % 16)
        struct.pack_into('<QQII', bnd, 0x40 + i * 0x24 + 0x08, len(body), len(body), len(bnd), file_id)
        bnd += body
    header = bytearray(0x4C)
    header[:4] = b'DCX\0'
    header[0x28:0x2C] = b'DFLT'
    return qm.pack_dcx(bytes(header), bytes(bnd))


def strings_of(archive):
    bnd = qm.unpack_dcx(archive)
    return {file_id: qm.read_fmg(bnd[offset:offset + length])
            for _, offset, length, file_id in qm.bnd4_files(bnd)}


# 110005: the System menu's Language entry, kept (Quit to Desktop's is a new id).
GAME_TEXTS = {200: {qm.TITLE_ID: 'Opinion Box', 110005: 'Language', 1: 'Exit Game'},
              201: {qm.TITLE_ID: 'Send an opinion', 110005: 'Change the language', 2: None},
              204: {qm.DIALOG_ID: 'Change the language?', 110000: 'Exit the game?'},
              300: {5: 'untouched'}}


class CodeTests(unittest.TestCase):
    def test_writes_fit_and_do_not_overlap(self):
        writes = qm.code_writes()
        spans = sorted((offset, offset + len(data)) for offset, data in writes)
        for (_, end), (start, _) in zip(spans, spans[1:]):
            self.assertLessEqual(end, start)
        cave = dict(writes)[qm.CAVE]
        # Past the end of the code segment, within its last page.
        self.assertGreaterEqual(qm.CAVE, qm.CODE_END)
        self.assertLessEqual(qm.CAVE + len(cave), qm.CAVE_END)
        self.assertTrue(cave.endswith(b'bb:t\0bb:q\0bb:p\0bb:d\0'))
        # The Language item: a jump into the new code, then nops up to the game's own text
        # lookup; the game's condition code (the item kept or removed) is left as it is.
        item = dict(writes)[qm.SYSTEM_ITEM]
        self.assertEqual(len(item), qm.SYSTEM_TEXT - qm.SYSTEM_ITEM)
        self.assertEqual(item[0], 0xE9)
        target = qm.SYSTEM_ITEM + 5 + struct.unpack_from('<i', item, 1)[0]
        self.assertTrue(qm.CAVE <= target < qm.CAVE + len(cave))
        self.assertEqual(item[5:], b'\x90' * (len(item) - 5))
        self.assertNotIn(qm.SYSTEM_KEEP, dict(writes))

    def test_title_entry_slot_points_into_the_code(self):
        writes = dict(qm.code_writes())
        slot, = struct.unpack('<Q', writes[qm.OPINION_SLOT])
        self.assertTrue(qm.CAVE <= slot - qm.EBOOT_BASE < qm.CAVE + len(writes[qm.CAVE]))

    def test_segment_layout(self):
        qm.check_segments([(0, qm.CODE_END), (0x50DC000, 0x56D30F4)])
        with self.assertRaises(ValueError):  # the code segment ends elsewhere
            qm.check_segments([(0, qm.CODE_END + 4), (0x50DC000, 0x56D30F4)])
        with self.assertRaises(ValueError):  # another segment starts in the cave's page
            qm.check_segments([(0, qm.CODE_END), (0x50D9800, 0x56D30F4)])

    def test_calls_reach_their_targets(self):
        title = dict(qm.code_writes())[qm.TITLE_CONDITION]
        self.assertEqual(title[0], 0xE8)
        target = qm.TITLE_CONDITION + 5 + struct.unpack('<i', title[1:5])[0]
        self.assertEqual(target, qm.CAVE)  # the first routine in the cave

    def test_no_overlap_with_the_built_in_patches(self):
        import xml.etree.ElementTree as ET
        writes = qm.code_writes()
        for meta in ET.parse(XML).getroot().iter('Metadata'):
            for line in meta.iter('Line'):
                offset = int(line.get('Address'), 0) - patches.EBOOT_BASE
                size = len(patches.encode(line))
                for at, data in writes:
                    self.assertFalse(offset < at + len(data) and at < offset + size, meta.get('Name'))

    def test_original_bytes_are_checked(self):
        qm.check_original(original_image())
        image = original_image()
        changed = lambda start, end: bytes(b ^ 0xFF if start + i == qm.EXIT_DIALOG else b
                                           for i, b in enumerate(image(start, end)))
        with self.assertRaisesRegex(ValueError, hex(qm.EXIT_DIALOG + qm.EBOOT_BASE)):
            qm.check_original(changed)


class PatchesTests(unittest.TestCase):
    def test_eboot_bytes_are_the_memory_image(self):
        image = elf(0x1000, b'abcd', 0x10)
        self.assertEqual(patches.eboot_bytes(image, 0xFFE, 0x1006), b'\0\0abcd\0\0')

    def test_other_code_skips_it(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(patches.quit_to_desktop_writes(elf(0, b'\0' * 64, 64)), [])
        self.assertIn('Quit to Desktop skipped', out.getvalue())

    def test_another_patch_of_the_same_code_wins(self):
        with mock.patch.object(qm, 'check_original'), mock.patch.object(qm, 'check_segments'), \
                mock.patch.object(patches, 'eboot_segments'):
            self.assertEqual(patches.quit_to_desktop_writes(b'', [(0x100, b'\x90')]), qm.code_writes())
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(patches.quit_to_desktop_writes(b'', [(qm.TITLE_CONDITION + 2, b'\x90')]), [])
        self.assertIn('another patch writes', out.getvalue())


class TextTests(unittest.TestCase):
    def test_fmg_round_trip(self):
        strings = {1: 'a', 2: None, 3: 'ç', 10: 'x'}
        self.assertEqual(qm.read_fmg(fmg(strings)), strings)

    def test_menu_texts(self):
        archive = menu_archive({k: fmg(v) for k, v in GAME_TEXTS.items()})
        result = strings_of(qm.menu_texts(archive, qm.TEXTS['spaes']))
        name, title_help, system_help, question = qm.TEXTS['spaes']
        self.assertEqual(result[200], {**GAME_TEXTS[200], qm.TITLE_ID: name, qm.SYSTEM_ID: name})
        self.assertEqual(result[201], {**GAME_TEXTS[201], qm.TITLE_ID: title_help,
                                       qm.SYSTEM_ID: system_help})
        self.assertEqual(result[204], {**GAME_TEXTS[204], qm.DIALOG_ID: question})
        self.assertEqual(result[300], GAME_TEXTS[300])
        self.assertEqual(name, 'Salir al escritorio')

    def test_every_text_is_complete(self):
        for folder, texts in qm.TEXTS.items():
            self.assertEqual(len(texts), 4, folder)
            self.assertTrue(all(texts), folder)


class LayerTests(unittest.TestCase):
    def run_main(self, *args):
        with mock.patch.object(sys, 'argv', ['quit_menu.py', *map(str, args)]), \
                contextlib.redirect_stdout(io.StringIO()) as out, \
                contextlib.redirect_stderr(io.StringIO()):
            qm.main()
        return out.getvalue().strip()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.game = self.root / 'game'
        archive = menu_archive({k: fmg(v) for k, v in GAME_TEXTS.items()})
        for folder in ('engus', 'spaes'):
            (self.game / 'dvdroot_ps4/msg' / folder).mkdir(parents=True)
            (self.game / 'dvdroot_ps4/msg' / folder / 'menu.msgbnd.dcx').write_bytes(archive)
        (self.game / 'dvdroot_ps4/menu').mkdir()
        self.out = self.root / 'out/quit-menu'
        self.config = self.root / 'bbport.ini'

    def tearDown(self):
        self.tmp.cleanup()

    def test_layer_made_once_and_turned_off(self):
        self.config.write_text('quit_to_desktop=1\n')
        self.assertEqual(self.run_main(self.game, '--out', self.out, '--config', self.config), str(self.out))
        spanish = self.out / 'dvdroot_ps4/msg/spaes/menu.msgbnd.dcx'
        self.assertEqual(strings_of(spanish.read_bytes())[200][qm.TITLE_ID], 'Salir al escritorio')
        made = spanish.stat().st_mtime_ns
        self.assertEqual(self.run_main(self.game, '--out', self.out), str(self.out))
        self.assertEqual(spanish.stat().st_mtime_ns, made)  # reused
        self.config.write_text('quit_to_desktop=0\n')
        self.assertEqual(self.run_main(self.game, '--out', self.out, '--config', self.config), '')
        self.assertFalse(self.out.exists())

    def test_game_without_menu_texts(self):
        game = self.root / 'empty'
        (game / 'dvdroot_ps4/msg').mkdir(parents=True)
        with self.assertRaises(ValueError):
            self.run_main(game, '--out', self.out)
        self.assertFalse(self.out.exists())


if __name__ == '__main__':
    unittest.main()
