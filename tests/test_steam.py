from paths import ROOT
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(ROOT / 'launcher'))
import bbport_steam as steam


class FlatpakSteamTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)

    def test_finds_flathubs_steam_after_the_native_one(self):
        flatpak = steam.flatpak_data(self.home)
        (flatpak / 'userdata/123/config').mkdir(parents=True)
        self.assertEqual(steam.steam_folder(self.home), flatpak.resolve())
        self.assertTrue(steam.is_flatpak(flatpak))
        native = self.home / '.local/share/Steam'
        (native / 'userdata/123/config').mkdir(parents=True)
        self.assertEqual(steam.steam_folder(self.home), native.resolve())
        self.assertFalse(steam.is_flatpak(native))

    def test_flatpak_shortcut_runs_on_the_host(self):
        flatpak = steam.flatpak_data(self.home)
        exe, start, options = steam.shortcut_command('/apps/Bloodborne.AppImage', '/apps', '--play', flatpak)
        self.assertEqual(exe, steam.SPAWN)
        self.assertEqual(options, '--host --directory="/apps" "/apps/Bloodborne.AppImage" --play')
        self.assertEqual(steam.shortcut_command('/x/bb', '/x', '--play', self.home / 'Steam'),
                         ('/x/bb', '/x', '--play'))

    def test_other_launchers_flatpak_spawn_shortcuts_are_kept(self):
        vdf = self.home / 'shortcuts.vdf'
        steam.add_shortcut(vdf, 'Hades', steam.SPAWN, '/', '', '--host heroic --launch hades')
        steam.add_shortcut(vdf, 'Bloodborne', steam.SPAWN, '/', '', '--host "/a/bb.AppImage" --play')
        steam.add_shortcut(vdf, 'Bloodborne', steam.SPAWN, '/', '', '--host "/b/bb.AppImage" --play')
        entries = steam.parse(vdf.read_bytes())[0][0][2]
        fields = [{k: v for _t, k, v in e[2]} for e in entries]
        self.assertEqual([f['AppName'] for f in fields], ['Hades', 'Bloodborne'])
        self.assertEqual(fields[1]['LaunchOptions'], '--host "/b/bb.AppImage" --play')

    def test_spawn_permission_is_read_from_flatpak_info(self):
        def run(output):
            return lambda *_a, **_k: SimpleNamespace(stdout=output)
        allowed = '[Session Bus Policy]\norg.freedesktop.Flatpak=talk\n'
        self.assertTrue(steam.flatpak_can_spawn(run(allowed)))
        self.assertFalse(steam.flatpak_can_spawn(run('[Context]\nshared=network;\n')))


if __name__ == '__main__':
    unittest.main()
