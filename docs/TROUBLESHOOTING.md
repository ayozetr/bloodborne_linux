# Troubleshooting

When asking for help, attach the log: in the launcher's **Log** section, **Export log…** saves it to
a file and **Copy** puts it on the clipboard.

## The launcher rejects the game

The launcher checks the game folder before starting. What it says, and what to do:

| Message | What to do |
|---|---|
| bbport needs the 1.09 update merged into the game folder | Copy everything from the dumped 1.09 update into the game folder, replacing files (`eboot.bin` and `sce_sys` too). |
| param.sfo is from 1.09 but eboot.bin is not | Copy `eboot.bin` from the dumped 1.09 update over the old one. |
| This eboot.bin has the 60 fps patch by Lance McDonald applied | Use a clean `eboot.bin` from the 1.09 update. bbport has its own 60 FPS. |
| This is not a retail release of Bloodborne | Alpha tests and other games do not run. See [COMPATIBILITY.md](COMPATIBILITY.md). |
| eboot.bin could not be read as a decrypted PS4 executable | Dump the game and the update again. |
| The game files are damaged | The extraction tool broke compressed files (LibOrbisPkg PkgTool on .NET 6 or newer); the game would hang while loading. Extract the game and the update again with a fixed tool. |

## The game shows *New Game* instead of my save

Saves live in the data directory, and each way of running the port has its own:

- The AppImage: `~/.local/share/bbport/user/savedata/1/<title ID>/`.
- From the repository (`run.sh`): `user/savedata/1/<title ID>/` in the repository.

To move a save, close the game, back up both folders, and copy the `savedata` folder over.

## DLSS is "not supported by this GPU"

The log says why, on a line starting with `DLSS:`.

- DLSS needs a GeForce RTX (20 series or newer) and NVIDIA's own driver; it does not work with
  NVK.
- The 0.4-linux.1 AppImage ships a modified copy of NVIDIA's DLSS library, which the driver
  refuses (`Feature requirement query failed: 0xbad00012`): update to 0.5-linux.1 or newer.
- From the repository, DLSS needs `bash tools/build_dlss.sh` once after `build.sh`.
- If the log says `Device creation with DLSS extensions failed`, NVIDIA's CUDA/UVM
  module is missing: the game then uses FSR 3.1. Load it with `sudo modprobe nvidia_uvm` (the
  `nvidia-modprobe` package loads it when needed); with Secure Boot, a module signing key that
  is not enrolled stops it (`Key was rejected by service`).

## Spanish shows the Latin American text (or the other way round)

The game picks a language's regional text by the dump's region. Choose it in **Setup → Game
region**: *Europe* for Spanish from Spain, *The Americas* for Latin American Spanish.

## The game crashes after playing a while, on a card with little VRAM

On a 6 GB card the texture cache can run out of video memory: the log then repeats
`Texture cache: memory pressure, ... (critical ...)`. Lower what uses VRAM: a 60 FPS limit,
a lower output resolution, lower **Model detail** in the game's *Display* settings, and close
other programs that use the GPU (browsers, video players, other games).

## The picture is stretched on an ultrawide screen

**Graphics → Display → Output resolution** lists 2560×1080, 3440×1440, 3840×1600 and 5120×2160
(21:9) and 3840×1080 and 5120×1440 (32:9); any other size written as `output_res=WxH` in
bbport.ini works too. The view gets wider instead of stretched: the game's camera, its HUD and the
lock-on and health-bar markers are patched at start for the screen's own aspect ratio. **HUD
position** moves health, items and Blood Echoes from the centred 16:9 area (as on a 16:9 screen)
to the screen edges, and menu backdrops cover the whole width. These sizes need the startup patch:
changing them in the game restarts it, and TAA (which needs live resolution changes) leaves them
stretched. `aspect_patch=0` in bbport.ini turns the wider view off.

## Quit to Desktop is missing from the menus, or shows another name

**Graphics → Game effects → Quit to Desktop in the title and System menus** (also in the in-game
menu; on by default) adds the entry to the title menu and to the System menu. The title entry
closes the game at once; the System entry runs the game's own *Exit Game* first (it saves, and
its confirmation asks to quit to the desktop), and the game closes when it is back at the intro
or the title screen. The log then says `Runtime: Quit to Desktop`, and the game ends with exit
code 0, as when the window is closed.

- No entry, and the log says `Quit to Desktop: ...; the game starts without it` or
  `Patches: ... Quit to Desktop skipped`: the menu texts could not be made from the game's files,
  or the game's executable is not the 1.09 code the entry was made for.
- A third-party *Exit Game (title menu)* patch (`Bloodborne_exit_game.xml` in the patches folder)
  also adds a way out to the title menu. When it changes any of the code Quit to Desktop changes,
  that patch is kept and Quit to Desktop's code is left out (`another patch writes ...` in the
  log): the System menu has no entry then. Quit to Desktop does the same and saves first from
  the System menu, so turn that patch off.
- A mod that replaces `msg/<language>/menu.msgbnd.dcx` (a translation) is laid over Quit to
  Desktop's texts: the entries keep that mod's names (*Opinion Box*, *Language*).

## The controller does nothing when the game is started from Steam

With Steam Input on, Steam hides the controller and the game gets Steam's virtual one, whose input
Steam sends only to the window it sees focused. On a Wayland desktop Steam sees only X11 windows,
so the game now opens its window through Xwayland when Steam made a virtual controller for it (the
log says `Window: X11 (Xwayland), so Steam Input reaches the game`). On older releases, put
`SDL_VIDEO_DRIVER=x11 %command% --play` in the shortcut's launch options (keep `--play` after
`%command%`), or turn Steam Input off for the shortcut: the game reads the controller itself.

## The camera turns much faster on diagonals

With the right stick pushed all the way, the game switches to its fast turn (about twice the
speed), and it does so on diagonals too, not only straight sideways. That is how the game turns on
a PS4 as well, with any controller. **Controls → Even camera speed on diagonals** keeps diagonals at
the normal speed; the fast turn stays when the stick is pushed straight sideways. With it on the
camera can feel heavier: the game's own *Camera speed* setting makes up for it.

## Summons never connect

Press **Test** in the **Status** row of **Multiplayer → Online**. An error mark on the shadNet server's UDP line means
the server never learns your address, and no summon can connect: check that the server is running
and that its log lists the UDP listener, and that no firewall blocks UDP 31314 on its side
([SERVER.md](SERVER.md)). shadPS4's public server does not accept bbport builds at all: use The
Hunter's Dream, Seamless Hunt or your own server.

## Other online problems

See [ONLINE.md](ONLINE.md): the account, the bells, the ports and the log lines of a summon.
