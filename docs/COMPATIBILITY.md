# Game compatibility

bbport runs Bloodborne for PS4 with **update 1.09**. Its hooks and patches use the addresses of
one executable: the launcher hashes the loaded `eboot.bin` image and runs only that one 1.09
executable (`scripts/game_check.py`). A dump that passes the check runs; one that does not is
told why (no 1.09 update, another executable, or an `eboot.bin` with Lance McDonald's 60 fps
patch baked in).

## Releases the launcher accepts

Every retail release of Bloodborne. Title and content IDs as listed in
[deadinside28/bloodborne_pc#117](https://github.com/deadinside28/bloodborne_pc/pull/117).

| Edition | Region | Title ID | Content ID | 1.09 executable checked |
|---|---|---|---|---|
| Bloodborne | US | `CUSA00900` | `UP9000-CUSA00900_00-BLOODBORNE000000` | Yes |
| Bloodborne | Europe | `CUSA00207` | `EP9000-CUSA00207_00-BLOODBORNE0000EU` | Not yet |
| Bloodborne | UK | `CUSA00208` | `EP9000-CUSA00208_00-BLOODBORNE0000UK` | Not yet |
| Bloodborne | Japan | `CUSA00299` | `JP9000-CUSA00299_00-BLOODBORNE0000JP` | Not yet |
| Bloodborne | Asia | `CUSA01363` | `HP9000-CUSA01363_00-BLOODBORNE0000AS` | Not yet |
| The Old Hunters Edition | US | `CUSA03179` | `UP9000-CUSA03179_00-BLOODBORNE000000` | Not yet |
| Game of the Year Edition | Europe | `CUSA03173` | `EP9000-CUSA03173_00-BLOODBORNE0000EU` | Yes |
| The Old Hunters Edition | Japan | `CUSA03014` | `JP9000-CUSA03014_00-BLOODBORNE0000JP` | Not yet |
| The Old Hunters Edition | Asia | `CUSA03023` | `HP9000-CUSA03023_00-BLOODBORNE0000AS` | Not yet |

*Checked* means a dump of that release with update 1.09 had exactly the executable bbport runs.
The others are accepted on the expectation that every release shares the same 1.09 executable;
if one does not, the launcher says so instead of starting a game that would crash. A report of
how yours goes is welcome either way.

The alpha tests (`CUSA01318`, `CUSA01322`, `CUSA01333`, `CUSA01335`) are not supported.

The Game of the Year and The Old Hunters editions include the DLC. With a base game, dump the
add-ons too and choose their folder in the launcher (see the README's *DLC* section).

## Tested with this fork

On Linux (CachyOS, NVIDIA GeForce RTX 3060), with the US release (`CUSA00900`):

- The base game with update 1.09 and the add-ons dumped separately (The Old Hunters and the two
  messenger add-ons), from the launcher's DLC folder.
- A dump whose `eboot.bin` had Lance McDonald's 60 fps patch baked in: the launcher reports it,
  and the clean 1.09 `eboot.bin` runs.
- Both regional texts through *Game region*: Spanish from Spain (Europe) and Latin American
  Spanish (the Americas).

The European Game of the Year edition (`CUSA03173`) is the release the original bbport is
developed and tested with.
