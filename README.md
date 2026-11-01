# Bloodborne for Linux

[![Total Download Count](https://img.shields.io/github/downloads/ayozetr/bloodborne_linux/total.svg?color=2ea44f)](https://github.com/ayozetr/bloodborne_linux/releases/latest)
[![Latest Release](https://img.shields.io/github/v/release/ayozetr/bloodborne_linux.svg?color=8a2be2)](https://github.com/ayozetr/bloodborne_linux/releases/latest)
[![License: GPL-3.0](https://img.shields.io/github/license/ayozetr/bloodborne_linux.svg?color=d73a49)](LICENSE)
[![Platform: Linux | Steam Deck](https://img.shields.io/badge/platform-Linux%20%7C%20Steam%20Deck-blue.svg)](#features)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-support-FF5E5B.svg?logo=ko-fi&logoColor=white)](https://ko-fi.com/ayozetr)

The PlayStation 4 version of *Bloodborne* running natively on Linux. The game's own code runs
directly on the CPU and its graphics are translated to Vulkan: it is not an emulator.

This fork is built on [bbport](https://github.com/deadinside28/bloodborne_pc) by deadinside28. It
adds improvements of its own, and others from the community, taken from pull requests and other
projects ([credits](docs/CREDITS.md)).

> **No game files are included.** You need your own decrypted dump of Bloodborne with update
> 1.09, from a retail release ([which ones](docs/COMPATIBILITY.md)). This project is not
> affiliated with Sony Interactive Entertainment or FromSoftware.

**[The players' guide](https://ayozetr.github.io/bloodborne_linux/)**: installing, playing online and
seamless co-op, the Steam Deck, and what to do when something goes wrong.

## Features

- **Multiplayer**: online messages, bloodstains, ghosts, bells and summons, on
  [The Hunter's Dream](https://thehuntersdream.com) or a server of your own; **Seamless Co-op**
  (experimental), co-op that lasts through deaths, lamps and areas, for up to 5 hunters; and
  **local co-op** (split screen), 2 to 4 players on one PC, each with their own controller.
- **In-game map** (Hunter's Atlas): a fullscreen map with where you are, lamps and items, and fast
  travel to the lamps you've found.
- **Frame rate unlocked** (up to 120 FPS) or capped at **30, 60 or 90**. Resolutions from
  **720p to 4K**, and **ultrawide** (21:9, 32:9, [how](docs/TROUBLESHOOTING.md#the-picture-is-stretched-on-an-ultrawide-screen)).
- **Upscaling:** AMD **FSR 3.1** and **FSR 4**, NVIDIA **DLSS** (GeForce RTX) and TAA.
- **Any controller:** PlayStation, Xbox and Switch pads with their own **button prompts in the
  game**, and **keyboard and mouse**, with a direct 1:1 mouse camera, keys you can rebind
  (or bbport 0.6's Dark Souls III-style layout) and the mouse as a pointer in the game's menus.
- **Quit to Desktop** from the game's title and System menus (it saves first).
- **Cheats and gameplay tweaks:** never die, stealth, camera distance, ragdoll physics and more.
- **Trophies and the platinum**, with a notice in the game like on the PS4.
- **Add to Steam** in one click, and **Discord Rich Presence** with your area and co-op partners.
- **Launcher and in-game menu** (L3 + R3 or Insert) in English, Spanish, French, German, Italian,
  Portuguese, Russian and Simplified Chinese.
- **AppImage** ready for any distribution and the Steam Deck, which **updates itself** from the
  launcher (and can go back to an earlier release).
- **Mods and community patches**, without touching the game files ([how](docs/MODS.en.md)).

## Requirements

- Linux x86-64 and a GPU with Vulkan 1.3: AMD or Intel with Mesa, or NVIDIA with NVIDIA's driver.
- About 6 GB of free memory, 10 GB for 1440p or 4K.

## Getting started

1. Download `Bloodborne-bbport-x86_64.AppImage` from the
   [latest release](https://github.com/ayozetr/bloodborne_linux/releases/latest).
2. Make it executable and run it.
3. Choose your game folder (the one with `eboot.bin`) and press **Play**.

Saves and settings go to `~/.local/share/bbport`; **Setup → Saves** exports your saves into a
.zip and imports them back, or from shadPS4, and can keep a copy of them from before each game
(off by default). The Game of the Year edition already has The Old
Hunters; with the base game, its DLC goes in **Setup → DLC folder** ([how](docs/COMPATIBILITY.md)).

## Online play

In the launcher's **Multiplayer → Online** tab, turn on **Play online**, choose a server and press **Test**
in the **Status** row (every line should get a check mark):

- **Seamless Hunt** (the default): the community server of Seamless Co-op (BBSC), with players on
  the Windows port. Make an account from the launcher with **Create** ([docs/ONLINE.md](docs/ONLINE.md#seamless-hunt)).
- **The Hunter's Dream**: sign in with Discord, or create an account with just a name. You play
  with bbhost's players. This connection is unofficial: report problems here, not to The Hunter's
  Dream.
- **Your own server**: for your group, with Docker and Tailscale ([docs/SERVER.md](docs/SERVER.md)).
- **Seamless Co-op (BBSC)**, in the same tab: every player needs it, and summons across areas need
  its game server, which your own server can run ([docs/ONLINE.md](docs/ONLINE.md#seamless-co-op-bbsc)).

With online play on, the game starts online by itself, as PLAY ONLINE on a PS4. If you turned off
*Skip the “play online / offline” choice* and pick offline, choose **Log In** on the title screen later
for online play; until then the co-op bells are greyed out.

Everyone in a session needs update 1.09. Turn cheats off when you play with others. Ports,
firewalls and the rest: [docs/ONLINE.md](docs/ONLINE.md).

## Local co-op (experimental)

Several games on one PC, one per player, each in its part of the screen with its own controller
(the launcher's **Multiplayer → Local** tab): choose the players (2 to 4), the layout and each player's
controller, then press **Play together**. Player 1 plays with the launcher's settings and saves;
players 2 to 4 get their own saves and settings in `~/.local/share/bbport/coop/player<N>` (copied
from player 1's the first time, about 400 MB each), without online play or Discord. One player can
use the keyboard and mouse. Only player 1 has sound unless you turn that off. The windows can go
to a monitor of their own (**Monitor**), and **Copy player 1's saves** gives another player the
same characters (their own saves are backed up first). The windows are placed through X11, which
works in a Wayland session too (XWayland).

## Building from source

On Arch Linux (or CachyOS, Manjaro…):

```bash
sudo pacman -S --needed base-devel cmake ninja python python-gobject gtk4 libadwaita sdl3 \
    vulkan-headers vulkan-icd-loader glslang spirv-headers spirv-cross ffmpeg boost fmt \
    robin-map xxhash zydis miniz protobuf nlohmann-json openssl miniupnpc python-pillow ttf-dejavu
paru -S magic_enum vulkan-memory-allocator xbyak   # from the AUR

git clone --recursive https://github.com/ayozetr/bloodborne_linux
cd bloodborne_linux
bash build.sh
python3 launcher/bbport_launcher.py
```

With [Nix](https://nixos.org), `bash build.sh` gets every dependency by itself. DLSS needs
`bash tools/build_dlss.sh` once; the AppImage is `bash packaging/appimage-sharun.sh`. Environment
variables for the launcher's **Advanced → Developer → Extra variables**: [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md).
Problems: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## On Windows

If you need a Windows version, I recommend
[Supermedo's Windows port](https://github.com/Supermedo/bloodborne_pc) and
[Awakenchan's LanternEngine](https://github.com/Awakenchan/LanternEngine).

## Support

This fork is built on the port deadinside28 created, but it has a lot of hours of work behind it,
and above all hours and hours of testing things and hunting down fixes so it runs as well as it
can. I always try to fix every report as soon as possible, because I know how much this game means
to some people. If it's useful to you and you'd like to support it, you can on
[Ko-fi](https://ko-fi.com/ayozetr).

## Credits

Built on [bbport](https://github.com/deadinside28/bloodborne_pc) by deadinside28, with
[shadPS4](https://github.com/shadps4-emu/shadPS4)'s renderer, and with work from many people and
projects: everyone is in [docs/CREDITS.md](docs/CREDITS.md). It includes code from
Lantern Engine by Awaken (https://github.com/Awakenchan/LanternEngine). Components and their licenses:
[BBPORT.md](BBPORT.md#credits-and-licenses).

## License

GNU GPL v3 or later ([LICENSE](LICENSE)). Files taken from other projects keep their own notices:
most are GPL-2.0-or-later (bbport, shadPS4), which allows them to be distributed under
GPL-3.0-or-later. Third-party components keep their own licenses. NVIDIA
and DLSS are trademarks of NVIDIA Corporation.
