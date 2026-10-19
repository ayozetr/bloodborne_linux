from paths import ROOT  # noqa: F401  (puts scripts/ on the path)
import tempfile
import unittest
from pathlib import Path

import bbsc_kit_texts as kit
from test_quit_menu import fmg, menu_archive, strings_of


def item_archive(names, helps, captions):
    return menu_archive({10: fmg(names), 20: fmg(helps), 24: fmg(captions), 11: fmg({1: 'other'})})


class KitTextTests(unittest.TestCase):
    def test_fills_only_the_empty_kit_slots(self):
        archive = item_archive({200: 'Beckoning Bell', 4016: None, 4121: 'A mod named it'},
                               {200: 'Use Insight', 4016: None}, {200: 'Great old bell'})
        out = strings_of(kit.item_texts(archive, 'spaes'))
        self.assertEqual(out[10][200], 'Beckoning Bell')
        self.assertEqual(out[10][4016], 'Hunt Bell')
        self.assertEqual(out[10][4121], 'A mod named it')  # not empty: kept
        self.assertEqual(out[10][4313], 'Duel Bell')
        self.assertEqual(out[20][200], 'Use Insight')
        self.assertTrue(out[20][4016].startswith('Requiere BBSC'))
        self.assertTrue(out[24][11251].startswith('A blank of silent powder'))
        self.assertEqual(out[11], {1: 'other'})

    def test_help_is_one_line(self):
        self.assertTrue(all('\n' not in line for line in kit.OFF_HELP.values()))

    def test_other_languages_get_the_english_help(self):
        out = strings_of(kit.item_texts(item_archive({}, {}, {}), 'korkr'))
        self.assertTrue(out[20][4016].startswith('Needs BBSC on'))

    def test_nothing_to_fill_writes_nothing(self):
        full = {goods: 'x' for goods in kit.KIT}
        self.assertIsNone(kit.item_texts(item_archive(full, full, full), 'engus'))

    def test_layer_holds_each_language_s_item_texts(self):
        with tempfile.TemporaryDirectory() as temp:
            game = Path(temp) / 'game'
            folder = game / 'dvdroot_ps4' / 'msg' / 'engus'
            folder.mkdir(parents=True)
            (folder / 'item.msgbnd.dcx').write_bytes(item_archive({}, {}, {}))
            out = Path(temp) / 'out' / 'bbsc-kit'
            out.parent.mkdir()
            kit.write_layer(game, out)
            self.assertTrue((out / 'dvdroot_ps4/msg/engus/item.msgbnd.dcx').is_file())


if __name__ == '__main__':
    unittest.main()
