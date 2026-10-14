from paths import ROOT
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pkg_install
from test_game_check import param_sfo

# A stand-in for pkgextract: a "package" is the PKG header (magic, content ID) and, after it, a
# JSON list of its files; it refuses an output folder that exists, as pkgextract without -f does.
FAKE_EXTRACTOR = '''import json, sys
from pathlib import Path
args = sys.argv[1:]
out, pkg = Path(args[args.index('-o') + 1]), Path(args[-1])
if out.exists():
    sys.exit('output directory already exists')
for name, data in json.loads(pkg.read_bytes()[0x80:]).items():
    (out / name).parent.mkdir(parents=True, exist_ok=True)
    (out / name).write_bytes(bytes.fromhex(data))
'''


def package(path, content_id, category, version, files):
    header = bytearray(0x80)
    header[:4] = b'\x7fCNT'
    header[0x40:0x40 + len(content_id)] = content_id.encode()
    files = {'sce_sys/param.sfo': param_sfo({'CATEGORY': category, 'APP_VER': version,
                                             'TITLE_ID': content_id[7:16]}), **files}
    path.write_bytes(bytes(header) + json.dumps({k: v.hex() for k, v in files.items()}).encode())
    return path


class PkgInstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.extractor = self.root / 'pkgextract'
        self.extractor.write_text(f'#!{sys.executable}\n' + FAKE_EXTRACTOR)
        self.extractor.chmod(0o755)
        self.dest = self.root / 'games'
        self.lines = []
        checked = mock.patch.object(pkg_install, 'problem', return_value=None)
        checked.start()
        self.addCleanup(checked.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def install(self, *pkgs):
        return pkg_install.install(pkgs, self.dest, str(self.extractor), self.lines.append)

    def test_game_updates_oldest_first_and_add_ons_apart(self):
        game = package(self.root / 'a.pkg', 'UP9000-CUSA00900_00-BLOODBORNE000000', 'gd', '01.00',
                       {'eboot.bin': b'1.00', 'dvdroot_ps4/kept.bin': b'base'})
        late = package(self.root / 'b.pkg', 'UP9000-CUSA00900_00-BLOODBORNE000000', 'gp', '01.09',
                       {'eboot.bin': b'1.09'})
        early = package(self.root / 'c.pkg', 'UP9000-CUSA00900_00-BLOODBORNE000000', 'gp', '01.05',
                        {'eboot.bin': b'1.05', 'dvdroot_ps4/new.bin': b'1.05'})
        dlc = package(self.root / 'd.pkg', 'UP9000-CUSA00900_00-SPEXPANSIONDLC03', 'ac', '01.00', {})
        game_dir, dlc_dir = self.install(late, dlc, game, early)
        self.assertEqual(game_dir, self.dest.resolve() / 'CUSA00900')
        self.assertEqual((game_dir / 'eboot.bin').read_bytes(), b'1.09')
        self.assertEqual((game_dir / 'dvdroot_ps4/kept.bin').read_bytes(), b'base')
        self.assertEqual((game_dir / 'dvdroot_ps4/new.bin').read_bytes(), b'1.05')
        self.assertEqual(dlc_dir, self.dest.resolve() / 'DLC')
        self.assertTrue((dlc_dir / 'SPEXPANSIONDLC03/sce_sys/param.sfo').is_file())
        self.assertEqual(sorted(p.name for p in self.dest.iterdir()), ['CUSA00900', 'DLC'])
        self.assertIn('Install: the game is ready (Bloodborne 1.09)', self.lines)

    def test_an_existing_game_folder_is_never_replaced(self):
        game = package(self.root / 'a.pkg', 'EP9000-CUSA03173_00-BLOODBORNE0000EU', 'gd', '01.09',
                       {'eboot.bin': b'new'})
        (self.dest / 'CUSA03173').mkdir(parents=True)
        (self.dest / 'CUSA03173/eboot.bin').write_bytes(b'mine')
        with self.assertRaisesRegex(pkg_install.InstallError, 'already exists'):
            self.install(game)
        self.assertEqual((self.dest / 'CUSA03173/eboot.bin').read_bytes(), b'mine')
        self.assertEqual([p.name for p in self.dest.iterdir()], ['CUSA03173'])

    def test_not_a_package_or_two_titles_or_no_game(self):
        other = self.root / 'notes.pkg'
        other.write_bytes(b'not a package' * 20)
        with self.assertRaisesRegex(pkg_install.InstallError, 'not a PS4 package'):
            self.install(other)
        us = package(self.root / 'a.pkg', 'UP9000-CUSA00900_00-BLOODBORNE000000', 'gd', '01.09', {})
        eu = package(self.root / 'b.pkg', 'EP9000-CUSA03173_00-BLOODBORNE0000EU', 'gp', '01.09', {})
        with self.assertRaisesRegex(pkg_install.InstallError, 'different titles'):
            self.install(us, eu)
        update = package(self.root / 'c.pkg', 'UP9000-CUSA00900_00-BLOODBORNE000000', 'gp', '01.09', {})
        with self.assertRaisesRegex(pkg_install.InstallError, '0 game packages'):
            self.install(update)
        self.assertFalse((self.dest / 'CUSA00900').exists())
        self.assertEqual([p.name for p in self.dest.iterdir()], [])   # no work folder left


if __name__ == '__main__':
    unittest.main()
