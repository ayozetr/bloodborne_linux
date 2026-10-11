# Bloodborne for Linux

The PlayStation 4 version of *Bloodborne* running natively on Linux. The game's own x86-64 code
runs directly on the CPU and its graphics are translated to Vulkan. It is not an emulator.

This fork builds on [bbport](https://github.com/deadinside28/bloodborne_pc), the native Linux port
by deadinside28. It adds the features of [Supermedo's Windows port](https://github.com/Supermedo/bloodborne_pc)
(online play, DLSS, cheats) brought to Linux, plus a few of its own.

> **No game files are included.** You need your own decrypted dump of Bloodborne with update
> 1.09, from a retail release: [which ones, and which have been checked](docs/COMPATIBILITY.md).
> This project is not affiliated with Sony Interactive Entertainment or FromSoftware.

## Features

- **Online play (beta)** through [The Hunter's Dream](https://thehuntersdream.com) and shadNet:
  messages, bloodstains, ghosts, bells and summons. Linux and Windows players can play together,
  through shadPS4's public server or [one of your own](docs/SERVER.md).
- **Upscaling:** AMD FSR 3.1, FSR 4 and FSR 4.1.1, **NVIDIA DLSS** on GeForce RTX, and
  native-resolution TAA.
- **Unlocked frame rate**, capped at your display's refresh rate up to 120 FPS (above that the
  game's own movement timing breaks), or 30/60/90 FPS. Output from 720p to 4K.
- **Launcher** with every setting in one window, in English, Spanish, Italian, French, German,
  Portuguese and Russian, like the in-game menu (Insert or L3+R3).
- **Settings in the game's own System menu** as well (Display and Effects pages), in the game's
  language.
- **Two memory models:** the new one, where the GPU works with the game's memory as in a PC game
  (the default on AMD), and the one of 0.3 (the default elsewhere); the launcher switches them.
- **Xbox, Switch and keyboard button prompts**, picked by the controller in use, and a gestures
  menu without the motion-control icons.
- **Cheats and gameplay tweaks:** never die, stealth, silent steps, enemy control, camera
  distance, ragdoll physics and more.
- **Game effects** on and off, **mods** and community **patches**, loaded without changing the
  game files ([how](docs/MODS.en.md)).
- **Add to Steam** in one click (native or Flatpak Steam), and **Discord Rich Presence** with the
  area you are in and your co-op partners.
- **AppImage:** one file with everything inside, for any distribution and the Steam Deck. It
  updates itself: the launcher's **About** page checks this repository's releases and installs
  a new AppImage over the old one.

## Requirements

- Linux x86-64 and a GPU with Vulkan 1.3: AMD or Intel with Mesa, or NVIDIA with NVIDIA's driver
  (open kernel modules included). Mesa's NVK has not been tested.
- DLSS needs a GeForce RTX (20 series or newer) and NVIDIA's driver; it does not work with NVK.
- About 6 GB of free memory, 10 GB for 1440p or 4K output.

## Getting started

### AppImage

Build it with `bash build.sh && bash packaging/appimage-sharun.sh`, then run
`dist/Bloodborne-bbport-x86_64.AppImage`. Choose your game folder (the one with `eboot.bin`) and
press **Play**. Saves and settings go to `~/.local/share/bbport`.

### From source

On Arch Linux (or CachyOS, Manjaro…):

```bash
sudo pacman -S --needed base-devel cmake ninja python python-gobject gtk4 libadwaita sdl3 \
    vulkan-headers vulkan-icd-loader glslang spirv-headers spirv-cross ffmpeg boost fmt \
    robin-map xxhash zydis miniz protobuf nlohmann-json openssl miniupnpc python-pillow ttf-dejavu
paru -S magic_enum vulkan-memory-allocator xbyak   # from the AUR

git clone --recursive https://github.com/ayozetr/bloodborne_linux
cd bloodborne_linux
bash build.sh
python3 launcher/bbport_launcher.py   # or launcher/install-desktop.sh for a menu entry
```

With [Nix](https://nixos.org), `bash build.sh` gets every dependency from `shell.nix` by itself.

### Online play

1. Register a shadNet account at [shadnet.shadps4.net](https://shadnet.shadps4.net), or get one
   from the owner of your group's own server.
2. In the launcher, open **Online**, turn on **Play online**, choose the shadNet server and enter
   your account name (not your email) and password. **Test the connection**: every line should
   be green.
3. Start the game and choose online at the title screen.

Everyone in a session needs game version 1.09 and the same servers. Turn cheats off when you
play with others.

**Co-op needs your own server for now:** shadPS4's public server does not answer on its UDP port,
so summons do not connect through it (messages, bloodstains and ghosts do).
[docs/SERVER.md](docs/SERVER.md) sets one up with Docker and Tailscale.

Co-op connects the players directly over UDP. UPnP opens the port on the router by itself; with
ufw or firewalld on, the launcher's **Online** page says so and gives the commands: pin the
**Co-op port** (for example 3658), open it (`sudo ufw allow 3658/udp`), and for UPnP let the
router's answers in (`sudo ufw allow from <router> proto udp`). [More in docs/ONLINE.md](docs/ONLINE.md).

### DLSS

On a PC with a GeForce RTX, run `bash tools/build_dlss.sh` once after `build.sh`. It downloads
what it needs from the NVIDIA DLSS SDK and builds the bridge. Then choose **DLSS** as the
upscaler.

### DLC

The Game of the Year edition (`CUSA03173`) already includes The Old Hunters. With the base game
(such as the US `CUSA00900`), dump your add-ons too: each one is a folder (`SPEXPANSIONDLC03`,
`SPDLCMESSENGER00`…) with only `sce_sys` inside, because their data ships with the 1.09 update.
Put them in one folder and pick it in the launcher (**Game → DLC folder**), or set
`BB_DLC_DIR=/path/to/dlc` for `run.sh`; the launcher shows how many it found. Each folder must
keep the add-on's name (its entitlement label, such as `SPEXPANSIONDLC03`). Copying them to
`user/addcont/<title id>/`, shadPS4's layout, works too.

### Add to Steam

**Game → Add to Steam** puts Bloodborne in your Steam library; it starts with the launcher's
settings. Steam has to be closed while the game is added, and the launcher offers to do that.
Flatpak Steam runs games inside its sandbox, which has neither the game nor your drivers, so
the shortcut starts the game outside it with `flatpak-spawn --host`. That needs the
`org.freedesktop.Flatpak` permission for Steam, which the launcher asks for once: it lets Steam
start programs on your system.

### Button prompts

The game shows PlayStation buttons. In the launcher, **Controls → Button prompts** switches them to
Xbox, Nintendo Switch or keyboard ones; *Automatic* follows the controller in use, and the
keyboard's when none is connected. Keyboard prompts show the keys bound in **Controls →
Keyboard**. **Gestures menu without motion-control icons** cleans up the gestures menu. The
prompts are put into your own game's menu files at each start, and nothing in the game folder
changes.

## Support

If this fork is useful to you and you would like to support it, you can on
[Ko-fi](https://ko-fi.com/ayozetr). The port itself is deadinside28's work (see below).

## Credits

- [deadinside28/bloodborne_pc](https://github.com/deadinside28/bloodborne_pc): **bbport**, the
  native Linux port this fork is built on, and almost all of the work behind it. Its README, with
  the technical details, is in [BBPORT.md](BBPORT.md).
- [Supermedo/bloodborne_pc](https://github.com/Supermedo/bloodborne_pc): the Windows port, whose
  online play, DLSS support, cheats page, Add to Steam and icon were brought to Linux here.
- [shadPS4](https://github.com/shadps4-emu/shadPS4): the renderer and shader recompiler.
- [shadp2p](https://github.com/Wozzardman/shadp2p) by Wozzardman: the network and PSN libraries
  for online play. Servers by the [shadPS4](https://shadps4.net) team and
  [The Hunter's Dream](https://thehuntersdream.com) by droogie and its team.
- [IFreemz/shadPS4-Bloodborne-DLSS-FSR](https://github.com/IFreemz/shadPS4-Bloodborne-DLSS-FSR):
  the DLSS bridge, and the [NVIDIA DLSS SDK](https://github.com/NVIDIA/DLSS).
- [FSR-Vulkan](https://github.com/FireBurn/FSR-Vulkan) by FireBurn and the AMD FidelityFX SDK.
- **Dommo**: the Xbox and Switch button prompts (*DS3 Style - Modern Xbox prompts*, *DS3 Style -
  Nintendo Switch prompts*) and the *Stripped down gesture menu*, from
  [Nexus Mods (Bloodborne, mod 30)](https://www.nexusmods.com/bloodborne/mods/30), uploaded by
  goomab. Only their drawn prompts are in this repository ([assets/menu_prompts](assets/menu_prompts)).
- **Abken**: the [KBM Icons Generator](https://www.nexusmods.com/bloodborne/mods/537), which showed
  which textures keyboard prompts need (after the idea of
  [mod 460](https://www.nexusmods.com/bloodborne/mods/460)); bbport draws its own.
- [quick-sharun](https://github.com/pkgforge-dev/Anylinux-AppImages) for the AppImage.
- Game patches by Kyo, Lance McDonald, auser1337, illusion, emoose and the Bloodborne community.

Full list of components and licenses: [BBPORT.md](BBPORT.md#credits-and-licenses).

## License

GNU GPL v2 or later ([LICENSE](LICENSE)). Third-party components keep their own licenses. NVIDIA
and DLSS are trademarks of NVIDIA Corporation.
