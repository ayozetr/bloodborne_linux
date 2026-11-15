#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-2.0-or-later
# Builds and runs every *-test target of gpu/CMakeLists.txt, after build.sh (which configures
# out/gpu). Each test runs on its own; the script fails if any of them does.
set -uo pipefail
tests=$(sed -nE 's/^add_executable\(([a-z0-9-]+-test) .*/\1/p' gpu/CMakeLists.txt)
[[ -n $tests ]] || { echo 'no tests found in gpu/CMakeLists.txt' >&2; exit 1; }
# shellcheck disable=SC2086
ninja -C out/gpu $tests || exit 1
failed=()
for test in $tests; do
    echo "::group::$test"
    if out/gpu/"$test"; then echo "$test: passed"; else failed+=("$test"); echo "$test: FAILED"; fi
    echo '::endgroup::'
done
if ((${#failed[@]})); then
    echo "Failed: ${failed[*]}" >&2
    exit 1
fi
echo "All $(wc -w <<<"$tests") C++ tests passed"
