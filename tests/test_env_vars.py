# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""The environment variable list (gpu/shim/bb_env_vars.def) against the code, and its document."""
from paths import ROOT
import contextlib
import io
import unittest

import env_vars


class EnvVarsTests(unittest.TestCase):
    def test_list_matches_the_code(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            ok = env_vars.check()
        self.assertTrue(ok, out.getvalue())

    def test_document_lists_every_variable(self):
        document = env_vars.document()
        for name in env_vars.registry():
            self.assertIn(f'`{name}`', document)


if __name__ == '__main__':
    unittest.main()
