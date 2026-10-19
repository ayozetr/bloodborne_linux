# Hunter's Atlas map generator

The generator of [Hunter's Atlas](https://github.com/MikeTat1988/HuntersAtlas) by MikeTat1988
(GPL-2.0-or-later): it reads the player's own Bloodborne 1.09 files and writes the map packs the
in-game map (`gpu/shim/bbport_map*.cpp`) draws. No game file is changed or shipped; the packs stay
on the player's computer.

These are the scripts of Atlas's `source/generator/src` at `4ee4a0ed` (Atlas 1.3), without its
Windows packaging (PyInstaller spec, `generate_atlas_lite.py`) and without its copy of soulstruct,
which is installed from PyPI instead.

## Running it

It needs CPython 3.12 and the pinned packages of `requirements.txt` (soulstruct, numpy, scipy,
shapely, fontTools, Pillow, ...). With [uv](https://docs.astral.sh/uv/):

```
uv venv --python 3.12 venv
uv pip install --python venv/bin/python -r tools/hunters-atlas/requirements.txt
cd tools/hunters-atlas
../../venv/bin/python generate_atlas.py --game-dir <game folder> --output-dir <output folder>
```

The game folder is the one with `eboot.bin`, `sce_sys` and `dvdroot_ps4` (the base game and The
Old Hunters). It prints one JSON progress line per step and takes about 4 to 5 minutes here. The
output folder gets `maps/` (`atlas.json`, `catalog.json`, `features.json` and one JSON per area)
and `art/native-font.ttf`, a map font made from the game's own menu font.

### Names in the game's language

The generator writes the names of areas, lamps and pickups in English. `localize_names.py` (the
port's) then replaces them in the pack with the game's own names in another language: each name is
looked up among the game's English texts (`msg/engus`, menu and item texts) and replaced by the
text with the same id in the chosen folder (`spaes`, `frafr`, `rusru`, `deude`, `itait`, ...).
Names it cannot find stay in English; the generator's own matching is not touched.

```
../../venv/bin/python localize_names.py --game-dir <game folder> --output-dir <output folder> --language spaes
```

It also writes the language and the new file hashes into `maps/generated-assets.json`.

The in-game map is then pointed at them with `BB_ATLAS_ENABLED=1`, `BB_MAP_DIR=<output>/maps`,
`BB_MAP_CATALOG=<output>/maps/catalog.json`, `BB_MAP_FONT=<output>/art/native-font.ttf` and
`BB_MAP_ART_DIR` (Atlas's own art, `background`, `icons`, `menu` and `parchment` as `.bbra`).
`BB_MAP_SOUND_GAIN` (0-2, 0.07 by default) sets the map's cursor sounds' level. `BB_ATLAS_DEBUG=1` logs what the map reads from the game's quick menu whenever it changes (lines
starting with `Atlas debug:`).

## Changes for Linux

- `extract_verified_gates.py` and `extract_subarea_names.py` look a parameter table up by its
  name: soulstruct gives a binder entry's name with the game's Windows path
  (`N:\SPRJ\...\ObjActParam.param`), and `Path.name` only splits it on Windows, so the table was
  never found on Linux (`StopIteration`). The last part after `\` or `/` is compared now.

## Licenses

Atlas's scripts are GPL-2.0-or-later, like the port. soulstruct (by Grimrukh) is GPL-3.0-or-later
and runs as a separate program with this generator; it is installed by the player, not shipped.
