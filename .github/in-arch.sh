#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-2.0-or-later
# Runs a command in the checkout inside the bbport-arch image (.github/workflows/tests.yml), as
# the runner's user, so what it writes stays the runner's.
set -euo pipefail
exec docker run --rm --user "$(id -u):$(id -g)" -e HOME=/home/builder -v "$PWD:/src" -w /src \
    bbport-arch "$@"
