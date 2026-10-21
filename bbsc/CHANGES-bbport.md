# bbport's changes to BBSC

This folder holds [BBSC](https://github.com/Classmg22/BBSC) 0.0.2 by CLS_AMG (GPL-2.0-or-later),
as published at commit 4f11faf (tag v0.0.2; 0.0.1 was commit 315f76c), with the changes below made
for the Linux port of bbport. Changed lines in BBSC's own files are marked `bbport:` in comments.

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
  BBSC 0.0.2's timeline log was not taken then (it is now, see "BBSC 0.0.2" below).

## 2026-10-21: BBSC 0.0.2

The rest of BBSC 0.0.2 (commit 4f11faf), merged with BBSC's own changes from 0.0.1 kept as they
are, and bbport's changes above kept on top of them.

- **Taken as published:** `CREDITS.txt`, `SUPPORTERS.txt`, `emulator/mod/mod.json` (version 0.0.2,
  the new "Bells anywhere" option, the Discord option's text), `emulator/mod/bbsc_channel.cpp`,
  `emulator/mod/bbsc_discord.cpp`, `emulator/mod/bbsc_mod.cpp` (both Windows only, not built
  here), `emulator/src/core/bbsc_cinematic.{h,cpp}` (not built here), `bbsc_patch_tables.h`,
  `bbsc_persistence.h` (the new default-on switches `SHADPS4_BBSC_AREA_LIST_CAP`,
  `SHADPS4_BBSC_WORLD_SYNC_ALL`, `SHADPS4_BBSC_TIMELINE`, `SHADPS4_BBSC_BELLS_ANYWHERE`), the
  shim's `np_signaling_bbsc.h` and `server/gameserver/`.
- **Taken with bbport's changes kept:** `emulator/src/core/bloodborne_re.{h,cpp}` (the watch
  camera of a dead guest, the kit's bells anywhere, the host's time of night for the guest, the
  area list cap against "Panic 265", the boss, kick and drop fixes, the kit from the game's own
  tables, the frame rate and Discord data, the timeline), `emulator/mod/bbsc_http.cpp` and
  `emulator/mod/bbsc_relay.cpp` (the relay's write queue).
- **The aimed placement and the host lock** (2026-10-19 and the first 2026-10-21 entry above) are
  now BBSC's own code, under its names: `OnAimedHostPlacement`, `RelaySendAimedPlacement`,
  `AimedPlacementType` (0x31), `own_user_id` / `placement_aimed`, and the claim told from the
  search by URL (`/summon_messenger/request` vs `/get`). The wire format is unchanged. Gone with
  them: bbport's own names (`OnDirectedPlacement`, `RelaySendPlacementTo`, `PlacementToType`) and
  its reading of a `UserId` / `TargetUserId` sent as a string.
- **The co-op kit, late** (2026-10-15) stays: 0.0.2 first looks in the game's own tables for 3
  minutes; the search of every copy behind it keeps going after 3 minutes as before.
- **Linux:**
  - `emulator/mod/linux/bbsc_mod_linux.cpp`: version 0.0.2; the import slot reads and writes
    0.0.2 calls `ReadSlotSafely` / `WriteSlotSafely` (through bbport's map of the game's memory);
    the timeline's start lines; the timeline file goes next to the log
    (`<user dir>/bbsc/logs/bbsc-timeline-*.txt`), and only the newest 5 are kept, as the logs.
  - **Watch camera:** the F1 free camera stays out of the Linux build (every key, button and the
    mouse also reach the game through bbport's pad, so flying it would move the hunter; L3+R3 is
    bbport's menu). The watch camera of 0.0.2 only comes on by itself while our hunter is dead in
    co-op, when those inputs do nothing in the game, so it is in: `bbsc_mod_linux.cpp` reads its
    keys through SDL like the F8 key, on the game thread and only while it is on: Tab / E / left
    click next hunter, Shift+Tab / Q previous, F fly freely and back; the controller's R1 / L1 and
    sticks; arrow keys and W / S. F1 turns it off for the rest of that death. The mouse's movement
    is not read (it is bbport's mouse look). Switches `SHADPS4_BBSC_CINEMATIC` and
    `SHADPS4_BBSC_SPECTATE` as on Windows.
  - `emulator/mod/bbsc_http.cpp`: 0.0.2's overrides file list (`HostOverridesFiles`) is Windows
    only; on Linux the online module still applies the overrides, and the relay keeps its own list.
  - `emulator/mod/bbsc_relay.cpp`: a send to a closed link fails instead of raising SIGPIPE
    (`MSG_NOSIGNAL`), and the writer's 10 s send timeout is set as a `timeval`.
  - `emulator/mod/linux/bbsc_win32.h`: `WSAGetLastError` and `SD_BOTH`, which the relay uses now.
- **Translations:** the new texts ("An item was added to your items." and the watch camera's) in
  every language. `bbsc_i18n.cpp` also translates a text with numbers through its `{n}` /
  `{count}` form ("Watching hunter 1 of 2.").
- **Not taken:**
  - BBSC's Discord status (`bbsc_discord.cpp`): bbport has its own; the build and boss timer data
    are gathered but not shown.
  - the files of BBSC's own emulator build (`emulator/src/core/bbsc_relay_client.cpp`, the
    emulator's network, signaling, pad and module files, `emulator/CMakeLists.txt`, the launcher's
    `emulator_settings.h`) and the patch for BBport's Windows build (`bbport/`): bbport builds
    none of them, and the game logic here does not need them.
