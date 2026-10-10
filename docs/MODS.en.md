# Mods and third-party patches

Both are on the launcher's **Settings** page and apply at the next start. The game folder itself
is never changed.

## File mods

The **Mods** group has the folder, a **Load mods** switch, and the list of mods: each one can be
turned on or off and moved up or down. The lowest mod that is on wins: when two mods replace the
same file, the log says which one replaced the other.

The mods folder is `~/.local/share/bbport/mods/` with the AppImage (`mods/` in the data
directory when running from the repository). Extract each mod into a folder of its own:

```text
mods/
  Mod name/
    dvdroot_ps4/
      chr/...
      param/...
      menu/...
```

These layouts work as well:

- `Mod name/app0/dvdroot_ps4/...`, and `Mod name/<title ID>/dvdroot_ps4/...` with whichever
  release the mod was made for (`CUSA03173`, `CUSA00900`, ...).
- One extra wrapper folder, as extracting an archive into a folder of its name leaves it:
  `Mod name/Mod name v1.2/dvdroot_ps4/...` (readme files and pictures may sit next to it).
- The game's folders without `dvdroot_ps4`: `Mod name/chr/...`, `Mod name/parts/...` (`chr`,
  `parts`, `map`, `menu`, `msg`, `param`, `sfx`, `sound`, `font` and the other folders of
  `dvdroot_ps4`).

Upper or lower case does not matter: a mod made on Windows with
`DVDROOT_PS4/Chr/C0000.chrbnd.dcx` replaces the game's `dvdroot_ps4/chr/c0000.chrbnd.dcx`.
The log shows how many game files the mods replaced and added, e.g.
`Mods: 12 game files replaced, 0 added`. A mod meant to replace files that says
`0 game files replaced` has its files in the wrong place.

What works: ready-made replacements of `dvdroot_ps4` files (textures, models, params,
interface, sound, fonts). What does not:

- ZIP or 7z archives: extract them first.
- Two mods changing different parts of the same `.dcx` or `.bnd` file: the last one replaces
  it whole, the files are not merged.
- Mods that replace `eboot.bin`, `sce_module` or `sce_sys`, DLL injectors and script plugins.
  Changes to the game's code are patches (below).
- Symbolic links inside a mod.

Whether a mod works with Bloodborne 1.09 is up to its author.

A shadPS4-style folder next to the game folder, `<game folder>-mods/dvdroot_ps4/...` (for
example `CUSA03173-mods` next to `CUSA03173`), is loaded too, before the mods in the list. You
can also choose a folder that holds `dvdroot_ps4` directly as the mods folder: it is then loaded
as one mod. **Load mods** turns all of them off. The launcher's button prompts and gestures
menu work the same way, as files laid under the mods; they are settings of their own and stay
on when mods are off.

### How it works

For each start, the data directory gets a merged tree of links, `out/mod-game-*`: the game sees
the mods' files where they replace its own and the original files everywhere else. `/app0` is
read-only, and saves go to the usual folder. The tree is removed when the game exits normally
or the launcher stops it; one left behind by a crash is not reused.

The order and the mods turned off are kept in `mods.json` in the data directory:

```json
{"order": ["First", "Second"], "disabled": ["First"]}
```

New folders are turned on and added at the end, in alphabetical order.

From a terminal:

```sh
BB_GAME_DIR=/path/to/game BB_MODS_DIR=/path/to/mods bash run.sh
BB_GAME_DIR=/path/to/game BB_MODS_ENABLED=0 bash run.sh
```

`BB_MODS_CONFIG` sets another `mods.json`. `BB_MOD_TRACE=1` (with `BB_MODS_DIR`) logs the
first reads of files that come from mods, to see whether a mod is being used.

## Third-party patches

The **Third-party patches** group loads patches in the shadPS4/GoldHEN XML format from the
patches folder: `~/.local/share/bbport/patches/` with the AppImage, or another folder chosen in
the launcher.

- Only patches for version `01.09` of `eboot.bin` are listed. Files for other games are
  skipped: a file applies when it lists any retail release of Bloodborne, or none.
- Each patch starts on or off as the file says (`isEnabled`); the choice in the launcher is
  kept in `patches.json` in the data directory:

  ```json
  {"enabled": ["file.xml/Patch name"], "disabled": ["file.xml/Other patch"]}
  ```

- Lines of type `bytes`, `bytes16`, `bytes32`, `bytes64`, `float32`, `float64`, `utf8` and
  `utf16` work. A patch with a `mask` line (a pattern search) or an address outside the
  executable is skipped whole, and the log says so.
- They apply after bbport's own patches (`patches/Bloodborne.xml`), so where both change the
  same bytes, the third-party patch wins.
- Patches that replace pointers in tables, such as *60 FPS++*, are moved to where the game is
  loaded.

From a terminal: `BB_PATCHES_DIR=/path BB_PATCHES_CONFIG=/path/patches.json bash run.sh`.

This guide is based on bbport's [MODS.md](MODS.md) (Russian), by deadinside28.
