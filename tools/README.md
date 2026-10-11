# Tools

Most of these come from [bbport](https://github.com/deadinside28/bloodborne_pc) and are kept as
they are, so that its updates merge cleanly. Only the first group matters to someone who builds
and plays the port; the rest are deadinside28's development tools.

## Used by the build, the launcher or the AppImage

| Tool | What it does |
|---|---|
| `gpu_capabilities.c` | Built by `build.sh` as `out/bb-gpu-capabilities`: the launcher's lists of gamepads and monitors, reading a key or button for the controls, and the GPU that `run.sh` picks the memory model by. |
| `fetch_fsr4_assets.sh` | Downloads AMD's FSR 4 assets (`fsr4_shaders/`) the FSR 4 upscaler needs. The AppImage build runs it. |
| `fsr4_optimize.sh` | Run by `run.sh`: faster, bit-exact versions of FSR 4 passes, rewritten with `fsr4_post_lds.pl`, `fsr4_pass11_guard.pl` and `Fsr4SpirvCrossFixes.pm`. |
| `fsr4cap/` | FSR 4.1.1 from your own AMD DLL: records the DLL under Proton and extracts its passes (`fsr4_411/`). The launcher's **Choose DLL…** button runs `fsr4cap/build_assets.sh`. |
| `build_dlss.sh` | DLSS on NVIDIA RTX: fetches what it needs from NVIDIA's DLSS SDK and builds the bridge. Run once after `build.sh` (this fork). |
| `shadnet-server/` | A private shadNet server for co-op, in Docker: [docs/SERVER.md](../docs/SERVER.md) (this fork). |
| `extract_prompt_assets.py` | Rebuilds `assets/menu_prompts/` (the Xbox and Switch button prompts) from Dommo's mods; only needed to update them (this fork). |

## Development: running and measuring the game

They start the game from `run.sh`, drive it and collect statistics. They expect a desktop where
the game can be watched and driven: `shot.sh` uses Hyprland's `hyprctl` and `grim`.

| Tool | What it does |
|---|---|
| `restart.sh`, `stop_own.sh` | Start the game with frame statistics and a scripted gamepad; close the one they started. |
| `press.sh` | Presses buttons of that scripted gamepad. |
| `shot.sh`, `frame.sh` | A screenshot of the game window; the game's next frame as a PNG. |
| `visual.sh`, `soak.sh`, `soak_walk.sh` | Enter the level and capture frames, or play for a while to check that the game keeps running. |
| `bench.sh`, `ab.sh`, `play_ab.sh` | Benchmarks and A/B comparisons of settings while the game runs. |
| `load_watch.sh` | GPU, CPU and memory load while the game runs, to see what holds the frame rate. |

## Development: upscaler, GPU and reverse engineering

| Tool | What it does |
|---|---|
| `fsr4_verify.sh` | Runs the FSR 4 benchmark with AMD's passes and the optimized ones: their output must match, and it prints their times. |
| `dump_view.py`, `mv_check.py` | Turn the upscaler's dumps into PNGs; check the motion vectors in them. |
| `host_import_probe.c`, `sparse_host_probe.c` | Probes of what the Vulkan driver supports for the new memory model. |
| `bridge_helper/` | A prototype of sharing GPU memory with a program under Wine. |
| `got_import.py` | Names the import behind an address of the game's executable. |
| `re/` | Reverse engineering of the game's graphics code; `gen_gnm_table.py` generates `gpu/shim/bbport_gnm_table.inc`. |

Each one's first lines say how to use it.
