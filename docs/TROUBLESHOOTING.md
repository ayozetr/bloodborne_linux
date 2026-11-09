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
| This is not a retail release of Bloodborne | Alpha tests and other games do not run. See [supported releases](COMPATIBILITY.md). |
| eboot.bin could not be read as a decrypted PS4 executable | Dump the game and the update again. |
| The game files are damaged | The extraction tool broke compressed files (LibOrbisPkg PkgTool on .NET 6 or newer); the game would hang while loading. Extract the game and the update again with a fixed tool. |

## The game shows *New Game* instead of my save

Saves live in the data directory, and each way of running the port has its own:

- The AppImage: `~/.local/share/bbport/user/savedata/1/<title ID>/`.
- From the repository (`run.sh`): `user/savedata/1/<title ID>/` in the repository.

To move a save, close the game, back up both folders, and copy the `savedata` folder over.

## DLSS is "not supported by this GPU"

The log says why, on a line `DLSS: unavailable (...)`; the game then uses another upscaler.

- DLSS needs a GeForce RTX (20 series or newer) and NVIDIA's own driver; it does not work with
  NVK (`not an NVIDIA GPU`, or `this GPU or driver does not support DLSS`).
- `NVIDIA NGX initialization failed`: update the driver, and check that NVIDIA's CUDA/UVM module
  is loaded (`sudo modprobe nvidia_uvm`; the `nvidia-modprobe` package loads it when needed). With
  Secure Boot, a module signing key that is not enrolled stops it (`Key was rejected by service`).
- DLSS Frame Generation needs a GeForce RTX 40 or newer; on older cards the log says so and DLSS
  itself still works.
- From the repository, DLSS needs `bash tools/build_dlss.sh` once after `build.sh`.

## Spanish shows the Latin American text (or the other way round)

The game picks a language's regional text by the dump's region and the system language. Choose the
text you want in **Setup → Game text language**: *Español* for Spanish from Spain, *Español
(Latinoamérica)* for Latin American Spanish. **Voice language** does the same for the voices.

## The game crashes after playing a while, on a card with little VRAM

On a 6 GB card the texture cache can run out of video memory: the log then repeats
`Texture cache: memory pressure, ... (critical ...)`. Lower what uses VRAM: a 60 FPS limit,
a lower output resolution, lower **Model detail** in the game's *Display* settings, and close
other programs that use the GPU (browsers, video players, other games).

## The frame rate drops in some places and stays low until a reload

Seen mostly on NVIDIA cards (#42): the game runs at its usual rate, then in some places drops
(to 17-35 FPS) and stays there until a lamp travel or a restart. When video memory was full, a
copy of the game's memory could land in system memory and stay there, and the GPU read it over
the bus. From 0.70-linux.4, on cards with more than 4 GB those copies stay in video memory, and
one that does not fit is made again later; the log says so at start (`Layer memory: mirrors in
VRAM only`). `BB_MIRROR_VRAM_ONLY=0` under **Advanced → Developer → Extra variables** brings the
old behaviour back, and `=1` turns it on for a card of 4 GB or less.

A place that is simply heavy is different: it is slower from the moment you get there, and the
same after a reload. If a drop stays until a reload, turn on **Save the log and statistics to a
file** and attach the log of that whole session to the issue.

## Keyboard and mouse in the game's menus

In the game's menus the mouse points at items and the **left button** chooses them. The other
buttons keep what they do in play, as the game's own prompts show: the **right button** is L2
(the storage box switches to the storage with it), the side buttons R2 and L1. **Escape** goes
back.

## The picture is stretched on an ultrawide screen

Choose the screen's shape in **Graphics → Display → Aspect ratio** (*Auto* follows the output
resolution): 4:3, 16:10, 16:9, 21:9 or 32:9. The view gets wider (or taller) instead of stretched,
and the HUD keeps to the screen's edges; it changes live, in the game's *Display* menu too.
**Output resolution** *Auto* is the monitor's own; any other size written as `output_res=WxH` in
bbport.ini works too.

## Fullscreen opens on the wrong monitor, or drops back to a window

With several monitors, choose the one to play on in **Display → Monitor**: the port's *Primary*
is the one the system reports first, which on Wayland is not always the one KDE or GNOME show as
primary. On Wayland a program cannot place its own window, so the compositor may open it on
another monitor first and then move it; when that leaves it as a plain window, the port asks for
fullscreen again during the first seconds (the log says
`Display: the compositor left the window out of fullscreen, asked again`). If it still ends up
windowed, add `SDL_VIDEO_DRIVER=x11` under **Advanced → Developer → Extra variables**: through
Xwayland the window places itself.

## Exit to desktop

**Exit to desktop** is in the game's System menu and on the title screen, from bbport 0.7. The
*Quit to Desktop* switch of earlier Linux versions is gone with it, and a third-party *Exit Game*
patch is no longer needed. In the world it asks first and goes through the game's own Quit Game,
so your progress is saved, and the game closes once it is back at the title.

## The port's menu opens by accident with L3 + R3

From bbport 0.7, L3 + R3 opens the port's menu only when both are held for 0.8 seconds, so pressing
them in a fight (lock-on and camera reset) no longer opens it. **Controls → Port menu from the
controller** can make it 2 seconds, or turn it off so that only Insert on the keyboard opens the
menu. Closing it with L3 + R3 always works.

## The controller does nothing when the game is started from Steam

With Steam Input on, Steam hides the controller and the game gets Steam's virtual one, whose input
Steam sends only to the window it sees focused. On a Wayland desktop Steam sees only X11 windows,
so the game now opens its window through Xwayland when Steam made a virtual controller for it (the
log says `Window: X11 (Xwayland), so Steam Input reaches the game`). On older releases, put
`SDL_VIDEO_DRIVER=x11 %command% --play` in the shortcut's launch options (keep `--play` after
`%command%`), or turn Steam Input off for the shortcut: the game reads the controller itself.

## The Steam overlay does not open in the game

Steam's overlay (Shift+Tab, its FPS counter, F12 screenshots) needs the game started from Steam,
with **Steam overlay** on under **Add to Steam** in the launcher (on by default). The log then says
`Steam overlay: …/ubuntu12_64/gameoverlayrenderer.so`. Without that line, the game was not started
by Steam.

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
([hosting your own server](SERVER.md)). shadPS4's public server does not accept bbport builds at all: use The
Hunter's Dream, Seamless Hunt or your own server.

## Other online problems

See [Online play and co-op](ONLINE.md): the account, the bells, the ports and the log lines of a summon.
