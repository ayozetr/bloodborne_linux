# Layer memory module: PS4 GPU addresses without sparse (plan, 2026-10-09)

## Why

The new memory model keeps game memory in a single sparse arena and moves blocks between game
memory and VRAM by rebinding (`vkQueueBindSparse`). On NVIDIA (Linux, drivers ≥ 555), the bind
time grows with the number of pages already bound, and the call holds a global lock: each
move to VRAM cost seconds, and the game and the desktop froze (GTX 1660 Ti, 615.71). Without moves
(`BB_FIXED_ARENA=1`) it runs at 48.6 FPS versus ~205 on an RX 7800 XT. We need a model that works the
same on AMD, NVIDIA and Intel and is not tied to the shadPS4 buffer cache: part of a future layer
for running PS4 games.

## Idea

The PS4 GPU has its own virtual memory (GPUVM) on top of shared memory; every V#, T# and pointer in
user data is a virtual address. On PC we do the same with Vulkan 1.2 means (BDA):

- **Memory sources**: ordinary (non-sparse) Vulkan buffers:
  - chunks of game memory: dma-buf (AMD) or host memory import (NVIDIA, Intel), one chunk per
    game direct memory allocation (allocations are mapped whole, so a range inside one
    mapping is always contiguous within one chunk);
  - VRAM mirrors: segments aligned to game addresses (game page X sits in the segment at the
    same offset), allocated when the first VRAM page appears in the segment.
- **Page table** (a buffer on the GPU): page of a PS4 address → device address (BDA) of its
  current source. It is changed by a copy in the command stream, in order with draws, without semaphores.
- **Direct path**: the whole V# range is in one source (almost all bindings) → an ordinary
  descriptor (source buffer, offset, size). The shader translator does not change.
- **Paged path**: the range is mixed (≈85 huge bindings per frame: shaders bound
  to all of memory) → the descriptor points to a record {PS4 address, size}, and the shader
  translates each address through the table. A pipeline variant only for such bindings
  (specialization key).
- **Vertices, indices, indirect arguments, copies, texture uploads**: the direct path; otherwise,
  assembly into a contiguous temporary buffer (read-only) or per-page copies (the CPU knows the table).
- **Moving to VRAM and back**: the policy of the current new model (data whose writes we
  know about: loaders, the GPU; unknown writers stay in place), but the execution is a copy + a
  table write + choosing the source at bind time. Bindings recorded before a move read the old
  source, which is still valid; VRAM is freed once the GPU has passed those commands.

## Order of work

1. **Module core** (`gpu/layer/`, no dependencies on shadPS4): sources, pages, table,
   `Resolve(address, size)` → a direct source or "mixed", walking over sources for copies.
   The command recording interface is abstract (copy, table write), so it does not pull in the scheduler.
2. **Hook-up without VRAM**: the new model returns ranges in place through chunk buffers, not
   through the arena; the new model does not create the sparse arena. Expected: ~48 FPS on AMD (like
   `BB_FIXED_ARENA`), no `vkQueueBindSparse` at all. Check the image, then make a build for NVIDIA.
3. **VRAM mirrors + moves**: the policy from `BufferCache`, the page table, the paged path in
   shaders for mixed bindings. Goal: parity with the sparse arena on AMD (~205 FPS).
4. **NVIDIA/Intel**: a test build, a tester log; then remove sparse from the new model entirely.

Measurements: RX 7800 XT, standing still (`tools/bench.sh`), `BB_PC_MODEL=1`; diagnostics `BB_RESIDENCY_MIX=1`.

## Status (2026-10-09, morning)

- Steps 1–3 are done. On the RX 7800 XT, standing still: module ~205 FPS, sparse arena ~205–238, old model
  ~220 (at the lamp in the Hunter's Nightmare); in another spot (1170 draw calls): 167.5 / 164.5 / 146.
  `vkQueueBindSparse` is never called in module mode (counter in the `Layer memory:` line).
- Mixed bindings are solved without the paged path: "volatile" blocks (`layer_volatile`). A block with
  unknown bytes (the edge of a range, a gap between images) goes into the mirror together with
  the rest of the range, is refreshed from game memory before each binding, and whatever a dispatch
  wrote into it is copied back after the dispatch (`LayerAfterBindings`). The paged path remains for
  bindings of 64 MiB and larger. `BB_LAYER_VOLATILE=0` turns it off (for comparison).
- Default: AMD uses the sparse arena, other GPUs use the module (`BB_LAYER_MEMORY=1/0` to
  choose manually). Step 4 (NVIDIA): needs a tester log; the host memory import path cannot be
  checked on AMD (RADV does not import memfd).

## Addendum: original copying and portable labels (2026-10-09)

In the new module, the paged path of the original copy shader is fixed: writes update game memory and the current mirror; the native shader is now selected by default. For GPU labels, a standard Vulkan path without AMD buffer marker was added. The implementation, switches and verification limits are described in [TRANSLATION_GPU_COPY_LABELS.ru.md](https://github.com/deadinside28/bloodborne_pc/blob/master/docs/TRANSLATION_GPU_COPY_LABELS.ru.md). This removes the dependency of label writes on the AMD extension, but does not replace hardware testing on NVIDIA.
