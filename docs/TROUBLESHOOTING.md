# Troubleshooting

When asking for help, attach the log: in the launcher's **Log** page, **Export log…** saves it to
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

The game picks a language's regional text by the dump's region. Choose it in **Settings → Game
region**: *Europe* for Spanish from Spain, *The Americas* for Latin American Spanish.

## The game crashes after playing a while, on a card with little VRAM

On a 6 GB card the texture cache can run out of video memory: the log then repeats
`Texture cache: memory pressure, ... (critical ...)`. Lower what uses VRAM: a 60 FPS limit,
a lower output resolution, lower **Model detail** in the game's *Display* settings, and close
other programs that use the GPU (browsers, video players, other games).

## The camera turns much faster on diagonals

With the right stick pushed all the way, the game switches to its fast turn (about twice the
speed), and it does so on diagonals too, not only straight sideways. That is how the game turns on
a PS4 as well, with any controller. **Controls → Even camera speed on diagonals** keeps diagonals at
the normal speed; the fast turn stays when the stick is pushed straight sideways. With it on the
camera can feel heavier: the game's own *Camera speed* setting makes up for it.

## Summons never connect

Run **Test the connection** in the **Online** page. A red line for the shadNet server's UDP means
the server never learns your address, and no summon can connect: check that the server is running
and that its log lists the UDP listener, and that no firewall blocks UDP 31314 on its side
([SERVER.md](SERVER.md)). shadPS4's public server does not accept bbport builds at all: use The
Hunter's Dream or your own server.

## Other online problems

See [ONLINE.md](ONLINE.md): the account, the bells, the ports and the log lines of a summon.
