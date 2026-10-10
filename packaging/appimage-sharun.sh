#!/usr/bin/env bash
# Builds dist/Bloodborne-bbport-x86_64.AppImage without Nix: the port's current build (run
# build.sh first), its scripts and the GTK4 launcher, with every library they load (glibc, Python
# and PyGObject, GTK 4, libadwaita, SDL3, FFmpeg, Mesa's Vulkan drivers) collected from this
# system by quick-sharun (github.com/pkgforge-dev/Anylinux-AppImages). The AppImage then runs on
# other distributions too; build it on an up-to-date Arch Linux (or CachyOS) with the launcher's
# dependencies installed. NVIDIA's driver comes from the host at run time.
# Running it opens the launcher; `--play` starts the game with the launcher's saved settings.
# Data (generated files, saves, bbport.ini): ~/.local/share/bbport (BB_DATA_DIR).
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
[[ -f out/bb-probe && -f out/gpu/libbbgpu.so ]] || { echo 'Build first: bash build.sh' >&2; exit 1; }
# FSR 4 assets ship with the package (downloaded once; files already there are kept).
bash tools/fetch_fsr4_assets.sh
root=$PWD
work=$root/out/appimage
appdir=$work/AppDir
rm -rf "$appdir"
mkdir -p "$appdir/bin" "$appdir/share/bbport" "$work/tmp"

# quick-sharun at a fixed revision; it downloads sharun and appimagetool itself (checksummed).
quick_rev=7eead3068c040e3b530aa06fd46522b4a45a62dc
quick_sha=2ae6fc29242b5c45b63f3638fff71cead679c8c41671a2c3970a6947e332470c
quick=$work/quick-sharun.sh
if ! echo "$quick_sha  $quick" | sha256sum -c --status 2>/dev/null; then
    curl -fsSL -o "$quick" \
        "https://raw.githubusercontent.com/pkgforge-dev/Anylinux-AppImages/$quick_rev/useful-tools/quick-sharun.sh"
    echo "$quick_sha  $quick" | sha256sum -c --quiet
fi
chmod +x "$quick"

# The port as run.sh expects it with BB_PREBUILT=1 (same layout as packaging/default.nix):
# share/bbport/{run.sh,scripts,...,bin/bb-probe}; bin/ is the AppImage's own bin directory.
d=$appdir/share/bbport
cp run.sh "$d/"
cp -r scripts patches fsr4_shaders launcher assets "$d/"
# The keyboard's button prompts (scripts/menu_prompts.py) are drawn with Pillow in this font.
font=$(fc-match -f '%{file}' 'DejaVu Sans:bold')
[[ $font == */DejaVuSans-Bold.ttf ]] || { echo 'DejaVu Sans Bold not found (ttf-dejavu).' >&2; exit 1; }
install -Dm644 "$font" "$d/fonts/DejaVuSans-Bold.ttf"
mkdir -p "$d/tools"
cp -r tools/fsr4cap "$d/tools/"
find "$d" -name __pycache__ -type d -prune -exec rm -rf {} +
ln -s ../../bin "$d/bin"
# DLSS (NVIDIA RTX), when tools/build_dlss.sh has built the bridge: it and NVIDIA's library.
if [[ -f out/libbbport_dlss.so ]]; then
    mkdir -p "$d/dlss"
    cp out/libbbport_dlss.so out/libnvidia-ngx-dlss.so.* out/NVIDIA-DLSS-LICENSE.txt "$d/dlss/"
fi

# The AppImage's main program: the launcher (or, with --play, the game alone).
cat > "$appdir/bin/bloodborne" <<'EOF'
#!/bin/sh
# Entry point of the AppImage (AppRun runs it with APPDIR set and APPDIR/bin first on PATH).
export BB_PREBUILT=1
export PYTHON="$APPDIR/bin/python3"
export BB_VULKANINFO="$APPDIR/bin/vulkaninfo"
export BB_DLSS_DIR="$APPDIR/share/bbport/dlss"
export BB_DATA_DIR="${BB_DATA_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/bbport}"
mkdir -p "$BB_DATA_DIR"
exec "$APPDIR/bin/python3" "$APPDIR/share/bbport/launcher/bbport_launcher.py" "$@"
EOF
chmod +x "$appdir/bin/bloodborne"
sed -e 's|@LAUNCHER@|bloodborne|' -e 's|@ICON@|bloodborne|' \
    launcher/io.github.bbport.Launcher.desktop.in > "$work/bloodborne.desktop"

# GTK, libadwaita and their typelibs are loaded by PyGObject at run time (not linked): named here.
# So are Python's ssl and hashlib modules, which quick-sharun leaves out by default: the launcher's
# connection test and scripts/online.py talk HTTPS to the co-op servers. Pillow (in site-packages,
# copied with Python) is named too, for the libraries its modules link (keyboard prompts).
pydyn=$(python3 -c 'import sysconfig; print(sysconfig.get_path("platstdlib"))')/lib-dynload
pil=$(python3 -c 'import os, PIL; print(os.path.dirname(PIL.__file__))')
cd "$work"
export APPDIR=$appdir TMPDIR=$work/tmp OUTPATH=$work
export MAIN_BIN=bloodborne DESKTOP=$work/bloodborne.desktop ICON=$root/launcher/bloodborne.png
export DEPLOY_PYTHON=1 DEPLOY_GTK=1 GTK_DIR=gtk-4.0 DEPLOY_SDL=1 DEPLOY_VULKAN=1 DEPLOY_PIPEWIRE=1
# Strace mode starts the programs to find what they dlopen: the game needs its game files.
export STRACE_MODE=0
export OUTPUT_APPIMAGE=1
"$quick" \
    "$root/out/bb-probe" "$root/out/bb-gpu-capabilities" \
    "$(command -v python3)" "$(command -v vulkaninfo)" \
    /usr/lib/libgtk-4.so* /usr/lib/libadwaita-1.so* /usr/lib/libgirepository-*.so* \
    "$pydyn"/_ssl.*.so "$pydyn"/_hashlib.*.so "$pil"/_imaging.*.so "$pil"/_imagingft.*.so

mkdir -p "$root/dist"
mv -f "$work"/*.AppImage "$root/dist/Bloodborne-bbport-x86_64.AppImage"
ls -lh "$root/dist/Bloodborne-bbport-x86_64.AppImage"
