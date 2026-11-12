# Local changes to gpu/third_party/fsr-vulkan

The submodule points at upstream FireBurn/FSR-Vulkan (`c64f093`). `build.sh` applies the
patches here to its working tree when they are not applied yet:

- `0001-...`: `BB_FSR4_PROFILE` (GPU time per FSR 4 pass) and `BB_FSR4_STATS` (driver
  statistics of each pass) in the FSR 4 v07 provider.
- `0002-...`: the FFX Vulkan backend never picks a protected memory type unless it asked for one.
  On RADV PHOENIX (Ryzen Z1 Extreme: ROG Ally, Legion Go) it picked one for FSR 3.1's
  device-local resources, and the scene was white or full of colored noise (#85). Also sent to
  FireBurn/FSR-Vulkan#1.
- `0003-...`: the port's hooks in the FFX Vulkan backend: `ffxVkShaderOverride` (its own SPIR-V
  for a pass, `gpu/upscale/ffx_shaders.cpp`) and `ffxVkJobMark` (a mark before each compute
  dispatch, `gpu/upscale/fg_profile.cpp`, `BB_FG_PROFILE`). 0.7 used them without this patch, so it
  did not link from source (upstream #404).
- `0004-...`: `aspectMask` in `FfxFsr4VkExternalImageState` (0 = color). The layout barriers of a
  registered external image named the color aspect, which is invalid for a depth image (the
  Linux fork's 0002).
- `0005-...`: the FSR 4 provider's table of external images (eight, matched by view) never let
  a record go, and the port makes new views whenever it recreates its images: after a few area
  loads every registration failed with `VK_ERROR_OUT_OF_POOL_MEMORY` and FSR 4 stopped (#50).
  The table is kept in order of use and a full one drops the record unused the longest.
