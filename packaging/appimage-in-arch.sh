#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-2.0-or-later
# Builds dist/Bloodborne-bbport-x86_64.AppImage in a container of plain Arch Linux, the way the
# releases are made. packaging/appimage-sharun.sh takes the system libraries the launcher and the
# game load from the build PC: on CachyOS those come from its x86-64-v3 repositories, and the
# AppImage then stopped at once ("illegal instruction", no message) on processors without AVX2
# and BMI2 (AMD FX and Phenom, Intel before Haswell, issue #39). Arch's own packages run on any
# x86-64 processor. The port's own code needs nothing newer either (no -march).
#
#   bash packaging/appimage-in-arch.sh        # needs docker (or podman as docker)
#
# The commit checked out (with its submodules) is built in out/arch-build/, apart from the tree's
# own out/. DLSS's SDK files (~/.cache/bbport) and the FSR 4 assets (fsr4_shaders/) already on
# this PC are reused; anything missing is downloaded inside the container.
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
root=$PWD
image=bbport-appimage-arch
work=$root/out/arch-build
docker build --network host -t "$image" -f packaging/appimage-arch.Dockerfile packaging >/dev/null
rm -rf "$work"
git clone --quiet --recursive "$root" "$work/src"
git -C "$work/src" checkout --quiet "$(git rev-parse HEAD)"
git -C "$work/src" submodule --quiet update --init --recursive
[[ -d fsr4_shaders ]] && cp -r fsr4_shaders "$work/src/"
mkdir -p "$work/cache" "${XDG_CACHE_HOME:-$HOME/.cache}/bbport"
# The container runs as this user, so what it writes stays ours.
docker run --rm --network host --user "$(id -u):$(id -g)" -e HOME=/home/builder \
    -v "$work/src:/src" -v "${XDG_CACHE_HOME:-$HOME/.cache}/bbport:/home/builder/.cache/bbport" \
    -v "$work/cache:/home/builder/.cargo" -w /src "$image" bash -c '
        set -euo pipefail
        bash build.sh
        bash tools/build_dlss.sh
        bash packaging/appimage-sharun.sh'
mkdir -p dist
# Renamed into place: an AppImage of the last build that is still open keeps running from the
# old file (copying over it would change the image under its mount).
cp "$work/src/dist/Bloodborne-bbport-x86_64.AppImage" dist/.Bloodborne-bbport-x86_64.AppImage.new
mv -f dist/.Bloodborne-bbport-x86_64.AppImage.new dist/Bloodborne-bbport-x86_64.AppImage
sha256sum dist/Bloodborne-bbport-x86_64.AppImage
