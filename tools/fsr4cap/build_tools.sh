#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-2.0-or-later
# tools/fsr4cap/build_tools.sh <folder>
#
# Builds the two tools of the FSR 4.1.1 build (build_assets.sh) into <folder>:
#   <folder>/dxil-spirv/build/dxil-spirv  DXIL -> SPIR-V as vkd3d-proton translates it (pinned
#                                         commit + dxil-spirv-class-bindings.patch; MIT);
#   <folder>/fsr4cap.exe                  records AMD's upscaler DLL under Proton (MinGW).
# dxil-spirv is kept and built again only when it no longer starts. build_assets.sh runs this
# when BB_FSR4CAP_TOOLS names no prebuilt pair; packaging/appimage-sharun.sh runs it so that the
# AppImage carries both and the user's system needs no compiler for the button (on Bazzite and
# other image-based systems installing one means rpm-ostree layering).
# Needs x86_64-w64-mingw32-gcc, cmake, ninja, gcc, python3, git and network for dxil-spirv.
set -euo pipefail
here=$(cd -- "$(dirname -- "$0")" && pwd)
dir=$(realpath -m "${1:?tools folder}")
mkdir -p "$dir"

dx=$dir/dxil-spirv
# A build that no longer starts (127: its library path names the tree where it was built,
# before the tree moved) is built again.
status=0
"$dx/build/dxil-spirv" --help >/dev/null 2>&1 || status=$?
if [[ ! -x $dx/build/dxil-spirv || $status == 126 || $status == 127 ]]; then
    rm -rf -- "${dx:?}"
    git clone -q https://github.com/HansKristian-Work/dxil-spirv.git "$dx"
    git -C "$dx" checkout -q 7dc52786cdb1f53c54dd5c5c2698dff00ea5f0a3
    git -C "$dx" submodule update -q --init --recursive
    git -C "$dx" apply "$here/dxil-spirv-class-bindings.patch"
    cmake -S "$dx" -B "$dx/build" -G Ninja -DCMAKE_BUILD_TYPE=Release >/dev/null
    ninja -C "$dx/build" dxil-spirv >/dev/null
fi

# The FidelityFX API headers (MIT) are in tools/fsr4cap/ffx.
x86_64-w64-mingw32-gcc -std=c11 -O1 -Wall -I"$here/ffx/api/include" -I"$here/ffx/upscalers/include" \
    "$here/fsr4cap.c" "$here/capture.c" "$here/rootsig.c" \
    -o "$dir/fsr4cap.exe" -ld3d12 -ldxguid -static
