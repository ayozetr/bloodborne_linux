from paths import ROOT
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(ROOT / 'launcher'))
import bbport_coop as coop


class LayoutTests(unittest.TestCase):
    def test_two_players_in_rows_or_columns(self):
        self.assertEqual([coop.rect_text(r) for r in coop.layout_rects(2, 'rows')],
                         ['0,0,1,0.5', '0,0.5,1,0.5'])
        self.assertEqual([coop.rect_text(r) for r in coop.layout_rects(2, 'columns')],
                         ['0,0,0.5,1', '0.5,0,0.5,1'])

    def test_three_and_four_players_take_the_quarters(self):
        self.assertEqual(len(coop.layout_rects(3, 'columns')), 3)
        self.assertEqual(coop.rect_text(coop.layout_rects(4)[3]), '0.5,0.5,0.5,0.5')

    def test_player_count_is_checked(self):
        for players in (1, 5):
            with self.assertRaises(ValueError):
                coop.layout_rects(players)


class ProfileTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.data = Path(temp.name)

    def test_players_two_to_four_get_player_ones_ini_once(self):
        ini = self.data / 'bbport.ini'
        ini.write_text('fov=50\n')
        folder = coop.prepare_data_dir(self.data, 2, ini)
        self.assertEqual(folder, self.data / 'coop/player2')
        self.assertEqual((folder / 'bbport.ini').read_text(), 'fov=50\n')
        (folder / 'bbport.ini').write_text('fov=60\n')
        coop.prepare_data_dir(self.data, 2, ini)
        self.assertEqual((folder / 'bbport.ini').read_text(), 'fov=60\n')

    def test_no_ini_yet_is_fine(self):
        folder = coop.prepare_data_dir(self.data, 3, self.data / 'bbport.ini')
        self.assertTrue(folder.is_dir())
        self.assertFalse((folder / 'bbport.ini').exists())

    def test_only_player_one_keeps_its_account_and_saves(self):
        settings = {'user_dir': '/saves', 'online': True, 'online_npid': 'hunter',
                    'online_password': 'x', 'discord': True, 'gamepad': 'Faceoff', 'fov': 1}
        self.assertEqual(coop.player_settings(settings, 1), settings)
        second = coop.player_settings(settings, 2)
        self.assertEqual((second['user_dir'], second['online'], second['online_npid'],
                          second['online_password'], second['discord'], second['gamepad']),
                         ('', False, '', '', False, ''))
        self.assertEqual(second['fov'], 1)
        self.assertEqual(settings['online_npid'], 'hunter')


class EnvironmentTests(unittest.TestCase):
    BASE = {'BB_GAMEPAD': 'old', 'BB_USER_DIR': '/saves', 'BB_CONFIG': '/p1/bbport.ini',
            'BB_FULLSCREEN': '1', 'PATH': '/bin'}

    def test_controller_player(self):
        env = coop.player_environment(self.BASE, 1, 2, '/dev/hidraw5')
        self.assertEqual(env['BB_GAMEPAD'], '/dev/hidraw5')
        self.assertEqual(env['BB_GAMEPAD_STRICT'], '1')
        self.assertEqual(env['BB_KEYBOARD'], '0')
        self.assertEqual(env['BB_WINDOW_RECT'], '0,0,1,0.5')
        self.assertEqual((env['SDL_VIDEO_DRIVER'], env['BB_PAD_BACKGROUND'], env['BB_FULLSCREEN']),
                         ('x11', '1', '0'))
        self.assertNotIn('BB_AUDIO', env)
        self.assertEqual(env['BB_USER_DIR'], '/saves')  # player 1 keeps its files
        self.assertEqual(self.BASE['BB_GAMEPAD'], 'old')

    def test_keyboard_player_has_no_controller(self):
        env = coop.player_environment(dict(self.BASE, BB_KEYBOARD='0'), 2, 2, coop.KEYBOARD,
                                      layout='columns', folder=Path('/data/coop/player2'))
        self.assertNotIn('BB_GAMEPAD', env)
        self.assertNotIn('BB_KEYBOARD', env)
        self.assertEqual(env['BB_GAMEPAD_STRICT'], '1')
        self.assertEqual(env['BB_WINDOW_RECT'], '0.5,0,0.5,1')

    def test_other_players_use_their_own_folder_and_may_be_silent(self):
        env = coop.player_environment(self.BASE, 2, 2, '/dev/hidraw6',
                                      folder=Path('/data/coop/player2'))
        self.assertEqual(env['BB_DATA_DIR'], '/data/coop/player2')
        self.assertNotIn('BB_USER_DIR', env)
        self.assertNotIn('BB_CONFIG', env)
        self.assertEqual(env['BB_AUDIO'], 'none')
        loud = coop.player_environment(self.BASE, 2, 2, '/dev/hidraw6', sound_first_only=False)
        self.assertNotIn('BB_AUDIO', loud)


class ProblemTests(unittest.TestCase):
    def test_ready(self):
        self.assertEqual(coop.problems(2, ['/dev/hidraw5', coop.KEYBOARD, '']), [])

    def test_missing_same_and_keyboard_twice(self):
        self.assertEqual(coop.problems(2, ['/dev/hidraw5']), ['controller'])
        self.assertEqual(coop.problems(2, ['/dev/hidraw5', '']), ['controller'])
        self.assertEqual(coop.problems(2, ['/dev/hidraw5', '/dev/hidraw5']), ['same controller'])
        self.assertEqual(coop.problems(3, [coop.KEYBOARD, coop.KEYBOARD, '/dev/hidraw5']),
                         ['keyboard twice'])


if __name__ == '__main__':
    unittest.main()
