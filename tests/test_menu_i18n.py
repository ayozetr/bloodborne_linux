from paths import ROOT
import re
import unittest

SHIM = ROOT / 'gpu' / 'shim'
LITERALS = re.compile(r'\s*"((?:[^"\\]|\\.)*)"')
PRINTF = re.compile(r'%[-+ #0]*\d*(?:\.\d+)?[a-zA-Z]')


def literals(src, pos):
    """The adjacent C string literals at pos, joined, and the position after them."""
    parts = []
    while match := LITERALS.match(src, pos):
        parts.append(match.group(1))
        pos = match.end()
    return ''.join(parts) if parts else None, pos


def translations():
    """bbport_menu_i18n.h: English -> the Spanish, Italian, French, German, Portuguese, Chinese
    row."""
    src = (SHIM / 'bbport_menu_i18n.h').read_text(encoding='utf-8')
    rows = {}
    for match in re.finditer(r'\n    \{(?=\s*")', src):
        english, pos = literals(src, match.end())
        pos = src.index('{', pos) + 1
        row = []
        while True:
            text, pos = literals(src, pos)
            row.append(text)
            pos = re.compile(r'\s*').match(src, pos).end()
            if src[pos] != ',':
                break
            pos += 1
        rows[english] = row
    return rows


def menu_texts():
    """The English texts of MenuText()/AddText() calls with literal arguments (when the Russian
    differs: names such as "FSR 3.1" are the same everywhere), of the game menu's page() and
    row() calls, and the game effects' labels."""
    texts = {}
    for path in sorted(SHIM.glob('*.cpp')):
        src = path.read_text(encoding='utf-8')
        for match in re.finditer(r'\b(MenuText|AddText|page|row)\(', src):
            pos = match.end()
            if match.group(1) == 'row':
                pos = src.find(',', pos) + 1
            pairs = []
            while True:
                text, pos = literals(src, pos)
                if text is None:
                    break
                pairs.append(text)
                pos = re.compile(r'\s*,?').match(src, pos).end()
            for english, russian in zip(pairs[::2], pairs[1::2]):
                if english != russian:
                    texts[english] = f'{path.name}:{src.count(chr(10), 0, match.start()) + 1}'
    effects = (SHIM / 'bbport_settings.h').read_text(encoding='utf-8')
    for match in re.finditer(r'\{"\w+", "((?:[^"\\]|\\.)*)", "(?:[^"\\]|\\.)*", (?:true|false)\}',
                             effects):
        texts[match.group(1)] = 'bbport_settings.h'
    return texts


def effect_help_texts():
    """The help lines the game menu's Effects page shows (bbport_game_menu.cpp): each effect's
    short help, with " (after a restart)" when BbSettings::IsHotEffect() says the effect does not
    change live. These are built at run time, so menu_texts() does not see them."""
    settings = (SHIM / 'bbport_settings.h').read_text(encoding='utf-8')
    keys = re.findall(r'\{"(\w+)", "(?:[^"\\]|\\.)*", "(?:[^"\\]|\\.)*", (?:true|false)\}', settings)
    body = re.search(r'IsHotEffect\(int effect\) \{\s*return ([^;]+);', settings).group(1)
    hot = lambda effect: eval(body.replace('&&', ' and ').replace('||', ' or '), {}, {'effect': effect})
    menu = (SHIM / 'bbport_game_menu.cpp').read_text(encoding='utf-8')
    texts = {}
    text = r'"((?:[^"\\]|\\.)*)"'
    for match in re.finditer(r'\{"(\w+)"' + (r',\s*' + text) * 4 + r'(?:,\s*(true|false))?\}', menu):
        key, help_en, graphics = match.group(1), match.group(4), match.group(6)
        if key in keys and graphics != 'false':
            index = keys.index(key)
            texts[help_en + ('' if hot(index) else ' (after a restart)')] = f'effect {key}'
    return texts


class MenuTranslationTests(unittest.TestCase):
    def test_every_menu_text_is_translated(self):
        texts, rows = menu_texts(), translations()
        self.assertGreater(len(texts), 80)
        self.assertEqual(sorted(f'{where}: {text}' for text, where in texts.items()
                                if text not in rows), [])

    def test_every_effect_help_is_translated(self):
        texts, rows = effect_help_texts(), translations()
        self.assertGreaterEqual(len(texts), 6)
        self.assertEqual(sorted(f'{where}: {text}' for text, where in texts.items()
                                if text not in rows), [])

    def test_rows_have_every_language_and_keep_the_placeholders(self):
        for english, row in translations().items():
            with self.subTest(text=english[:40]):
                self.assertEqual(len(row), 6)
                for text in row:
                    self.assertEqual(PRINTF.findall(text), PRINTF.findall(english))


if __name__ == '__main__':
    unittest.main()
