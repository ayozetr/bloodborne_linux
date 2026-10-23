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
  through `process_vm_readv`, and through `/proc/self/mem` where that fails: on AMD the game's
  memory is a GPU dma-buf, and the item tables were never found there (no co-op kit).
- **F8 key.** The F8 unstuck key works on Linux through SDL (`emulator/src/core/bloodborne_re.cpp`).
- **Bell trace.** The responder bell trace also records the kit's Kin and Bloodlust Bells (4121,
  11201), not only the vanilla bells they replace (`emulator/src/core/bloodborne_re.cpp`).
- **The co-op kit, late.** The search for the item tables, which only appear once a character is
  loaded, no longer gives up after 3 minutes (`emulator/src/core/bloodborne_re.cpp`, StartBbscDuelBell).
- **Saves.** `BBSC_SAVE_DIR` is set to bbport's save folder (`savedata/<user>/<title id>/SPRJ0005`).
  On a first start, with no saves yet, it is the folder the game will write (`BB_SAVEDATA_TITLE`,
  from bbport's runtime), so the kit still comes.
- **Translations.** BBSC's texts follow the game's language:
  - `emulator/src/core/bbsc_i18n.{h,cpp}` and `bbsc_translations.inc`, generated from
    `translations/*.json` by `translations/gen_translations.py`;
  - in `emulator/src/core/bloodborne_re.cpp`, BBSC's texts are passed through them.

## 2026-10-19

- **A host's placement goes to the sign it rings** (bbport issue #17). BBSC 0.0.1 sent a host's
  placement to every player on the server, and a waiting guest followed the first host it heard
  from. On a busy server (12 hosts on Seamless Hunt in one session) a guest followed a stranger:
  its sign went to that stranger's map, its friend never found it, and a stranger could summon it
  despite the password. BBSC's own `bbsc.dll` of 2026-10-17 (no source published yet) changed
  the protocol; this is the same protocol, reimplemented from that binary
  (`emulator/mod/bbsc_http.cpp`, `emulator/mod/bbsc_relay.cpp`):
  - a guest keeps the `UserId` its sign is created under;
  - a host ringing a sign (`/summon_messenger/request` with a `TargetUserId`) sends its placement
    to that user only: relay frame `"SHAD"` 0x31 + `"<TargetUserId>|<placement>"`, and the
    placement header to the broker;
  - a guest takes only a placement sent to its own sign, and keeps it 90 s (20 s otherwise);
  - placements sent to the whole server (0x30) are ignored, as BBSC's newer builds do;
  - nothing is sent while polling for signs any more, so the "own sign out" check is gone.

## 2026-10-21

- **The guest locks onto the host that rang its sign** (BBSC 0.0.2, source published 2026-10-21,
  `emulator/src/core/bloodborne_re.cpp`, BbscRangHost / TickBbscRelayHostLock). The 2026-10-19
  placement is now the same as BBSC 0.0.2's on the wire, so Linux and Windows 0.0.2 players find
  each other. Taken from 0.0.2 on top of it:
  - a placement aimed at our sign notes its sender as the host that rang it (90 s);
  - while joining or a guest, that host's packets are taken before the lock is made, so the join
    load gets its world flags;
  - the lock takes that host when it is on the relay; else the position lock is stricter (6 m
    instead of 15, one host that close, 3 checks in a row), and "the only one hosting on the
    server" is gone: it was a stranger whenever the real host was not on the relay;
  - the hosts that rang are forgotten when the session ends.
  BBSC 0.0.2's timeline log is not taken.

## 2026-10-23

- **Documentation.** `README.md`, `server/README.md` (in place of `server/README.txt`) and
  `server/gameserver/README.md` describe BBSC as this port builds, runs and hosts it.
- **Windows host package removed.** The `.cmd` scripts and `server/tools/*.ps1` set up BBSC's
  Windows server package; this port hosts with `tools/shadnet-server`, `tools/bbsc-server` and
  `docs/SERVER.md`.
- **SUPPORTERS.txt** keeps its heading and list, without the donation links.
