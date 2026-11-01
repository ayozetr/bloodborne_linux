from paths import ROOT  # noqa: F401  (puts scripts/ on the path)
import json
import tempfile
import unittest
from pathlib import Path

import bbsc
import online

LISTED = [
    {'id': 'scaling', 'type': 'bool', 'default': True, 'env': 'SHADPS4_BBSC_SCALING'},
    {'id': 'scale_boss_hp', 'type': 'int', 'default': 100, 'min': 0, 'max': 300,
     'env': 'BBSC_SCALE_BOSS_HP'},
    {'id': 'relay', 'type': 'text', 'default': '', 'env': 'BBSC_RELAY'},
]


class BbscTests(unittest.TestCase):
    def test_the_repository_list(self):
        options = bbsc.options()
        self.assertEqual(len(options), 28)
        ids = [o['id'] for o in options]
        for left_out in ('seamless', 'hooks', 'discord', 'p2p_channel'):
            self.assertNotIn(left_out, ids)
        for option in options:
            self.assertIn(option['type'], ('bool', 'int', 'text'))
            self.assertTrue(option['env'])

    def test_off_gives_nothing(self):
        self.assertEqual(bbsc.environment({'bbsc': False, 'bbsc_options': {'scaling': False}},
                                          LISTED), {})

    def test_only_what_the_player_changed(self):
        self.assertEqual(bbsc.environment({'bbsc': True}, LISTED), {})
        chosen = {'scaling': False, 'scale_boss_hp': 900, 'relay': ' 10.0.0.2:20444 '}
        self.assertEqual(bbsc.environment({'bbsc': True, 'bbsc_options': chosen}, LISTED),
                         {'SHADPS4_BBSC_SCALING': '0', 'BBSC_SCALE_BOSS_HP': '300',
                          'BBSC_RELAY': '10.0.0.2:20444'})
        # Values of the wrong type fall back to the default.
        chosen = {'scaling': 'yes', 'scale_boss_hp': 'many'}
        self.assertEqual(bbsc.environment({'bbsc': True, 'bbsc_options': chosen}, LISTED),
                         {'SHADPS4_BBSC_SCALING': '1', 'BBSC_SCALE_BOSS_HP': '100'})

    def test_no_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(bbsc.options(Path(tmp) / 'missing.json'), [])
            (Path(tmp) / 'list.json').write_text(json.dumps({'settings': LISTED}))
            self.assertEqual(len(bbsc.options(Path(tmp) / 'list.json')), 3)

    def test_online_environment_carries_them(self):
        settings = {'online_server_kind': 'own', 'online_server': '10.0.0.2:31313', 'bbsc': True,
                    'bbsc_options': {'scale_enemy_hp': 60}}
        env = online.environment(settings)
        self.assertEqual((env['BB_BBSC'], env['BBSC_SCALE_ENEMY_HP']), ('1', '60'))
        self.assertNotIn('BBSC_SCALE_ENEMY_HP', online.environment(settings | {'bbsc': False}))


if __name__ == '__main__':
    unittest.main()
