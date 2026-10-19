from paths import ROOT
import io
import json
import os
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(ROOT / 'launcher'))
import bbport_atlas_maps as maps


def make_maps(folder, language='spaes'):
    (folder / 'maps').mkdir(parents=True)
    (folder / 'art').mkdir()
    (folder / 'maps' / 'atlas.json').write_text('{}')
    (folder / 'art' / 'icons.bbra').write_bytes(b'BBRA')
    (folder / 'bbport.json').write_text(json.dumps({'language': language}))


class StateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.data = Path(temp.name)

    def test_language_folders(self):
        self.assertEqual(maps.language_folder(3), 'spaes')
        self.assertEqual(maps.language_folder('8'), 'rusru')
        self.assertEqual(maps.language_folder(''), 'engus')
        self.assertEqual(maps.language_folder(99), 'engus')

    def test_no_maps(self):
        self.assertFalse(maps.maps_state(self.data)['ready'])

    def test_ready_maps_and_their_language(self):
        make_maps(self.data / maps.MAPS)
        state = maps.maps_state(self.data)
        self.assertTrue(state['ready'])
        self.assertEqual(state['language'], 'spaes')
        self.assertGreater(state['bytes'], 0)

    def test_hard_links_count_once(self):
        tools = self.data / maps.TOOLS
        (tools / 'cache').mkdir(parents=True)
        (tools / 'venv').mkdir()
        (tools / 'cache' / 'numpy.so').write_bytes(b'x' * 1000)
        os.link(tools / 'cache' / 'numpy.so', tools / 'venv' / 'numpy.so')
        self.assertEqual(maps.folder_bytes(tools), 1000)

    def test_language_of_maps_made_by_hand(self):
        folder = self.data / maps.MAPS
        make_maps(folder)
        (folder / 'bbport.json').unlink()
        (folder / 'maps' / 'generated-assets.json').write_text(json.dumps({'language': 'frafr'}))
        self.assertEqual(maps.maps_state(self.data)['language'], 'frafr')
        (folder / 'maps' / 'generated-assets.json').write_text(json.dumps({'schema': 1}))
        self.assertEqual(maps.maps_state(self.data)['language'], 'engus')

    def test_delete_removes_maps_tools_and_leftovers(self):
        for name in (maps.MAPS, maps.NEW, maps.OLD, maps.STAGING, maps.TOOLS):
            (self.data / name).mkdir()
        (self.data / 'bbport.ini').write_text('keep')
        maps.delete(self.data)
        self.assertEqual(sorted(p.name for p in self.data.iterdir()), ['bbport.ini'])

    def test_children_do_not_get_the_package_s_python_or_libraries(self):
        with mock.patch.dict(os.environ, {'PYTHONHOME': '/appimage', 'LD_PRELOAD': 'x.so',
                                          'LD_LIBRARY_PATH': '/appimage/lib', 'UV_INDEX_URL': 'evil',
                                          'HOME': '/home/hunter'}):
            env = maps.child_environment(Path('/data/atlas-tools'))
        self.assertNotIn('PYTHONHOME', env)
        self.assertNotIn('LD_PRELOAD', env)
        self.assertNotIn('LD_LIBRARY_PATH', env)
        self.assertNotIn('UV_INDEX_URL', env)
        self.assertEqual(env['HOME'], '/home/hunter')
        self.assertEqual(env['UV_PYTHON_PREFERENCE'], 'only-managed')
        self.assertEqual(env['UV_CACHE_DIR'], '/data/atlas-tools/cache')


class PreparationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.data = self.root / 'data'
        self.game = self.root / 'game'
        self.game.mkdir()
        (self.game / 'eboot.bin').write_bytes(b'x')
        self.prep = maps.Preparation(self.data, self.game, 3)

    def test_install_swaps_in_the_new_maps_and_keeps_the_map_settings(self):
        make_maps(self.data / maps.MAPS, 'engus')
        (self.data / maps.MAPS / 'settings.ini').write_text('keyboard=2\n')
        make_maps(self.data / maps.NEW)
        self.prep.install('spaes')
        self.assertFalse((self.data / maps.NEW).exists())
        self.assertFalse((self.data / maps.OLD).exists())
        self.assertEqual((self.data / maps.MAPS / 'settings.ini').read_text(), 'keyboard=2\n')
        self.assertEqual(maps.maps_state(self.data)['language'], 'spaes')

    def test_a_failure_keeps_the_previous_maps(self):
        make_maps(self.data / maps.MAPS, 'engus')

        def broken():
            make_maps(self.data / maps.NEW)
            raise maps.Failure('maps', 'generator failed')
        with mock.patch.object(self.prep, 'install_tools'), mock.patch.object(self.prep, 'generate', broken):
            with self.assertRaises(maps.Failure):
                self.prep.prepare()
        self.assertFalse((self.data / maps.NEW).exists())
        self.assertEqual(maps.maps_state(self.data)['language'], 'engus')

    def test_cancelling_keeps_the_previous_maps(self):
        make_maps(self.data / maps.MAPS, 'engus')

        def cancelled():
            make_maps(self.data / maps.NEW)
            raise KeyboardInterrupt
        with mock.patch.object(self.prep, 'install_tools'), mock.patch.object(self.prep, 'generate', cancelled):
            with self.assertRaises(KeyboardInterrupt):
                self.prep.prepare()
        self.assertFalse((self.data / maps.NEW).exists())
        self.assertTrue(maps.maps_state(self.data)['ready'])

    def test_needs_the_game_folder(self):
        (self.game / 'eboot.bin').unlink()
        with self.assertRaises(maps.Failure) as caught:
            self.prep.prepare()
        self.assertEqual(caught.exception.stage, 'game')

    def test_needs_free_space(self):
        with mock.patch('shutil.disk_usage', return_value=mock.Mock(free=10 << 20)):
            with self.assertRaises(maps.Failure) as caught:
                self.prep.prepare()
        self.assertEqual(caught.exception.stage, 'space')

    def test_tools_are_reused_only_when_they_match(self):
        tools = self.data / maps.TOOLS
        (tools / 'bin').mkdir(parents=True)
        (tools / 'venv' / 'bin').mkdir(parents=True)
        self.prep.uv().write_text('')
        self.prep.python().write_text('')
        (tools / 'ready.json').write_text(json.dumps(self.prep.marker()))
        self.assertTrue(self.prep.tools_ready())
        (tools / 'ready.json').write_text(json.dumps(dict(self.prep.marker(), python='3.12.0')))
        self.assertFalse(self.prep.tools_ready())

    def test_a_download_that_does_not_match_its_hash_is_refused(self):
        payload = io.BytesIO()
        with tarfile.open(fileobj=payload, mode='w:gz') as archive:
            body = b'#!/bin/sh\n'
            info = tarfile.TarInfo('uv-x86_64-unknown-linux-musl/uv')
            info.size = len(body)
            archive.addfile(info, io.BytesIO(body))
        reply = mock.MagicMock()
        reply.__enter__.return_value = io.BytesIO(payload.getvalue())
        reply.__enter__.return_value.headers = {}
        self.data.mkdir()
        with mock.patch('urllib.request.urlopen', return_value=reply):
            with self.assertRaises(maps.Failure) as caught:
                self.prep.fetch_uv()
        self.assertEqual(caught.exception.stage, 'uv')
        self.assertFalse(self.prep.uv().exists())

    def test_the_shipped_art_and_lock_are_the_expected_ones(self):
        import hashlib
        for name, digest in maps.ART.items():
            self.assertEqual(hashlib.sha256((maps.TOOLS_DIR / 'art' / name).read_bytes()).hexdigest(), digest)
        lock = (maps.TOOLS_DIR / 'requirements.lock').read_text()
        self.assertIn('soulstruct==2.3.2', lock)
        self.assertIn('--hash=sha256:', lock)


if __name__ == '__main__':
    unittest.main()
