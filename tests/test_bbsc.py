from paths import ROOT
import json
import tempfile
import unittest
from pathlib import Path

import bbsc
import online

INFO = {'settings': [
    {'id': 'seamless', 'type': 'bool', 'default': True, 'env': 'BBSC_MOD_SEAMLESS'},
    {'id': 'scale_boss_hp', 'type': 'int', 'default': 100, 'min': 0, 'max': 300,
     'env': 'BBSC_SCALE_BOSS_HP'},
    {'id': 'relay', 'type': 'text', 'default': '', 'env': 'BBSC_RELAY'},
    {'id': 'discord', 'type': 'bool', 'default': True, 'env': 'SHADPS4_BBSC_DISCORD'},
    {'id': 'broken', 'type': 'bool', 'default': True},
]}


class BbscTests(unittest.TestCase):
    def test_the_repository_mod_json(self):
        options = bbsc.options()
        self.assertEqual(len(options), 30)
        self.assertNotIn('discord', [o['id'] for o in options])
        for option in options:
            self.assertIn(option['type'], ('bool', 'int', 'text'))
            self.assertTrue(option['env'])

    def test_off_gives_nothing(self):
        self.assertEqual(bbsc.environment({}, INFO), {})
        self.assertEqual(bbsc.environment({'bbsc': False, 'bbsc_options': {'seamless': False}}, INFO), {})

    def test_defaults_and_choices(self):
        self.assertEqual(bbsc.environment({'bbsc': True}, INFO),
                         {'BB_BBSC': '1', 'BBSC_MOD_SEAMLESS': '1', 'BBSC_SCALE_BOSS_HP': '100'})
        chosen = {'seamless': False, 'scale_boss_hp': 900, 'relay': ' 10.0.0.2:20444 '}
        self.assertEqual(bbsc.environment({'bbsc': True, 'bbsc_options': chosen}, INFO),
                         {'BB_BBSC': '1', 'BBSC_MOD_SEAMLESS': '0', 'BBSC_SCALE_BOSS_HP': '300',
                          'BBSC_RELAY': '10.0.0.2:20444'})
        # Values of the wrong type fall back to the default.
        chosen = {'seamless': 'yes', 'scale_boss_hp': 'many'}
        self.assertEqual(bbsc.environment({'bbsc': True, 'bbsc_options': chosen}, INFO),
                         {'BB_BBSC': '1', 'BBSC_MOD_SEAMLESS': '1', 'BBSC_SCALE_BOSS_HP': '100'})

    def test_no_mod_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(bbsc.mod_info([Path(tmp) / 'mod.json']))
            (Path(tmp) / 'mod.json').write_text(json.dumps(INFO))
            self.assertEqual(bbsc.mod_info([Path(tmp) / 'missing', Path(tmp) / 'mod.json']), INFO)
        self.assertEqual(bbsc.options({}), [])

    def test_online_environment_on_every_server(self):
        for settings in ({'online_server_kind': 'thd', 'online_npid': 'hunter'},
                         {'online_server_kind': 'own', 'online_server': '10.0.0.2:31313'}):
            self.assertEqual(online.environment(settings).get('BB_BBSC'), None)
            env = online.environment(settings | {'bbsc': True})
            self.assertEqual(env['BB_BBSC'], '1')
            self.assertEqual(env['BB_ONLINE'], '1')


if __name__ == '__main__':
    unittest.main()
