from paths import ROOT
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(ROOT / 'launcher'))
import bbport_update  # noqa: E402


class VersionTests(unittest.TestCase):
    def test_keys(self):
        self.assertEqual(bbport_update.version_key('0.5-linux.1'), (0, 5, 0, 1))
        self.assertEqual(bbport_update.version_key('v0.5.2-linux.3'), (0, 5, 2, 3))
        self.assertIsNone(bbport_update.version_key('0.5-pre4'))

    def test_newer(self):
        self.assertTrue(bbport_update.is_newer('0.5-linux.2', '0.5-linux.1'))
        self.assertTrue(bbport_update.is_newer('0.6-linux.1', '0.5-linux.9'))
        self.assertTrue(bbport_update.is_newer('0.10-linux.1', '0.9-linux.1'))
        self.assertFalse(bbport_update.is_newer('0.5-linux.1', '0.5-linux.1'))
        self.assertFalse(bbport_update.is_newer('0.4-linux.1', '0.5-linux.1'))
        self.assertFalse(bbport_update.is_newer('nightly', '0.5-linux.1'))

    def test_the_version_follows_the_scheme(self):
        self.assertIsNotNone(bbport_update.version_key(bbport_update.VERSION))


class ReleaseTests(unittest.TestCase):
    def test_latest_release_and_its_appimage(self):
        with tempfile.TemporaryDirectory() as tmp:
            reply = Path(tmp) / 'latest.json'
            reply.write_text(json.dumps({
                'tag_name': '0.5-linux.2', 'html_url': 'https://example.invalid/r',
                'assets': [{'name': 'notes.txt', 'browser_download_url': 'x', 'size': 1},
                           {'name': 'Bloodborne-bbport-x86_64.AppImage',
                            'browser_download_url': 'https://example.invalid/a', 'size': 9}]}))
            latest = bbport_update.latest_release(reply.as_uri())
        self.assertEqual(latest, {'tag': '0.5-linux.2', 'url': 'https://example.invalid/r',
                                  'appimage': 'https://example.invalid/a', 'size': 9, 'date': ''})

    def test_releases_to_choose_from(self):
        # This fork's /releases reply of 2026-10-15, trimmed to the fields the launcher reads.
        found = bbport_update.releases((ROOT / 'tests/data/github_releases.json').as_uri())
        self.assertEqual([r['tag'] for r in found],
                         ['0.51-linux.6', '0.51-linux.5', '0.51-linux.4', '0.51-linux.3',
                          '0.51-linux.2', '0.51-linux.1', '0.5-linux.1'])
        self.assertEqual(found[0]['date'], '2026-10-14')
        self.assertTrue(found[0]['appimage'].endswith('/0.51-linux.6/Bloodborne-bbport-x86_64.AppImage'))
        self.assertEqual(found[0]['size'], 241642707)

    def test_install_replaces_the_file_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            new = Path(tmp) / 'download'
            new.write_bytes(b'new appimage' * 1000)
            target = Path(tmp) / 'Bloodborne.AppImage'
            target.write_bytes(b'old')
            seen = []
            bbport_update.install(new.as_uri(), target, lambda done, total: seen.append((done, total)),
                                  chunk=4096)
            self.assertEqual(target.read_bytes(), new.read_bytes())
            self.assertTrue(os.access(target, os.X_OK))
            self.assertEqual(seen[-1], (12000, 12000))
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()),
                             ['Bloodborne.AppImage', 'download'])

    def test_a_failed_download_keeps_the_old_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'Bloodborne.AppImage'
            target.write_bytes(b'old')
            with self.assertRaises(OSError):
                bbport_update.install((Path(tmp) / 'missing').as_uri(), target)
            self.assertEqual(target.read_bytes(), b'old')
            self.assertEqual([p.name for p in Path(tmp).iterdir()], ['Bloodborne.AppImage'])

    def test_running_appimage(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / 'Bloodborne.AppImage'
            image.write_bytes(b'')
            with mock.patch.dict(os.environ, {'APPIMAGE': str(image)}):
                self.assertEqual(bbport_update.running_appimage(), image)
            with mock.patch.dict(os.environ, {}, clear=True):
                self.assertIsNone(bbport_update.running_appimage())


if __name__ == '__main__':
    unittest.main()
