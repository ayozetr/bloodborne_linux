from paths import ROOT
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

import save_import
from test_game_check import param_sfo


def save_folder(path, marker, files=('userdata0000', 'userdata0001', 'userdata0010', 'backup0000')):
    path.mkdir(parents=True)
    for name in files:
        (path / name).write_bytes(marker + name.encode())
    return path


class SaveImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.user = self.root / 'user'
        self.game = self.root / 'CUSA03173'
        (self.game / 'sce_sys').mkdir(parents=True)
        (self.game / 'sce_sys/param.sfo').write_bytes(
            param_sfo({'TITLE_ID': 'CUSA03173', 'INSTALL_DIR_SAVEDATA': 'CUSA00207'}))

    def tearDown(self):
        self.tmp.cleanup()

    def test_save_id_from_the_game_or_the_saves_there(self):
        self.assertEqual(save_import.save_id(self.user, self.game), 'CUSA00207')
        (self.game / 'sce_sys/param.sfo').write_bytes(param_sfo({'TITLE_ID': 'CUSA00900'}))
        self.assertEqual(save_import.save_id(self.user, self.game), 'CUSA00900')
        with self.assertRaises(save_import.SaveImportError):
            save_import.save_id(self.user, None)
        save_folder(self.user / 'savedata/1/CUSA01363/SPRJ0005', b'x')
        self.assertEqual(save_import.save_id(self.user, None), 'CUSA01363')

    def test_finds_shadps4_and_exported_saves_newest_first(self):
        shad = self.root / 'shadPS4'
        old = save_folder(shad / 'savedata/1/CUSA00900/SPRJ0005', b'old')
        (old / 'sce_sys').mkdir()
        new = save_folder(self.root / 'usb/PS4/APOLLO/CUSA00207_SPRJ0005', b'new')
        # Game files and a lone userdata file elsewhere are no save folder.
        (shad / 'games/CUSA00900/dvdroot_ps4/SPRJ0005').mkdir(parents=True)
        (shad / 'games/CUSA00900/dvdroot_ps4/SPRJ0005/userdata0000').write_bytes(b'')
        (self.root / 'notes').mkdir()
        (self.root / 'notes/userdata0000').write_bytes(b'')
        for folder, when in ((old, 1000), (new, 2000)):
            for path in save_import.save_files(folder):
                os.utime(path, (when, when))
        found = [folder for folder, _ in save_import.find(self.root)]
        self.assertEqual(found, [new, old])
        self.assertEqual(save_import.find(old), [(old, 1000)])

    def test_encrypted_console_copy(self):
        (self.root / 'PS4/SAVEDATA/abc/CUSA00900').mkdir(parents=True)
        (self.root / 'PS4/SAVEDATA/abc/CUSA00900/sdimg_SPRJ0005').write_bytes(b'')
        self.assertEqual(save_import.find(self.root), [])
        self.assertTrue(save_import.encrypted_ps4_save(self.root))
        self.assertFalse(save_import.encrypted_ps4_save(self.game))

    def test_import_backs_up_and_replaces_the_save_files_only(self):
        target = save_folder(self.user / 'savedata/1/CUSA00207/SPRJ0005', b'mine',
                             ('userdata0000', 'userdata0005', 'userdata0010'))
        meta = self.user / 'savedata/1/CUSA00207/SPRJ0005.sce_sys'
        meta.mkdir()
        (meta / 'param.bin').write_bytes(b'param')
        source = save_folder(self.root / 'shadPS4/savedata/1/CUSA00900/SPRJ0005', b'theirs')
        (source / 'sce_sys').mkdir()
        (source / 'sce_sys/param.sfo').write_bytes(b'sfo')
        result, backup = save_import.import_saves(source, self.user, self.game,
                                                  now=datetime(2026, 10, 15, 12, 0, 0))
        self.assertEqual(result, target)
        self.assertEqual(sorted(p.name for p in target.iterdir()),
                         ['backup0000', 'userdata0000', 'userdata0001', 'userdata0010'])
        self.assertEqual((target / 'userdata0000').read_bytes(), b'theirsuserdata0000')
        self.assertEqual((meta / 'param.bin').read_bytes(), b'param')
        self.assertEqual(backup, self.user / 'savedata-backups/2026-10-15_120000')
        kept = backup / 'CUSA00207/SPRJ0005'
        self.assertEqual((kept / 'userdata0005').read_bytes(), b'mineuserdata0005')
        self.assertEqual((backup / 'CUSA00207/SPRJ0005.sce_sys/param.bin').read_bytes(), b'param')
        self.assertFalse(any(p.name.endswith(('.importing', '.old')) for p in target.parent.iterdir()))

    def test_first_import_without_saves(self):
        source = save_folder(self.root / 'export/SPRJ0005', b'theirs')
        target, backup = save_import.import_saves(source, self.user, self.game)
        self.assertIsNone(backup)
        self.assertEqual(target, self.user / 'savedata/1/CUSA00207/SPRJ0005')
        self.assertTrue((target.parent / 'SPRJ0005.sce_sys').is_dir())

    def test_refusals(self):
        with self.assertRaises(save_import.SaveImportError):
            save_import.import_saves(self.root, self.user, self.game)
        target = save_folder(self.user / 'savedata/1/CUSA00207/SPRJ0005', b'mine')
        with self.assertRaises(save_import.SaveImportError):
            save_import.import_saves(target, self.user, self.game)

    def test_failed_copy_keeps_the_saves(self):
        target = save_folder(self.user / 'savedata/1/CUSA00207/SPRJ0005', b'mine')
        source = save_folder(self.root / 'export/SPRJ0005', b'theirs')
        with mock.patch.object(save_import.shutil, 'copy2', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                save_import.import_saves(source, self.user, self.game)
        self.assertEqual((target / 'userdata0000').read_bytes(), b'mineuserdata0000')
        self.assertFalse((target.parent / 'SPRJ0005.importing').exists())


if __name__ == '__main__':
    unittest.main()
