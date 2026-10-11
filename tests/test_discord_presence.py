from paths import ROOT  # noqa: F401
import tempfile
import unittest
from pathlib import Path

import discord_presence as presence


class AreaTests(unittest.TestCase):
    def test_areas_by_map(self):
        self.assertEqual(presence.area_name('m24_01'), 'Central Yharnam')
        self.assertEqual(presence.area_name('M21_00\n'), "Hunter's Dream")
        self.assertEqual(presence.area_name('m29_10'), presence.CHALICE_DUNGEON)
        self.assertIsNone(presence.area_name('m99_99'))
        self.assertIsNone(presence.area_name(None))

    def test_every_map_folder_of_the_game_has_a_name(self):
        # The game's map folders (dvdroot_ps4/map/mXX_YY_00_00), test maps and m29 aside.
        maps = ['m21_00', 'm21_01', 'm22_00', 'm23_00', 'm24_00', 'm24_01', 'm24_02', 'm25_00',
                'm26_00', 'm27_00', 'm28_00', 'm32_00', 'm33_00', 'm34_00', 'm35_00', 'm36_00']
        self.assertEqual(sorted(presence.AREAS), maps)


class StateTests(unittest.TestCase):
    def test_area_and_partners(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(presence.read_state(tmp), (None, []))
            (Path(tmp) / 'area').write_text('m24_01\n')
            (Path(tmp) / 'coop').write_text('Hunter\n\nFriend_2\n')
            self.assertEqual(presence.read_state(tmp), ('m24_01', ['Hunter', 'Friend_2']))
            (Path(tmp) / 'coop').write_text('')
            self.assertEqual(presence.read_state(tmp), ('m24_01', []))
        self.assertEqual(presence.read_state(None), (None, []))


class ActivityTests(unittest.TestCase):
    def test_before_an_area(self):
        value = presence.activity(True, 100)
        self.assertEqual(value['details'], 'Online')
        self.assertNotIn('state', value)

    def test_area_and_session(self):
        self.assertEqual(presence.activity(False, 100, 'm24_01')['state'], 'Offline')
        value = presence.activity(True, 100, 'm21_00', ['Hunter'])
        self.assertEqual((value['details'], value['state']), ("Hunter's Dream", 'Co-op with Hunter'))
        self.assertEqual(presence.activity(True, 100, 'm24_01', ['A', 'B'])['state'],
                         'Co-op with A, B')

    def test_unknown_map_shows_the_session(self):
        value = presence.activity(True, 100, 'm99_99', ['Hunter'])
        self.assertEqual(value['details'], 'Co-op with Hunter')
        self.assertNotIn('state', value)


if __name__ == '__main__':
    unittest.main()
