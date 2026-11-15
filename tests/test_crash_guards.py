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


def short_target(code, at):
    """Where the two-byte jump at `at` in `code` (placed at its offset) goes."""
    return code[0] + at + 2 + struct.unpack_from('<b', code[1], at + 1)[0]


class CrashGuardsTest(unittest.TestCase):
    def test_the_guard_sits_in_the_code_pages_free_tail(self):
        (cave, code), _site, _claim = crash_guards.code_writes()
        self.assertGreaterEqual(cave, crash_guards.CODE_END)
        self.assertLessEqual(cave + len(code), crash_guards.CAVE_END)

    def test_no_data_goes_where_an_unknown_event_goes_and_data_carries_on(self):
        (cave, code), (site, jump), _claim = crash_guards.code_writes()
        self.assertEqual(code[:3], bytes.fromhex('4d85e4'))                      # test r12, r12
        self.assertEqual(target((cave, code), 3, 6), crash_guards.EVENT_UNKNOWN)  # jz
        self.assertEqual(code[9:20], crash_guards.EVENT_CASE_BYTES)
        self.assertEqual(target((cave, code), 20, 5), crash_guards.EVENT_CASE + 11)
        self.assertEqual(len(jump), len(crash_guards.EVENT_CASE_BYTES))
        self.assertEqual(target((site, jump), 0, 5), cave)

    def test_the_claim_replaces_the_loop_exactly(self):
        *_event, claim = crash_guards.code_writes()
        self.assertEqual(claim, crash_guards.lod_claim_code())
        offset, code = claim
        self.assertEqual(offset, crash_guards.LOD_CLAIM)
        self.assertEqual(len(code), len(crash_guards.LOD_CLAIM_BYTES))
        self.assertEqual(offset + len(code), crash_guards.LOD_CLAIM_END)

    def test_the_claim_is_a_bounded_lock_cmpxchg(self):
        _offset, code = crash_guards.lod_claim_code()
        claim = code.index(bytes.fromhex('f00fb18cb700010000'))   # lock cmpxchg [rdi+rsi*4+0x100], ecx
        bound = code.index(bytes.fromhex('483b84dfa8000000'))     # cmp rax, [rdi+rbx*8+0xa8]
        self.assertLess(bound, claim)
        self.assertEqual(code[bound + 8], 0x73)                   # jae: a full slot is never claimed
        self.assertEqual(code[claim - 3:claim], bytes.fromhex('8d4801'))   # count + 1 from that count

    def test_the_claims_jumps(self):
        claim = crash_guards.lod_claim_code()
        offset, code = claim
        self.assertEqual(code[:3], bytes.fromhex('4531ff'))      # r15d = 0 on every way out
        # Instruction by instruction (the guard's own instructions only), so operand bytes are
        # never read as jumps.
        plain = [bytes.fromhex(h) for h in (
            '4531ff', '83f903', '89ce', '488d1c76', '8b84b700010000', '483b84dfa8000000', '8d4801',
            'f00fb18cb700010000', '4c8b8cdfb0000000', '4c69d0d0030000', '4b8d1411', '91', '8d4e01', '90')]
        jumps = {}
        at = 0
        while at < len(code):
            op = code[at]
            known = next((p for p in plain if code.startswith(p, at)), None)
            if known:
                at += len(known)
            elif op in (0x77, 0x73, 0x75, 0xEB):
                jumps.setdefault(op, []).append(short_target(claim, at))
                at += 2
            elif op == 0xE9:
                jumps.setdefault(op, []).append(target(claim, at, 5))
                at += 5
            else:
                self.fail(f'unexpected byte {op:#x} at +{at:#x}')
        self.assertIn(crash_guards.LOD_CLAIM_END, jumps[0xEB])   # on with the element
        self.assertEqual(jumps[0xE9], [crash_guards.LOD_ALL_FULL])   # every slot full
        self.assertEqual(jumps[0x75], [offset + code.index(bytes.fromhex('8b84b700010000'))])  # retry
        for targets in jumps.values():
            for t in targets:
                self.assertTrue(offset <= t <= crash_guards.LOD_CLAIM_END or t == crash_guards.LOD_ALL_FULL)

    def test_other_code_is_refused(self):
        def image(site, cave=b'', claim=crash_guards.LOD_CLAIM_BYTES):
            return lambda offset, size: (site if offset == crash_guards.EVENT_CASE
                                         else claim if offset == crash_guards.LOD_CLAIM
                                         else cave.ljust(size, b'\0'))
        self.assertTrue(crash_guards.applies(image(crash_guards.EVENT_CASE_BYTES)))
        self.assertFalse(crash_guards.applies(image(b'\x90' * 11)))
        self.assertFalse(crash_guards.applies(image(crash_guards.EVENT_CASE_BYTES, b'\xcc')))
        self.assertFalse(crash_guards.applies(image(crash_guards.EVENT_CASE_BYTES,
                                                    claim=crash_guards.lod_claim_code()[1])))

    def test_turned_off(self):
        self.assertEqual(patches.crash_guard_writes(b'', {'BB_CRASH_GUARDS': '0'}), [])


if __name__ == '__main__':
    unittest.main()
