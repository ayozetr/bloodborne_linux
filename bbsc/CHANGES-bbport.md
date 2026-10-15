# bbport's changes to BBSC

This folder holds [BBSC](https://github.com/Classmg22/BBSC) 0.0.1 by CLS_AMG (GPL-2.0-or-later),
as published at commit 315f76c, with the changes below made for the Linux port of bbport. Changed
lines in BBSC's own files are marked `bbport:` in comments.

## 2026-10-15

- **Linux build.** `CMakeLists.txt` builds `libbbsc.so`, which bb-probe loads into the game.
  - New files `emulator/mod/linux/`:
    - `bbsc_mod_linux.cpp`, which replaces `bbsc_mod.cpp`;
    - `bbsc_hooks_linux.cpp`, which replaces the Windows hook code;
    - `bbsc_win32.h`, the Win32 and Winsock names the mod uses.
  - Linux branches (`#ifdef`) in `emulator/mod/bbsc_relay.cpp`, `bbsc_channel.cpp` and
    `bbsc_http.cpp`.
- **Logs and captures.** BBSC keeps 5 of each, and stops a capture at 64 MB.
- **Data folder.** BBSC's files go in the game's user folder, not the working directory.
- **Memory search on Linux.** `emulator/src/core/bbsc_memscan.cpp` reads the readable mappings
  through `process_vm_readv`.
- **F8 key.** The F8 unstuck key works on Linux through SDL (`emulator/src/core/bloodborne_re.cpp`).
- **Saves.** `BBSC_SAVE_DIR` is set to bbport's save folder (`savedata/<user>/<title id>/SPRJ0005`).
- **Translations.** BBSC's texts follow the game's language:
  - `emulator/src/core/bbsc_i18n.{h,cpp}` and `bbsc_translations.inc`, generated from
    `translations/*.json` by `translations/gen_translations.py`;
  - in `emulator/src/core/bloodborne_re.cpp`, BBSC's texts are passed through them.
