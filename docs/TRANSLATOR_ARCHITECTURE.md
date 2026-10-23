# Our own translator instead of shadPS4: structure and order of work (2026-10-10)

Goal: move away from emulation and from shadPS4 code. We want our own PS4 command translator and
our own graphics renderer that scale to other games (everything specific to one game lives in its
profile, `gpu/games/`) and behave the same on AMD and NVIDIA. After that comes shadnet (online play).

## Current state

Borrowed from shadPS4 (`gpu/VENDOR.txt`, commit b4e7ae7 from 2026-09-24): about 116k lines.

| Part | Lines | What it does | Our work in it |
|---|---|---|---|
| `video_core/amdgpu` | 8.3k | PM4 parsing (command processor `liverpool.cpp`), registers, tiling | GPU-side labels, occlusion, predication, PM4 self-test |
| `video_core/renderer_vulkan` | 28.6k | Vulkan renderer: pipelines, rasterizer, scheduler, presenter | draw pipeline (stages A/B), recording threads, upscalers, background compilation |
| `video_core/buffer_cache` | 7.4k | game memory for the GPU | almost all rewritten (memory module, VRAM copies, traps) |
| `video_core/texture_cache` | 4.8k | textures by address, detiling | time-based collector, uploads |
| `shader_recompiler` | 38.6k | GCN → IR → SPIR-V | paged buffers (BDA), fixes |
| `core`, `common` | 21.8k | VideoOut, GnmDriver, event queues, utilities | vblank, labels |

Our own code, outside shadPS4: `gpu/layer/` (memory module `BbLayer::GpuMemory`), `gpu/games/` (game
profiles), `gpu/shim/` (overlay, settings, hooks), the runtime in `src/` (kernel, libc, files, saves).

## Target structure

Modules with narrow interfaces. None of them knows addresses in the game's code (that belongs to the
profile), and none does the GPU's work on the CPU (that is emulation):

1. **memory**: game memory in place, VRAM copies as a cache, shared tracking of page protection
   (write traps for copies and textures). Exists: `layer/` + the module in `buffer_cache_layer.cpp`.
2. **cp**: command processor. Parses PM4 into the translator's command stream (state, draws,
   dispatches, synchronization) in the order the GPU executes it. Replaces `liverpool.cpp`.
3. **state**: context registers → pipeline keys and Vulkan dynamic state. Replaces
   `liverpool_to_vk` and the key building in `vk_pipeline_cache`.
4. **resources**: V#/T#/S# descriptors → buffers, images, samplers (caches, detiling). Replaces
   `buffer_cache`, `texture_cache` (the buffer part is already almost ours).
5. **render**: Vulkan. Command recording per thread, barriers, submission, presentation. Replaces
   `renderer_vulkan` (the scheduler and stages A/B are already ours).
6. **shaders**: GCN → SPIR-V. The largest part; it is replaced last, stage by stage (decoder,
   IR, passes, code generation).
7. **platform**: VideoOut, GnmDriver, kernel events (`core/libraries`), next to the runtime.
8. **games**: game profiles (exists).

## Order

One module is replaced at a time. First an interface in our code with the shadPS4 code behind it
as is, then our own implementation behind the same interface. After each step: the route (a route
benchmark script (not in this repository), frames and snapshots), the PM4 self-test
(`BB_PM4_SELFTEST=1`), unit tests, the game on AMD and (from tester logs) on NVIDIA.

| Step | What | Why in this order |
|---|---|---|
| 1 | memory: shared tracking of page protection; write traps under textures by default; model 0.3 and the sparse arena are removed | removes the rest of memory emulation and the dependency on game hooks |
| 2 | cp: the translator's command stream; `MEM_SEMAPHORE`, GPU time, compute queues done by the GPU | the last emulation left is in the command processor |
| 3 | state + resources | they build on 1 and 2; the buffer part is already ours |
| 4 | render | the scheduler and stages are already ours; the rasterizer and pipelines remain |
| 5 | shaders | the largest and riskiest; by then everything else is already ours |
| 6 | shadnet | networking, once the graphics are our own |

Steps 1 and 2 are the plan to move away from emulation
([`EMULATION_REMOVAL_PLAN.ru.md`](https://github.com/deadinside28/bloodborne_pc/blob/master/docs/EMULATION_REMOVAL_PLAN.ru.md),
section dated 2026-10-10).

## Progress

### 2026-10-10: our own PM4 decoder (step 2, start)

- `gpu/cp/`: our own code, without shadPS4. Packet format and opcodes (`cp_pm4.h`), register file and
  decoder (`cp_decoder.{h,cpp}`). The decoder walks the buffer in stream order, applies register
  packets (`SET_*_REG`, `CLEAR_STATE`, registers written by draw packets), descends into
  nested buffers and hands each packet to a "sink" (`BbCp::Sink`) with the state already applied:
  draws and dispatches as typed calls, the rest as packets. The sink decides `COND_EXEC`. The
  decoder knows nothing about Vulkan, the game or where execution happens.
- Unit test `tests/test_cp_decoder.cpp` (target `cp-decoder-test`): registers, partial writes,
  draws, dispatches, nested buffers, `COND_EXEC`, `CLEAR_STATE`, corrupt buffers.
- Register addresses are checked against the shadPS4 layout at build time (`static_assert`). This
  found a bug: on CIK, `CP_STRMOUT_CNTL` is in uconfig (`0xC03F`), not in config.
- Shadow check in the game (`BB_CP_SHADOW=1`): the new decoder parses every top-level buffer
  from the same state, and the register files are compared at the end of the buffer. On the route,
  all buffers matched (~800k buffers, ~200 million packets, 0 mismatches, 0 parse errors).
  Bloodborne does not use nested buffers (they are covered by the unit test).
- Next: the decoder as a cursor (packet by packet, so the command processor loop can yield to
  other queues while waiting), the register file as shared state storage (its layout matches
  shadPS4 `Regs` word for word), then moving packet handling from `liverpool.cpp` into the
  translator's sink one packet type at a time, each time with the shadow check and the route.

### 2026-10-10: the new decoder is the real parsing path

- The decoder became a cursor (`BbCp::Cursor`: packet by packet, nested buffers at the
  caller's choice). The register file can live in the owner's storage (for the command processor,
  its `regs`, with the same word layout). A write observer (`RegisterObserver`, one call per
  packet) provides what draw preparation needs: the written blocks and the packet checksum.
- `ProcessGraphics` takes packets and register writes from the cursor (`BB_CP_DECODER=0` selects
  the old walk). What each packet does is still the old code. PM4 self-test: 11 of 11. The share of
  prepared draws is the same (747k used, 19k not, versus 755k/24k), so the checksums
  match. The image is the same.
