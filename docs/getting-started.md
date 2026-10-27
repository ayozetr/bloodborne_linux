# Getting started

## What you need

- **Your own dump of Bloodborne with update 1.09**, from your PS4: any retail release (US, Europe,
  UK, Japan, Asia, and the editions with The Old Hunters). No game files are included, and other
  versions of the game's executable start and then crash. [Which releases work](COMPATIBILITY.md).
- **Linux x86-64** and a GPU with **Vulkan 1.3**: AMD or Intel with Mesa, or NVIDIA with NVIDIA's
  driver. The Steam Deck works too.
- About **6 GB of free memory**, 10 GB for 1440p or 4K.

## First launch

1. Download `Bloodborne-bbport-x86_64.AppImage` from the
   [latest release](https://github.com/ayozetr/bloodborne_linux/releases/latest).
2. Make it executable (in a file manager: *Properties → Permissions → Allow executing*, or
   `chmod +x Bloodborne-bbport-x86_64.AppImage`) and run it.
3. In the launcher, choose your **game folder**: the one with `eboot.bin` in it.
4. Press **Play**.

!!! tip "The first minutes"
    The first time, the game builds its shaders as it meets them, so it can stutter for a few
    minutes. The next sessions start with them ready.

## Saves, settings and the DLC

- Saves and settings go to `~/.local/share/bbport`.
- **Setup → Saves** exports your saves into a `.zip` and imports them back, also from shadPS4.
- The Game of the Year edition already has *The Old Hunters*. With the base game, put its DLC
  folder in **Setup → DLC folder**.

## Updating

The launcher's **About** page says when a new release is out and installs it; it can also go back
to an earlier one. Your saves and settings stay as they are.

## Next steps

- [Play online](ONLINE.md), alone or in seamless co-op.
- [Add the game to Steam](steam-deck.md), or play on the Steam Deck.
- Something wrong? [Troubleshooting](TROUBLESHOOTING.md) and [getting a log](logs.md).
