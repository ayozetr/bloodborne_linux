# Button prompts and gestures menu

By **Dommo**, from [Nexus Mods: Bloodborne, mod 30](https://www.nexusmods.com/bloodborne/mods/30)
(uploaded by goomab): *DS3 Style - Modern Xbox prompts*, *DS3 Style - Nintendo Switch prompts* and
*Stripped down gesture menu*. The mod page allows using its assets and uploading them elsewhere
with credit to the author, but not in anything sold.

Only what the mods drew is here, never the game's own files:

- `xbox/`, `switch/`: the 20 button icons (`KG_*.dds`, BC7 exactly as in the mods) and the strip
  of big prompts from the shared UI atlas (`atlas.dds`, scaled down to the game's atlas size).
- `gesturetop.json`: the edits that turn the game's `menu/gesturetop.gfx` into the mod's.

The port draws its button prompts live (`gpu/shim/bbport_button_prompts.cpp`): `scripts/prompt_art.py`
turns the 20 icons into the raw images it uses for the Xbox and Switch styles, and the keyboard's
are its own. `scripts/gestures_menu.py` applies `gesturetop.json` to the player's own
`menu/gesturetop.gfx` when the launcher's *Gestures menu without motion-control icons* is on.
The Linux fork's `tools/extract_prompt_assets.py` rebuilt this folder from the mods' ZIPs.
