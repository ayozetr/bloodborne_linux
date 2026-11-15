#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-2.0-or-later
# Builds and runs every *-test target of gpu/CMakeLists.txt, after build.sh (which configures
# out/gpu). Each test runs on its own; the script fails if any of them does. The tests that open
# a Vulkan device run only where vulkaninfo finds one: GitHub's machines have no GPU.
set -uo pipefail
tests=$(sed -nE 's/^add_executable\(([a-z0-9-]+-test) .*/\1/p' gpu/CMakeLists.txt)
[[ -n $tests ]] || { echo 'no tests found in gpu/CMakeLists.txt' >&2; exit 1; }
gpu_tests=' scene-resolution-test taa-shader-test camera-motion-test translation-memory-test image-spares-test '
gpu=0
vulkaninfo --summary 2>/dev/null | grep -qE 'deviceType += PHYSICAL_DEVICE_TYPE_(DISCRETE|INTEGRATED|VIRTUAL)_GPU' && gpu=1
# shellcheck disable=SC2086
ninja -C out/gpu $tests || exit 1
failed=() skipped=()
for test in $tests; do
    if ((!gpu)) && [[ $gpu_tests == *" $test "* ]]; then
        skipped+=("$test"); echo "$test: skipped (no Vulkan device)"; continue
    fi
    echo "::group::$test"
    if out/gpu/"$test"; then echo "$test: passed"; else failed+=("$test"); echo "$test: FAILED"; fi
    echo '::endgroup::'
done
((${#skipped[@]})) && echo "Skipped without a GPU: ${skipped[*]}"
if ((${#failed[@]})); then
    echo "Failed: ${failed[*]}" >&2
    exit 1
fi
echo "C++ tests passed: $(($(wc -w <<<"$tests") - ${#skipped[@]})) of $(wc -w <<<"$tests")"
