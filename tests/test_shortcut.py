# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-3.0-or-later
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "launcher"))
import bbport_shortcut  # noqa: E402


class ShortcutTest(unittest.TestCase):
    def test_exec_quotes_spaces_and_specials(self):
        self.assertEqual(bbport_shortcut.exec_quote("/a b/Bloodborne.AppImage"),
                         '"/a b/Bloodborne.AppImage"')
        self.assertEqual(bbport_shortcut.exec_quote('/x/"$`\\'), '"/x/\\"\\$\\`\\\\"')

    def test_entry_fields(self):
        text = bbport_shortcut.entry_text("/games/Bloodborne.AppImage", "/data/bloodborne.png")
        lines = text.splitlines()
        self.assertEqual(lines[0], "[Desktop Entry]")
        self.assertIn('Exec="/games/Bloodborne.AppImage"', lines)
        self.assertIn("Icon=/data/bloodborne.png", lines)
        self.assertIn("StartupWMClass=io.github.bbport.Launcher", lines)

    def test_applications_dir_follows_xdg_data_home(self):
        self.assertEqual(bbport_shortcut.applications_dir({"XDG_DATA_HOME": "/d"}),
                         Path("/d/applications"))

    def test_write_entry_modes(self):
        with tempfile.TemporaryDirectory() as tmp:
            menu = bbport_shortcut.write_entry(Path(tmp) / "apps", "/a", "/i")
            self.assertEqual(menu.stat().st_mode & 0o777, 0o644)
            desk = bbport_shortcut.write_entry(Path(tmp) / "desk", "/a", "/i", trusted=True)
            self.assertEqual(desk.stat().st_mode & 0o777, 0o755)
            self.assertEqual(desk.read_text(), bbport_shortcut.entry_text("/a", "/i"))


if __name__ == "__main__":
    unittest.main()
