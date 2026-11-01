# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""The launcher's settings from earlier launchers as 0.7 reads them, and frame generation's rows."""
from paths import ROOT
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

# The launcher's window needs GTK; these tests use its functions only.
gi = types.ModuleType("gi")
gi.require_version = lambda *_args: None
gi.repository = mock.MagicMock()
gi.repository.Adw.ApplicationWindow = type("ApplicationWindow", (), {})
gi.repository.Adw.Application = type("Application", (), {})
sys.modules.setdefault("gi", gi)
sys.modules.setdefault("gi.repository", gi.repository)
sys.path.insert(0, str(ROOT / "launcher"))
spec = importlib.util.spec_from_file_location("bbport_launcher", ROOT / "launcher/bbport_launcher.py")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class MigrationTests(unittest.TestCase):
    def setUp(self):
        folder = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: [p.unlink() for p in folder.iterdir()] and folder.rmdir())
        self.ini = folder / "bbport.ini"
        for patcher in (mock.patch.dict(os.environ, {"BB_CONFIG": str(self.ini)}),
                        mock.patch.object(launcher, "CONFIG_DIR", folder),
                        mock.patch.object(launcher, "CONFIG_FILE", folder / "settings.json")):
            patcher.start()
            self.addCleanup(patcher.stop)

    def migrate(self, ini_text, settings=None):
        self.ini.write_text(ini_text)
        settings = dict(launcher.DEFAULTS, **(settings or {}))
        values, lines = launcher.load_ini()
        launcher.migrate_ini(settings, values, lines)
        return settings, launcher.load_ini()[0]

    def test_each_player_keeps_the_keys_they_had(self):
        # The fork's launcher wrote bbport (its own keys) or 0.6 (0.7's, Dark Souls III's).
        for old, new in (("bbport", "classic"), ("0.6", "0.7"), ("classic", "classic")):
            with self.subTest(old=old):
                settings, ini = self.migrate(f"keyboard_layout={old}\n")
                self.assertEqual(ini["keyboard_layout"], new)
                self.assertTrue(settings["keyboard_layout_07"])

    def test_keyboard_layout_moves_once(self):
        settings, ini = self.migrate("keyboard_layout=bbport\n", {"keyboard_layout_07": True})
        self.assertEqual(ini["keyboard_layout"], "bbport")

    def test_new_players_get_0_7_s_keys(self):
        _settings, ini = self.migrate("")
        self.assertEqual(ini["keyboard_layout"], "0.7")

    def test_button_prompts_move_to_bbport_ini(self):
        settings, ini = self.migrate("", {"prompts": "switch"})
        self.assertEqual(ini["button_prompts"], "switch")
        self.assertNotIn("prompts", settings)
        # Automatic was "" in the launcher's settings.
        settings, ini = self.migrate("", {"prompts": ""})
        self.assertEqual(ini["button_prompts"], "auto")
        # One the game's menu or the player wrote stays.
        settings, ini = self.migrate("button_prompts=xbox\n", {"prompts": "switch"})
        self.assertEqual(ini["button_prompts"], "xbox")


class FrameGenerationTests(unittest.TestCase):
    def test_choices_and_bbport_ini(self):
        for choice, ini in (("off", {"frame_generation": "off"}), ("fsr3", {"frame_generation": "fsr3"}),
                            ("dlss3", {"frame_generation": "dlss", "frame_generation_multiplier": "3"})):
            with self.subTest(choice=choice):
                self.assertEqual(launcher.frame_gen_ini(choice), ini)
                self.assertEqual(launcher.frame_gen_choice(ini), choice)
        self.assertEqual(launcher.frame_gen_choice({"frame_generation": "dlss",
                                                    "frame_generation_multiplier": "7"}), "dlss2")


if __name__ == "__main__":
    unittest.main()
