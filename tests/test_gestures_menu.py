from paths import ROOT  # noqa: F401  (puts scripts/ on the path)
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import gestures_menu


class GesturesMenuTests(unittest.TestCase):
    def test_patch_applies_only_to_its_file(self):
        original = b'0123456789'
        result = b'01AB456789'
        patch = {'original_sha256': hashlib.sha256(original).hexdigest(),
                 'result_sha256': hashlib.sha256(result).hexdigest(),
                 'edits': [[2, 2, b'AB'.hex()]]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'gesturetop.json'
            path.write_text(json.dumps(patch))
            self.assertEqual(gestures_menu.apply_gestures(original, path), result)
            with self.assertRaises(ValueError):
                gestures_menu.apply_gestures(b'another file', path)

    def test_the_repository_patch_is_well_formed(self):
        patch = json.loads(gestures_menu.PATCH.read_text())
        self.assertEqual(len(patch['original_sha256']), 64)
        self.assertTrue(patch['edits'])

    def test_off_or_missing_gives_no_layer(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(FileNotFoundError):
            gestures_menu.layer(Path(tmp) / 'no-game', Path(tmp) / 'out')


if __name__ == '__main__':
    unittest.main()
