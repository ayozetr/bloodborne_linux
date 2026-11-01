#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
if [[ ${1:-} == --software ]]; then
    shift
    if [[ -z ${VK_DRIVER_FILES:-} ]]; then
        for candidate in /run/opengl-driver/share/vulkan/icd.d/lvp_icd*.json /usr/share/vulkan/icd.d/lvp_icd*.json; do
            if [[ -f $candidate ]]; then export VK_DRIVER_FILES=$candidate; break; fi
        done
    fi
    if [[ -z ${VK_DRIVER_FILES:-} ]]; then echo 'Lavapipe not found; set VK_DRIVER_FILES.' >&2; exit 1; fi
    export VK_LOADER_LAYERS_DISABLE='~implicit~'
fi
# BB_PREBUILT=1 (packaged builds, the AppImage): out/bb-probe and its GPU library are installed
# next to this script; nothing is built and no nix-shell is needed.
# BB_DATA_DIR: writable directory for the generated files (out/), saves (user/) and bbport.ini;
# by default this directory.
data=${BB_DATA_DIR:-.}
out=$data/out
mkdir -p "$out"
export BB_CONFIG=${BB_CONFIG:-$data/bbport.ini}
# GPU paths are initialized when libbbgpu is loaded, before bbgpu_init receives --user.
# Select the same user directory now, including for an AppImage or a separate save profile.
export BB_GPU_USER_DIR=${BB_GPU_USER_DIR:-${BB_USER_DIR:-$data/user}}
# The drivers' own shader caches keep compiled pipelines between sessions (the port's cache gives
# them the shaders again at startup): NVIDIA's without its cleanup and with room for the game's
# pipelines (as Steam sets it), Mesa's with more room than its default.
export __GL_SHADER_DISK_CACHE=${__GL_SHADER_DISK_CACHE:-1}
export __GL_SHADER_DISK_CACHE_SKIP_CLEANUP=${__GL_SHADER_DISK_CACHE_SKIP_CLEANUP:-1}
export __GL_SHADER_DISK_CACHE_SIZE=${__GL_SHADER_DISK_CACHE_SIZE:-10737418240}
export MESA_SHADER_CACHE_MAX_SIZE=${MESA_SHADER_CACHE_MAX_SIZE:-4G}
mkdir -p "$BB_GPU_USER_DIR"
# FSR 4.1.1 assets (tools/fsr4cap/build_assets.sh): next to run.sh or in the data directory.
if [[ -z ${BB_FSR411_DIR:-} && ! -d fsr4_411 && -d $data/fsr4_411 ]]; then
    export BB_FSR411_DIR=$data/fsr4_411
fi
if [[ -z ${BB_PREBUILT:-} && -z ${BB_IN_NIX_SHELL:-} ]] && ! { command -v pkg-config >/dev/null && pkg-config --exists vulkan sdl3; } && command -v nix-shell >/dev/null; then
    args=''; if (( $# )); then args=$(printf '%q ' "$@"); fi
    exec env BB_IN_NIX_SHELL=1 nix-shell shell.nix --run "bash run.sh $args"
fi
# BB_SAVE_LOG=1 (launcher: "Save the log and statistics to a file"): this run's output and its
# per-frame statistics also go to $data/logs/<time>.log, .frames.csv and .readbacks.csv.
if [[ ${BB_SAVE_LOG:-} == 1 ]]; then
    logs=$data/logs
    mkdir -p "$logs"
    printf -v stamp '%(%Y%m%d_%H%M%S)T' -1
    export BB_FRAME_STATS=1 BB_FRAME_LOG=${BB_FRAME_LOG:-$logs/$stamp.frames.csv}
    export BB_READBACK_LOG=${BB_READBACK_LOG:-$logs/$stamp.readbacks.csv}
    echo "Log: $logs/$stamp.log"
    # A descriptor bash picks (10 and up), not 3: the AppImage's runtime keeps its mount for as
    # long as the program holds an inherited pipe (the first free descriptor, 3); with --play
    # this script replaced the launcher, and closing that pipe unmounted the store under it
    # ("python3: Software caused connection abort").
    exec {log_fd}>"$logs/$stamp.log"
    # Bash builtins only (the AppImage's PATH has no tee).
    exec > >(while IFS= read -r line || [[ -n $line ]]; do printf '%s\n' "$line"; printf '%s\n' "$line" >&$log_fd; done) 2>&1
fi
# The port's version (VERSION, issue #307), first in every log, with the build: the commit, branch
# and date from packaging/appimage-sharun.sh's BUILD file, or git's commit and branch in a checkout
# (a test build is a branch other than main), as issue reports rarely say which build they ran.
# Bash builtins only (the AppImage's PATH has no tee).
bb_build=''
if [[ -f BUILD ]]; then
    IFS= read -r bb_build < BUILD || true
elif [[ -d .git || -f .git ]] && command -v git >/dev/null; then
    bb_build="$(git rev-parse --short=8 HEAD 2>/dev/null)$(git diff --quiet HEAD 2>/dev/null || echo -modified) $(git rev-parse --abbrev-ref HEAD 2>/dev/null) (git checkout)" || true
fi
# The Linux fork's version (launcher/bbport_update.py), with bbport's it is built on.
bb_version=
if [[ -f launcher/bbport_update.py ]]; then
    while IFS= read -r line; do
        if [[ $line =~ ^VERSION\ =\ \"([^\"]+)\" ]]; then bb_version=${BASH_REMATCH[1]}; break; fi
    done < launcher/bbport_update.py
fi
if [[ -n $bb_version ]]; then
    echo "bbport Linux $bb_version${bb_build:+, build $bb_build} (bbport $(<VERSION))"
elif [[ -f VERSION ]]; then
    echo "bbport $(<VERSION)${bb_build:+, build $bb_build}"
fi
if [[ -z ${PYTHON:-} ]]; then
    PYTHON=$(command -v python3 || true)
    if [[ -z $PYTHON ]]; then
        for candidate in /nix/store/*-python3-*/bin/python3; do
            if [[ -x $candidate ]]; then PYTHON=$candidate; break; fi
        done
    fi
fi
if [[ -z ${PYTHON:-} ]]; then echo 'Install Python 3 or set PYTHON.' >&2; exit 1; fi
# BB_GAME_DIR: the game's folder (eboot.bin, sce_module, ...); default next to this directory.
game=${BB_GAME_DIR:-../CUSA03173}
if [[ ! -f $game/eboot.bin ]]; then echo "No eboot.bin in $game (set BB_GAME_DIR)." >&2; exit 1; fi
original_game=$game
# Field of view (bbport.ini fov, degrees; unset or 43 the game's): the camera table with every
# camera's field of view scaled, a layer under the mods (a mod's own camera table wins). Optional:
# without it the game keeps its own (scripts/fov.py).
ui_mods=$("$PYTHON" scripts/fov.py "$game" --out "$out/fov" --config "$BB_CONFIG") || ui_mods=
# Seamless co-op's kit items (the Hunt, Kin, Bloodlust and Duel Bells, the Parting Blank) get their
# names from BBSC while it runs; with Seamless co-op off (or The Hunter's Dream, which has no BBSC)
# this layer names them in the game's item texts, in slots the game leaves empty, so a save made
# with BBSC shows them by name (scripts/bbsc_kit_texts.py). Optional, like the others.
bbsc_on=0; [[ ${BB_BBSC:-0} == 1 && ${BB_ONLINE:-0} == 1 && ${BB_NET_BACKEND:-} != thd ]] && bbsc_on=1
kit_layer=$("$PYTHON" scripts/bbsc_kit_texts.py "$game" --out "$out/bbsc-kit" --bbsc "$bbsc_on") || kit_layer=
if [[ -n $kit_layer ]]; then ui_mods=${ui_mods:+$ui_mods:}$kit_layer; fi
# The gestures menu without the motion-control icons (the launcher's switch, Dommo's mod):
# BB_GESTURES_NO_MOTION=1, a layer under the mods (scripts/gestures_menu.py). Optional.
gestures_layer=$("$PYTHON" scripts/gestures_menu.py "$game" --out "$out/gestures" \
    --on "${BB_GESTURES_NO_MOTION:-0}") || gestures_layer=
if [[ -n $gestures_layer ]]; then ui_mods=${ui_mods:+$ui_mods:}$gestures_layer; fi
game=$("$PYTHON" scripts/mods.py "$game" --out "$out" \
    --mods-dir "${BB_MODS_DIR:-$data/mods}" --config "${BB_MODS_CONFIG:-$data/mods.json}" \
    --enabled "${BB_MODS_ENABLED:-1}" --ui-mods "$ui_mods" \
    --saves "${BB_USER_DIR:-$data/user}/savedata" --state "$data/mods.last")
# A private merged view lasts for this launch, including restarts. Cleanup only our own view.
if [[ $game != "$(realpath "$original_game")" ]]; then
    mod_game=$game
    trap '"$PYTHON" -c '\''import shutil,sys; shutil.rmtree(sys.argv[1])'\'' "$mod_game"' EXIT
fi
"$PYTHON" scripts/prepare.py "$game" --out "$out"
"$PYTHON" scripts/link_libc.py "$game" --out "$out"
"$PYTHON" scripts/link_modules.py "$game" --out "$out"
# BB_DLC_DIR (the launcher's DLC folder): the dumped add-ons of this title, one folder each (e.g.
# SPEXPANSIONDLC03). The runtime reports <user>/addcont/<title id>/<label> as installed (shadPS4's
# layout), so the folder is linked there; a real folder already in its place is left alone.
if [[ -n ${BB_DLC_DIR:-} && -d $BB_DLC_DIR ]]; then
    title=$("$PYTHON" -c 'import sys; sys.path.insert(0, "scripts"); from prepare import sfo
print(sfo(open(sys.argv[1] + "/sce_sys/param.sfo", "rb").read()).get("TITLE_ID", ""))' "$game" 2>/dev/null) || title=
    addcont=${BB_USER_DIR:-$data/user}/addcont
    if [[ $title =~ ^[A-Z]{4}[0-9]{5}$ && ( ! -e $addcont/$title || -L $addcont/$title ) ]]; then
        mkdir -p "$addcont"
        ln -sfn "$(realpath "$BB_DLC_DIR")" "$addcont/$title"
    fi
fi
"$PYTHON" scripts/content_profile.py "$game" --out "$out" --sku "${BB_CONTENT_SKU:-full}"
# Sizes chosen below for the previous launch are recomputed after an in-game restart.
if [[ ${BB_AUTO_RENDER_RES:-} == 1 ]]; then
    unset BB_RENDER_RES BB_OUTPUT_RES BB_AUTO_RENDER_RES
fi
# BB_RENDER_RES=WxH explicitly sets the game's render resolution (a patch at start).
# Frame rate: BB_FPS=uncap (default; hooks in the game's code, gpu/shim/bbport_frame_rate.cpp:
# each frame's real time; vblank 480 Hz, frames shown at once; BB_FRAME_HOOKS=0: the patches),
# 60/90 (the same hooks, at most 60/90 frames a second) or 30 (the game's own). BB_PATCHES adds
# patch names ("a;b").
fps=${BB_FPS:-uncap}
# bbport.ini output_res other than 1080p (720p for the Steam Deck, 1440p, 2160p): the whole game
# renders at the preset's size of the output (a patch), the upscaler fills the output, the UI is
# drawn at the output size. Preset and output changes need a restart.
# Live resolution changes keep the guest at 1920x1080 and scale host targets at run time instead
# (output and presets change in the menu without a restart). Over the startup patch below
# (BB_LIVE_HYBRID) they are always on; BB_LIVE_RES=0 turns them off for tests.
# The GPU tools (bb-gpu-capabilities: the game's GPU, its live resolution support).
if [[ -n ${BB_PROBE:-} ]]; then caps=$(dirname -- "$BB_PROBE")/bb-gpu-capabilities
elif [[ -n ${BB_PREBUILT:-} ]]; then caps=bin/bb-gpu-capabilities
else caps=out/bb-gpu-capabilities; fi
# output_res=auto (and no key, the default): the monitor's resolution, the chosen one (BB_DISPLAY:
# its name or number) or the primary. Bash builtins only (the AppImage's PATH has no sed/grep).
output_setting=auto
if [[ -f $BB_CONFIG ]]; then
    while IFS= read -r line || [[ -n $line ]]; do
        [[ $line =~ ^output_res=(.*)$ ]] && output_setting=${BASH_REMATCH[1]}
    done < "$BB_CONFIG"
fi
if [[ $output_setting == auto && -z ${BB_MONITOR_SIZE:-} ]]; then
    number=0
    while IFS=$'\t' read -r name size primary; do
        number=$((number + 1))
        if [[ -n ${BB_DISPLAY:-} ]]; then
            [[ $name == "$BB_DISPLAY" || $number == "$BB_DISPLAY" ]] && BB_MONITOR_SIZE=$size
        elif [[ $primary == 1 ]]; then
            BB_MONITOR_SIZE=$size
        fi
    done < <("$caps" --displays 2> /dev/null)
    [[ ${BB_MONITOR_SIZE:-} =~ ^[1-9][0-9]*x[1-9][0-9]*$ ]] && export BB_MONITOR_SIZE &&
        echo "Output: the monitor's resolution, ${BB_MONITOR_SIZE} (output_res=auto)"
fi
# The game's larger heaps (patches.py: "Increased Graphics Heap Sizes" for a scene above 1920x1080)
# need more direct memory; the game sizes its heaps by what it is given, and with the GPU using
# its memory in place all of it is resident: only then (a smaller scene left 3.5 GiB more RAM
# in use for nothing).
large_scene_memory() {
    local w=${1%x*} h=${1#*x}
    [[ $w =~ ^[0-9]+$ && $h =~ ^[0-9]+$ ]] && (( w * h > 1920 * 1080 )) && export BB_DMEM_MB=${BB_DMEM_MB:-9152}
    return 0
}
if [[ -z ${BB_RENDER_RES:-} ]]; then
    read -r scaled_render scaled_output < <("$PYTHON" scripts/patches.py --print-scaled --settings "$BB_CONFIG") || true
fi
live=0
# 1080p output: the live path always ran there. Over the startup patch (BB_LIVE_HYBRID) a preset
# below Native AA gets the game's targets at its size too.
if [[ -z ${scaled_output:-} && -z ${BB_RENDER_RES:-} && ${BB_LIVE_HYBRID:-1} == 1 ]]; then
    read -r hybrid_render hybrid_output < <("$PYTHON" scripts/patches.py --print-scaled --align 8 --settings "$BB_CONFIG") || true
    [[ -n ${hybrid_output:-} ]] && live=1 scaled_output=$hybrid_output scaled_render=$hybrid_render
fi
# Live changes are always on (they cost nothing over the startup patch); BB_LIVE_RES=0 (tests):
# the startup patch alone, presets change after a restart.
if [[ -n ${scaled_output:-} && $live != 1 ]]; then
    live=${BB_LIVE_RES:-1}
    [[ $live == 1 ]] || live=0
fi
# Live changes run over the startup patch (BB_LIVE_HYBRID): the game's targets get the launch
# preset's size, so a frame costs what it costs without live changes; another preset chosen in
# the game is drawn through proxies until the next start. BB_LIVE_HYBRID=0: the game's targets
# stay 1920x1080 and every preset goes through proxies (slower: on a Steam Deck 30 FPS against 44).
if [[ $live == 1 && ${BB_LIVE_HYBRID:-1} == 1 ]]; then
    read -r scaled_render scaled_output < <("$PYTHON" scripts/patches.py --print-scaled --align 8 --settings "$BB_CONFIG") || true
    export BB_RENDER_RES=$scaled_render BB_OUTPUT_RES=$scaled_output BB_AUTO_RENDER_RES=1 BB_LIVE_HYBRID=1
    large_scene_memory "$scaled_render"
    echo "Output ${scaled_output}: scene ${scaled_render}, live preset changes over it (BB_LIVE_HYBRID=0: proxies only)"
elif [[ $live == 1 ]]; then
    echo "Output ${scaled_output}: live resolution changes (BB_LIVE_HYBRID=0: proxies only)"
elif [[ -n ${scaled_output:-} ]]; then
    export BB_RENDER_RES=$scaled_render BB_OUTPUT_RES=$scaled_output BB_AUTO_RENDER_RES=1
    large_scene_memory "$scaled_render"
    echo "Output ${scaled_output}: scene ${scaled_render}, direct memory ${BB_DMEM_MB:-5056} MiB (BB_LIVE_RES=0: no live changes)"
fi
# bbport (Linux fork): an explicit render size (BB_RENDER_RES by hand) above 1080p skips the scaled
# path above, but patches.py still grows the graphics heaps for it: the direct memory follows, or
# the game stops at start (exit 139).
if [[ -n ${BB_RENDER_RES:-} && ${BB_AUTO_RENDER_RES:-0} != 1 ]]; then
    large_scene_memory "${BB_RENDER_RES// /}"
    [[ -n ${BB_DMEM_MB:-} ]] && echo "Render ${BB_RENDER_RES}: direct memory ${BB_DMEM_MB} MiB"
fi
# Texture packs (upscaled map textures, baked into the game folder or from the mods folder) fill
# the game's graphics heaps where the retail game fits: its GPU allocations fail, textures flicker,
# then it crashes (139 at Iosefka's Clinic, #240). They get the full larger heaps and the direct
# memory those need. scripts/game_check.py finds a map texture larger than the retail game's
# (once, kept in out/); BB_LARGE_HEAPS=1/0 forces it on or off.
large_heaps=${BB_LARGE_HEAPS:-} pack=
if [[ $large_heaps != [01] ]]; then
    read -r large_heaps pack < <("$PYTHON" scripts/game_check.py --texture-pack "$game" "$out/texture-pack.json") || true
    [[ $large_heaps == 1 ]] || large_heaps=0
fi
if [[ $large_heaps == 1 ]]; then
    export BB_DMEM_MB=${BB_DMEM_MB:-9152}
    echo "Graphics heaps: larger (${pack:-BB_LARGE_HEAPS=1}), direct memory ${BB_DMEM_MB} MiB (BB_LARGE_HEAPS=0: the game's own sizes)"
fi
"$PYTHON" scripts/patches.py --out "$out" --fps "$fps" --extra "${BB_PATCHES:-}" --settings "$BB_CONFIG" --game-dir "$game" --render-res "${BB_RENDER_RES:-}" --output-res "${BB_OUTPUT_RES:-}" \
    --patches-dir "${BB_PATCHES_DIR:-$data/patches}" --patches-config "${BB_PATCHES_CONFIG:-$data/patches.json}" --large-heaps "$large_heaps"
# Memory model and translation: the only one there is (0.7). The GPU uses the game's memory where
# it is (GPU-visible system memory: dma-buf chunks or imported host memory) and keeps the data it
# reads often in VRAM through the layer's memory module (no sparse binding; BB_LAYER_MEMORY=0:
# AMD's sparse arena); the command processor's work is translated rather than emulated.
# The game's GPU (vendor ID and name), for the choices below that depend on it.
gpu_vendor= gpu_name=
if [[ ${BB_AUTO_NOHIZ:-1} != 0 && -z ${RADV_DEBUG:-} ]]; then
    IFS=$'\t' read -r gpu_vendor gpu_name < <("$caps" --device 2> /dev/null) || true
fi
# GCN 3-5 under RADV (Polaris, Vega and their APUs): with HiZ, depth compression showed black
# halos and missing geometry (issues #54, #99); RADV_DEBUG=nohiz fixed it at some cost. Set
# unless RADV_DEBUG is the user's, BB_AUTO_NOHIZ=0: off.
if [[ ${BB_AUTO_NOHIZ:-1} != 0 && -z ${RADV_DEBUG:-} && $gpu_name == *"(RADV "* ]]; then
    for chip in TONGA ICELAND CARRIZO FIJI STONEY POLARIS VEGA RAVEN RENOIR; do
        if [[ $gpu_name == *"(RADV $chip"* ]]; then
            export RADV_DEBUG=nohiz
            echo "RADV: $gpu_name: RADV_DEBUG=nohiz (depth compression artifacts on GCN 3-5; BB_AUTO_NOHIZ=0: off)"
            break
        fi
    done
fi
# MangoHud (launcher switch: MANGOHUD=1) must be drawn once. Two overlays on top of each other
# showed doubled, offset text: the Steam Deck's performance overlay (mangoapp, game mode) plus the
# in-game layer, or the AppImage's bundled layer plus a system MangoHud (the layer names differ,
# so the Vulkan loader loads both).
if [[ ${MANGOHUD:-0} == 1 ]]; then
    if pgrep -x mangoapp > /dev/null 2>&1; then
        echo "MangoHud: Steam's performance overlay is on; the in-game MangoHud stays off"
        unset MANGOHUD
        export DISABLE_MANGOHUD=1
    elif grep -qs '"VK_LAYER_MANGOHUD' /usr/share/vulkan/implicit_layer.d/*.json \
            /etc/vulkan/implicit_layer.d/*.json \
            "${XDG_DATA_HOME:-$HOME/.local/share}"/vulkan/implicit_layer.d/*.json; then
        # The system's own MangoHud (and its config) is used; the bundled one is skipped.
        export VK_LOADER_LAYERS_DISABLE=${VK_LOADER_LAYERS_DISABLE:+$VK_LOADER_LAYERS_DISABLE,}VK_LAYER_MANGOHUD_overlay_64_x86_64
    fi
fi
# The command buffers of each submission are copied when the game submits them and decoded from
# the copy: while an area loads the game reused that memory before the GPU thread got to it
# ("Unimplemented PM4 type 0" a few seconds after loading a save). 0 decodes guest memory.
export BB_COPY_GPU_BUFFERS=${BB_COPY_GPU_BUFFERS:-1}
# A guest write next to small GPU outputs the GPU is still writing (counters, compute results,
# up to BB_GPU_WRITE_TWINS_MAX bytes per page) does not wait for the GPU (BufferCache twins).
export BB_GPU_WRITE_TWINS=${BB_GPU_WRITE_TWINS:-1} BB_GPU_WRITE_TWINS_MAX=${BB_GPU_WRITE_TWINS_MAX:-65536}
if [[ -z ${BB_VBLANK_HZ:-} ]]; then
    case $fps in uncap) export BB_VBLANK_HZ=1000 ;; 90) export BB_VBLANK_HZ=90 ;; *) export BB_VBLANK_HZ=60 ;; esac
fi
# FSR 4: faster post passes next to the downloaded ones (incremental; tools/fsr4_optimize.sh).
if [[ -z ${BB_PREBUILT:-} && -d fsr4_shaders ]] && command -v spirv-cross >/dev/null; then
    bash tools/fsr4_optimize.sh || echo 'FSR 4: optimized post passes not built' >&2
fi
if [[ -n ${BB_PREBUILT:-} ]]; then
    probe=${BB_PROBE:-bin/bb-probe}
else
    bash build.sh
    probe=${BB_PROBE:-out/bb-probe}  # BB_PROBE: a wrapper (gdb) around it
fi
# Steam Input (Linux fork issue #12): Steam sends its virtual controller's input only while it
# sees the game's window focused, and on a Wayland desktop it only sees X11 windows. A native
# Wayland window got nothing from the controller; through Xwayland it works. Only when Steam made a
# virtual controller for the game and SDL_VIDEO_DRIVER is not set (BB_STEAM_INPUT_X11=0: keep
# Wayland).
if [[ -z ${SDL_VIDEO_DRIVER:-} && -n ${WAYLAND_DISPLAY:-} && -n ${DISPLAY:-} \
        && ${BB_STEAM_INPUT_X11:-1} != 0 && ${SDL_GAMECONTROLLER_ALLOW_STEAM_VIRTUAL_GAMEPAD:-0} == 1 ]] \
        && grep -qs '^\[slot' "${SteamVirtualGamepadInfo:-}"; then
    echo "Window: X11 (Xwayland), so Steam Input reaches the game (BB_STEAM_INPUT_X11=0: Wayland)"
    export SDL_VIDEO_DRIVER=x11
fi
# The Xbox and Switch button art for the live button prompts (scripts/prompt_art.py): without it
# (Pillow missing) those pads' prompts are letters.
if prompt_art=$("$PYTHON" scripts/prompt_art.py --out "$out/prompt_art") && [[ -n $prompt_art ]]; then
    export BB_PROMPT_ART=$prompt_art
fi
# Trophies (scripts/trophies.py): the dump's list and icons in the user directory, for the
# runtime's notices and the launcher; BB_TROPHY_KEY (the PS4's trophy key) decrypts the names.
if trophies=$("$PYTHON" scripts/trophies.py prepare --game "$original_game" \
        --user "${BB_USER_DIR:-$data/user}" --language "${BB_LANGUAGE:-1}") && [[ -n $trophies ]]; then
    export BB_TROPHY_DIR=$trophies
fi
# Online play (BB_ONLINE=1, launcher: Online; the online module gpu/bbnet20): the game's own server
# goes to the community server, summon signs to the shadNet WebAPI (scripts/online.py).
if [[ ${BB_ONLINE:-0} == 1 && -f scripts/online.py ]]; then
    # The shadPS4 0.20 module (gpu/bbnet20) answers both pools: Seamless Hunt (shadNet with BBSC) and
    # The Hunter's Dream (BB_NET_BACKEND=thd, without BBSC).
    if [[ ${BB_NET_BACKEND:-} == thd ]]; then
        unset BB_BBSC
    fi
    if [[ -z ${BB_NET_MODULE:-} ]]; then
        if [[ -n ${BB_PREBUILT:-} ]]; then BB_NET_MODULE=$PWD/bin/gpu/libbbnet20.so; else BB_NET_MODULE=$PWD/out/gpu/libbbnet20.so; fi
        export BB_NET_MODULE
    fi
    export BB_SHADNET_SERVER=${BB_SHADNET_SERVER:-play.seamlesshunt.com:31313}
    # HTTPS needs CA certificates: OpenSSL from Nix looks only in its own store path (the
    # packaged wrapper brings a bundle; from source the system's is taken).
    if [[ ! -r ${SSL_CERT_FILE:-} ]]; then
        for bundle in "${NIX_SSL_CERT_FILE:-}" /etc/ssl/certs/ca-certificates.crt /etc/pki/tls/certs/ca-bundle.crt /etc/ssl/cert.pem /etc/ssl/ca-bundle.pem; do
            [[ -n $bundle && -r $bundle ]] && { export SSL_CERT_FILE=$bundle; break; }
        done
    fi
    [[ -n ${BB_SHADNET_WEBAPI:-} ]] || export BB_SHADNET_WEBAPI=http://${BB_SHADNET_SERVER%:*}:31315
    # BBSC: its game server on this PC when the server's own does not answer (online.py
    # bbsc-local). It lives as long as the game: a watcher stops it when this process (exec'd into
    # the game below) is gone. Messages and bloodstains are then this PC's only.
    if [[ ${BB_BBSC:-0} == 1 && -f scripts/bbsc_gameserver/bbsc_gameserver.py ]]; then
        bbsc_shadnet=$("$PYTHON" scripts/online.py bbsc-local) || bbsc_shadnet=
        if [[ -n $bbsc_shadnet ]]; then
            bbsc_dir=${BB_USER_DIR:-$data/user}/bbsc
            mkdir -p "$bbsc_dir/logs"
            game_pid=$$
            if ! (exec 3<>/dev/tcp/127.0.0.1/20443) 2>/dev/null; then
                ( "$PYTHON" scripts/bbsc_gameserver/bbsc_gameserver.py --shadnet "$bbsc_shadnet" \
                      --host 127.0.0.1 --port 20443 --relay-port 0 --no-bbhost --no-playlog \
                      --data "$bbsc_dir/online-data.json" --log-dir "$bbsc_dir/logs" \
                      > "$bbsc_dir/logs/gameserver-console.log" 2>&1 &
                  server_pid=$!
                  while kill -0 "$game_pid" 2>/dev/null && kill -0 "$server_pid" 2>/dev/null; do sleep 2; done
                  kill "$server_pid" 2>/dev/null ) &
                echo "Co-op: BBSC game server on 127.0.0.1:20443 (summons -> $bbsc_shadnet:31315)"
            else
                echo "Co-op: a game server answers on 127.0.0.1:20443 already: used"
            fi
            export BB_COMMUNITY_SERVER=http://127.0.0.1
        fi
    fi
    user_data=${BB_USER_DIR:-$data/user}
    if [[ ${BB_NET_BACKEND:-} == thd ]]; then
        # The Hunter's Dream (bbhost's protocol): the account comes from the launcher's Discord sign-in.
        if [[ -z ${BB_THD_TOKEN:-} || -z ${BB_THD_ONLINE_ID:-} ]]; then
            echo "The Hunter's Dream: not signed in (launcher: Online -> Sign in with Discord)." >&2; exit 1
        fi
        thd_out=$("$PYTHON" scripts/online.py thd-overrides --user "$user_data") || exit 1
        SHADPS4_HTTP_HOST_OVERRIDES_JSON=$(sed -n 1p <<<"$thd_out")
        thd_base=$(sed -n 2p <<<"$thd_out")
        export SHADPS4_HTTP_HOST_OVERRIDES_JSON BB_THD_SERVER=${BB_THD_SERVER:-$thd_base:18671} BB_THD_AUTH=${BB_THD_AUTH:-$thd_base}
        unset BB_SHADNET_SERVER BB_SHADNET_WEBAPI BB_SHADNET_NPID BB_SHADNET_PASSWORD BB_SHADNET_TOKEN
    else
        SHADPS4_HTTP_HOST_OVERRIDES_JSON=$("$PYTHON" scripts/online.py overrides --user "$user_data") || true
        export SHADPS4_HTTP_HOST_OVERRIDES_JSON
    fi
fi
# Shader recipes (gpu/render/shader_rebuild.h): the shaders of the recorded game, translated for
# this GPU by a background process at start, the code read from the game's own files.
if [[ -z ${BB_SHADER_RECIPES+set} && -f shader_recipes.bin ]]; then
    export BB_SHADER_RECIPES=$PWD/shader_recipes.bin
fi
# Image shapes (gpu/textures/image_spares.h): the textures the game makes, so spares are made
# ahead from the first session on.
if [[ -z ${BB_IMAGE_SHAPES+set} && -f image_shapes.txt ]]; then
    export BB_IMAGE_SHAPES=$PWD/image_shapes.txt
fi
export BB_SHADER_GAME_DIR=${BB_SHADER_GAME_DIR:-$(realpath "$original_game")}
# Discord Rich Presence (launcher: Discord; BB_DISCORD=0 turns it off): $$ becomes the game
# below (exec), and the helper ends with it. The game writes its area and co-op partners into
# BB_PRESENCE_DIR (scripts/discord_presence.py), new for each start.
if [[ ${BB_DISCORD:-1} != 0 ]]; then
    BB_PRESENCE_DIR=$(cd -- "$out" && pwd)/presence; export BB_PRESENCE_DIR
    rm -rf "$BB_PRESENCE_DIR" && mkdir -p "$BB_PRESENCE_DIR"
    presence=(--pid $$ --presence-dir "$BB_PRESENCE_DIR")
    [[ ${BB_ONLINE:-0} == 1 ]] && presence+=(--online)
    "$PYTHON" scripts/discord_presence.py "${presence[@]}" </dev/null &
fi
# Steam overlay (#77, #217: Shift+Tab, Remote Play, the controller's Steam Input layout): the
# packaged entry (packaging/bbport-entry.c) keeps Steam's preload out of the launcher and names it
# in BB_STEAM_OVERLAY; the game alone loads it, with its Vulkan layer. BB_STEAM_OVERLAY=0: off.
# bbport (Linux fork): the sharun AppImage has no such entry, and sharun clears LD_PRELOAD in every
# program of the package: when Steam started the game and nothing named the overlay, Steam's
# 64-bit library is read from the nearest process above that still has it in its preload.
if [[ ${BB_STEAM_OVERLAY:-} != 0 && ! -f ${BB_STEAM_OVERLAY:-} && -n ${SteamGameId:-} ]]; then
    pid=$$
    while [[ ! -f ${BB_STEAM_OVERLAY:-} && $pid -gt 1 ]]; do
        preload=
        while IFS= read -r -d '' variable; do
            [[ $variable == LD_PRELOAD=* ]] && preload+=" ${variable#*=}"
        done 2>/dev/null < "/proc/$pid/environ" || true
        for library in ${preload//:/ }; do
            [[ $library == */ubuntu12_64/gameoverlayrenderer.so && -f $library ]] && BB_STEAM_OVERLAY=$library
        done
        { stat=$(< "/proc/$pid/stat"); } 2>/dev/null || break
        stat=${stat##*) }
        read -r _ pid _ <<< "$stat"
    done
    [[ -f ${BB_STEAM_OVERLAY:-} ]] ||
        echo "Steam overlay: Steam's 64-bit gameoverlayrenderer.so not found among the processes above" >&2
fi
if [[ -n ${BB_STEAM_OVERLAY:-} && $BB_STEAM_OVERLAY != 0 && -f $BB_STEAM_OVERLAY ]]; then
    export LD_PRELOAD=$BB_STEAM_OVERLAY ENABLE_VK_LAYER_VALVE_steam_overlay_1=1
    # sharun (the AppImage) passes LD_PRELOAD on only with this.
    export SHARUN_ALLOW_LD_PRELOAD=1
    unset DISABLE_VK_LAYER_VALVE_steam_overlay_1
    echo "Steam overlay: $BB_STEAM_OVERLAY"
    # Steam draws its overlay only on windows it can see: on a Wayland desktop, X11 ones (as
    # Steam Input above).
    if [[ -z ${SDL_VIDEO_DRIVER:-} && -n ${WAYLAND_DISPLAY:-} && -n ${DISPLAY:-} ]]; then
        echo "Window: X11 (Xwayland), so Steam's overlay shows on it"
        export SDL_VIDEO_DRIVER=x11
    fi
fi
probe_args=("$out/boot-linked.bin" --content-profile "$out/content.bin" --patches "$out/patches.bin" --app0 "$game" --user "${BB_USER_DIR:-$data/user}" --timeout "${BB_TIMEOUT:-0}" "$@")
if [[ -n ${mod_game:-} ]]; then
    "$probe" "${probe_args[@]}" &
    mod_pid=$!
    trap 'kill -TERM "$mod_pid" 2>/dev/null || true' TERM INT
    mod_status=0
    wait "$mod_pid" || mod_status=$?
    # An interrupted wait must finish the child before removing its mounted view.
    if kill -0 "$mod_pid" 2>/dev/null; then wait "$mod_pid" || mod_status=$?; fi
    exit "$mod_status"
fi
exec "$probe" "${probe_args[@]}"
