#!/usr/bin/env bash
# DLSS for NVIDIA RTX on Linux: fetches the files of the NVIDIA DLSS SDK it needs (headers, the
# static NGX loader and the DLSS library, ~60 MB, once into ~/.cache/bbport), builds the bridge
# (gpu/dlss_bridge, the only code that uses the SDK) and puts it with NVIDIA's DLSS library and
# license next to bb-probe (out/), where the port looks for them, as build.sh does with
# DLSS_SDK_ROOT. Without these files
# the port keeps its other upscalers. Needs the proprietary NVIDIA driver at run time.
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
version=310.9.1
sdk=${DLSS_SDK_ROOT:-${XDG_CACHE_HOME:-$HOME/.cache}/bbport/dlss-sdk-$version}
base=https://raw.githubusercontent.com/NVIDIA/DLSS/v$version
dlss=lib/Linux_x86_64/rel/libnvidia-ngx-dlss.so.$version
fetch() {
    [[ -s $sdk/$1 ]] && return
    mkdir -p "$(dirname "$sdk/$1")"
    curl -fsSL --retry 3 -o "$sdk/$1.part" "$base/$1"
    mv "$sdk/$1.part" "$sdk/$1"
}
headers=(nvsdk_ngx.h nvsdk_ngx_defs.h nvsdk_ngx_defs_vk.h nvsdk_ngx_defs_dlssd.h nvsdk_ngx_defs_dlssg.h
         nvsdk_ngx_helpers.h nvsdk_ngx_helpers_vk.h nvsdk_ngx_helpers_cuda.h nvsdk_ngx_helpers_d3d.h
         nvsdk_ngx_helpers_dlssd.h nvsdk_ngx_helpers_dlssd_vk.h nvsdk_ngx_helpers_dlssd_cuda.h
         nvsdk_ngx_helpers_dlssd_d3d.h nvsdk_ngx_helpers_dlssg.h nvsdk_ngx_helpers_dlssg_vk.h
         nvsdk_ngx_helpers_dlssg_d3d.h nvsdk_ngx_loader.h nvsdk_ngx_params.h nvsdk_ngx_params_dlssd.h
         nvsdk_ngx_params_dlssg.h nvsdk_ngx_standalone_common.h nvsdk_ngx_standalone_cuda.h
         nvsdk_ngx_vk.h)
for header in "${headers[@]}"; do fetch "include/$header"; done
fetch LICENSE.txt
fetch lib/Linux_x86_64/libnvsdk_ngx.a
echo "DLSS: NVIDIA DLSS $version library (~60 MB)…"
fetch "$dlss"
cmake -S gpu/dlss_bridge -B out/dlss-bridge -G Ninja -DCMAKE_BUILD_TYPE=Release \
    -DDLSS_SDK_ROOT="$sdk" > /dev/null
ninja -C out/dlss-bridge > /dev/null
rm -f out/libnvidia-ngx-dlss.so.* out/gpu/libbbport_dlss.so out/gpu/libnvidia-ngx-dlss.so.*
install -m755 out/dlss-bridge/libbbport_dlss.so out/
install -m755 "$sdk/$dlss" out/
install -m644 "$sdk/LICENSE.txt" out/NVIDIA-DLSS-LICENSE.txt
echo "DLSS ready: out/libbbport_dlss.so, out/${dlss##*/}"
