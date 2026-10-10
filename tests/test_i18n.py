from paths import ROOT
import ast
import re
import string
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


# The languages this fork keeps complete; ZH_CN comes from upstream and is not maintained here.
MAINTAINED = ('EN', 'ES', 'IT', 'FR', 'DE', 'PT_BR')
CYRILLIC = re.compile('[А-Яа-яЁё]')


def launcher_texts():
    """The Russian texts the launcher translates: tr()'s literal arguments, and the choice
    lists' labels (tuples of module-level constants, passed to tr() later)."""
    texts = set()
    for path in sorted((ROOT / 'launcher').glob('*.py')):
        if path.name == 'bbport_i18n.py':
            continue
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and getattr(node.func, 'id', None) == 'tr' and node.args
                    and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                texts.add(node.args[0].value)
        for node in tree.body:
            if isinstance(node, ast.Assign) and all(getattr(t, 'id', '').isupper() for t in node.targets):
                for item in ast.walk(node.value):
                    if (isinstance(item, ast.Tuple) and item.elts and isinstance(item.elts[0], ast.Constant)
                            and isinstance(item.elts[0].value, str)):
                        texts.add(item.elts[0].value)
    return {text for text in texts if CYRILLIC.search(text)}


def fields(text):
    return sorted(str(name or index) for index, (_lit, name, _spec, _conv)
                  in enumerate(string.Formatter().parse(text)) if name is not None)


class TranslationTests(unittest.TestCase):
    def test_every_launcher_text_is_translated(self):
        texts = launcher_texts()
        self.assertGreater(len(texts), 200)
        for language in MAINTAINED:
            table = getattr(bbport_i18n, language)
            with self.subTest(language=language):
                self.assertEqual(sorted(t for t in texts if t not in table), [])

    def test_translations_keep_the_placeholders(self):
        for language in (*MAINTAINED, 'ZH_CN'):
            for key, text in getattr(bbport_i18n, language).items():
                with self.subTest(language=language, key=key[:40]):
                    self.assertEqual(len(fields(text)), len(fields(key)))


if __name__ == '__main__':
    unittest.main()
