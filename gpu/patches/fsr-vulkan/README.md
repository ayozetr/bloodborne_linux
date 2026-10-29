# Local changes to gpu/third_party/fsr-vulkan

The submodule points at upstream FireBurn/FSR-Vulkan (`c64f093`). `build.sh` applies the
patches here to its working tree when they are not applied yet:

- `0001-...`: `BB_FSR4_PROFILE` (GPU time per FSR 4 pass) and `BB_FSR4_STATS` (driver
  statistics of each pass) in the FSR 4 v07 provider.
- `0002-...`: `aspectMask` in `FfxFsr4VkExternalImageState` (0 = color). The layout barriers
  of a registered external image named the color aspect, which is invalid for the
  D32_SFLOAT_S8_UINT depth image.
- `0003-...`: `findMemoryTypeIndex` never picks a protected memory type unless asked for.
  RADV lists device-local protected types after the plain ones on some GPUs (Ryzen Z1 Extreme /
  PHOENIX: ROG Ally, Legion Go), and FSR 3.1 put its resources there: full-screen colour noise.
  From upstream bbport 0.7 (by iannitram).
