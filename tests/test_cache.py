from paths import ROOT
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(ROOT / 'launcher'))
import bbport_cache  # noqa: E402


class ShaderCacheTests(unittest.TestCase):
    def test_size_and_clear_keep_the_saves(self):
        with tempfile.TemporaryDirectory() as tmp:
            user = Path(tmp)
            self.assertEqual(bbport_cache.size(user), 0)
            game = user / 'cache' / 'CUSA00900'
            game.mkdir(parents=True)
            (game / 'a.spv').write_bytes(b'x' * 100)
            (user / 'cache' / 'CUSA03173.zip').write_bytes(b'y' * 50)
            saves = user / 'savedata' / '1'
            saves.mkdir(parents=True)
            (saves / 'userdata0000').write_bytes(b'z' * 10)
            self.assertEqual(bbport_cache.size(user), 150)
            self.assertEqual(bbport_cache.clear(user), 150)
            self.assertEqual(bbport_cache.size(user), 0)
            self.assertTrue((user / 'cache').is_dir())
            self.assertTrue((saves / 'userdata0000').is_file())

    def test_symlinks_are_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            user, outside = Path(tmp) / 'user', Path(tmp) / 'outside'
            (user / 'cache').mkdir(parents=True)
            outside.mkdir()
            (outside / 'keep').write_bytes(b'k')
            (user / 'cache' / 'link').symlink_to(outside)
            bbport_cache.clear(user)
            self.assertTrue((outside / 'keep').is_file())


if __name__ == '__main__':
    unittest.main()
