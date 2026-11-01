# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""The crash guards (scripts/crash_guards.py): where their code goes and what it does."""
from paths import ROOT
import struct
import sys
import unittest

sys.path.insert(0, str(ROOT / 'scripts'))
import crash_guards  # noqa: E402
import patches  # noqa: E402


def target(code, at, length):
    """Where the rel32 jump ending at `at + length` in `code` (placed at its offset) goes."""
    return code[0] + at + length + struct.unpack_from('<i', code[1], at + length - 4)[0]


class CrashGuardsTest(unittest.TestCase):
    def test_the_guard_sits_in_the_code_pages_free_tail(self):
        (cave, code), _site = crash_guards.code_writes()
        self.assertGreaterEqual(cave, crash_guards.CODE_END)
        self.assertLessEqual(cave + len(code), crash_guards.CAVE_END)

    def test_no_data_goes_where_an_unknown_event_goes_and_data_carries_on(self):
        (cave, code), (site, jump) = crash_guards.code_writes()
        self.assertEqual(code[:3], bytes.fromhex('4d85e4'))                      # test r12, r12
        self.assertEqual(target((cave, code), 3, 6), crash_guards.EVENT_UNKNOWN)  # jz
        self.assertEqual(code[9:20], crash_guards.EVENT_CASE_BYTES)
        self.assertEqual(target((cave, code), 20, 5), crash_guards.EVENT_CASE + 11)
        self.assertEqual(len(jump), len(crash_guards.EVENT_CASE_BYTES))
        self.assertEqual(target((site, jump), 0, 5), cave)

    def test_other_code_is_refused(self):
        def image(site, cave=b''):
            return lambda offset, size: (site if offset == crash_guards.EVENT_CASE
                                         else cave.ljust(size, b'\0'))
        self.assertTrue(crash_guards.applies(image(crash_guards.EVENT_CASE_BYTES)))
        self.assertFalse(crash_guards.applies(image(b'\x90' * 11)))
        self.assertFalse(crash_guards.applies(image(crash_guards.EVENT_CASE_BYTES, b'\xcc')))

    def test_turned_off(self):
        self.assertEqual(patches.crash_guard_writes(b'', {'BB_CRASH_GUARDS': '0'}), [])


if __name__ == '__main__':
    unittest.main()
