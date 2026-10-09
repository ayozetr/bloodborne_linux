from paths import ROOT
import sys
import unittest
sys.path.insert(0, str(ROOT / 'launcher'))
import bbport_i18n


class GameLanguageTests(unittest.TestCase):
    def test_desktop_locale_picks_the_ps4_system_language(self):
        cases = {'es_ES.UTF-8': 3, 'fr_CA.UTF-8': 2, 'ja_JP.UTF-8': 0, 'ru_RU.UTF-8': 8,
                 'de_DE.UTF-8': 4, 'it_IT.UTF-8': 5, 'en_GB.UTF-8': 1, 'nl_NL.UTF-8': 1, '': 1}
        for locale, code in cases.items():
            with self.subTest(locale=locale):
                self.assertEqual(bbport_i18n.system_game_language({'LANG': locale}), code)

    def test_lc_all_overrides_lang(self):
        self.assertEqual(bbport_i18n.system_game_language({'LC_ALL': 'de_DE', 'LANG': 'es_ES'}), 4)


if __name__ == '__main__':
    unittest.main()
