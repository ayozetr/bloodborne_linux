# Credits

Everyone whose work is in this fork, and every project it took something from. Everyone listed
under *People* and *Help and testing* also appears in the launcher's **About** section. Components and their licenses: [bbport's notes](../BBPORT.md#credits-and-licenses).

## Projects

| Project | What this fork takes from it |
|---|---|
| [deadinside28/bloodborne_pc](https://github.com/deadinside28/bloodborne_pc) | **bbport**, the native Linux port everything here is built on. Its README is [here](../BBPORT.md). |
| [Supermedo/bloodborne_pc](https://github.com/Supermedo/bloodborne_pc) | The Windows port: online play, the cheats page, Add to Steam, the field of view, the game's audio at full level and many fixes. |
| [Awakenchan/LanternEngine](https://github.com/Awakenchan/LanternEngine) (formerly BloodBorneButPc) | Lantern Engine by Awaken (https://github.com/Awakenchan/LanternEngine) (GPL-3.0-or-later): crash fixes, stick options, the controller in use, save import, the version selector, and renderer fixes (vertex inputs, index buffers, camera motion vectors). |
| [shadPS4](https://github.com/shadps4-emu/shadPS4) | The renderer and shader recompiler they started from, and the online code: shadPS4 0.20's network, NP and shadNet libraries, put together for bbport by Awaken ([gpu/bbnet20](../gpu/bbnet20)). |
| [Wozzardman/shadnet-p2p](https://github.com/Wozzardman/shadnet-p2p) | The shadNet server for a group's own co-op server ([hosting your own server](SERVER.md)). |
| [Classmg22/BBSC](https://github.com/Classmg22/BBSC) | Seamless Co-op, by CLS_AMG, with Wozzardman's seamless summon ([gpu/bbnet20/bbsc](../gpu/bbnet20/bbsc), its game server in [scripts/bbsc_gameserver](../scripts/bbsc_gameserver)). |
| [fhody125-web/NoDreamForHunter](https://github.com/fhody125-web/NoDreamForHunter) | The base of BBSC's game server. |
| [MikeTat1988/HuntersAtlas](https://github.com/MikeTat1988/HuntersAtlas) | Hunter's Atlas: the fullscreen in-game map, its quick-menu tile, lamp travel and the map generator ([tools/hunters-atlas](../tools/hunters-atlas)), which runs with Grimrukh's [soulstruct](https://github.com/Grimrukh/soulstruct). |
| [The Hunter's Dream](https://thehuntersdream.com) | The online server, by droogie and its team; droogie's [bbhost](https://github.com/droogie/bbhost) is the base of its backend in the online module ([gpu/bbnet20/thd](../gpu/bbnet20/thd)) and brought fast loading after a death or travel. |
| [IFreemz/shadPS4-Bloodborne-DLSS-FSR](https://github.com/IFreemz/shadPS4-Bloodborne-DLSS-FSR) | The FSR 4 model without trails. |
| [NVIDIA DLSS SDK](https://github.com/NVIDIA/DLSS) | DLSS. |
| [FireBurn/FSR-Vulkan](https://github.com/FireBurn/FSR-Vulkan) | FSR 3.1, with the AMD FidelityFX SDK. |
| [pkgforge-dev/Anylinux-AppImages](https://github.com/pkgforge-dev/Anylinux-AppImages) | quick-sharun, which builds the AppImage. |
| [paulomanrique/ps4-pkg-extractor](https://github.com/paulomanrique/ps4-pkg-extractor) | The launcher's *Install from PKG*, on [orbis-pkg-util](https://crates.io/crates/orbis-pkg-util). |
| [herumi/xbyak](https://github.com/herumi/xbyak), [fmtlib/fmt](https://github.com/fmtlib/fmt) | Used by the shader translator and the online module. |
| [GoldHEN_Patch_Repository](https://github.com/GoldHEN/GoldHEN_Patch_Repository) | Game patches by Kyo, Lance McDonald, auser1337, illusion, emoose and the Bloodborne community: high frame rates, resolution, ultrawide and more. |
| [Nexus Mods: mod 30](https://www.nexusmods.com/bloodborne/mods/30) | Dommo's Xbox and Switch button prompts and stripped-down gestures menu, uploaded by goomab ([assets/menu_prompts](../assets/menu_prompts)). |

## bbport 0.7's contributors

This fork is built on bbport 0.7, which took pull requests and outside work from Qiming-Liu,
AndiMajore, adds39939, iannitram, maiconjsv, whp199, DominickCobb-rs, Sarxzer, wheat32,
ArenaMMORPG, guutol (Luís Gustavo P. Bomfim), redditor69, SrShadowy and Teefpyre, Supermedo and
Awaken, and in earlier releases SrDeTs, IgorWarzocha, itachi-re, Bainianzzz, hideoneric,
guitaripod, unTanana, andrR89, JuanraCM, SaeedShow, msisovic, AyrtonSanabio, axpico, Aryxa,
Obrikash and noelmiller. What each one did:
[bbport's list](https://github.com/deadinside28/bloodborne_pc/blob/master/docs/CONTRIBUTORS_0.7.md).

## People

- **[deadinside28](https://github.com/deadinside28)**: bbport, the port this whole project is built on,
  and 0.6's menu pointer and keyboard layout.
- **[Supermedo](https://github.com/Supermedo)**: online play, the cheats page, Add to Steam, and many
  fixes from the Windows port.
- **[0xCydral](https://github.com/0xCydral)**: gathered and adapted dozens of fixes (crashes while
  loading, black images, the upscaler, the performance line in the log).
- **[Awakenchan](https://github.com/Awakenchan)**: crash fixes (flips, descriptors, page faults),
  stick options, the controller in use, save import, the version selector, vertex shaders with
  the right bindings, stale vertex inputs read again, index buffers of indirect draws, and camera
  motion vectors without NaN.
- **[Classmg22](https://github.com/Classmg22)** (CLS_AMG): BBSC, Seamless Co-op.
- **[Wozzardman](https://github.com/Wozzardman)**: the server for a group's own co-op, and BBSC's seamless summon.
- **[droogie](https://github.com/droogie)**: The Hunter's Dream server, and fast loading (bbhost).
- **[fhody125-web](https://github.com/fhody125-web)**: NoDreamForHunter, the base of BBSC's game server.
- **[MikeTat1988](https://github.com/MikeTat1988)**: Hunter's Atlas, the fullscreen in-game map.
- **[IFreemz](https://github.com/IFreemz)**: the FSR 4 model without trails.
- **[FireBurn](https://github.com/FireBurn)**: FSR 3.1.
- **[Jhony-Jhansen](https://github.com/Jhony-Jhansen)**: keyboard movement (the last of two opposite keys wins).
- **[cassioKenji](https://github.com/cassioKenji)**: the keyboard sprint measurements.
- **[msisovic](https://github.com/msisovic)**: why loading hung after a lamp travel (guest thread handles above 40 bits).
- **[axpico](https://github.com/axpico)**: with VRAM full, the game waits for evicted textures to be freed instead of closing.
- **[emurphy04](https://github.com/emurphy04)**: a video player crash when it stops, the field of
  view, and an online crash guard.
- **[yumlevi](https://github.com/yumlevi)**: the black character preview, the loading screen's
  picture, and a crash on an unreadable shader program.
- **[GoncaloLobo0](https://github.com/GoncaloLobo0)**: crashes while loading areas.
- **[bmy](https://github.com/bmy)**: motion vectors for the large beasts, and a memory fault.
- **[Mrsuss60](https://github.com/Mrsuss60)**: the gestures menu from the keyboard, a deleted
  image's slot, and the log of failed memory reservations.
- **[SrShadowy](https://github.com/SrShadowy)**: the on-screen keyboard for the character's name,
  the shader compiling notice, and compacting the memory copies in VRAM.
- **[Wooloomooloo2](https://github.com/Wooloomooloo2)**: the game starting on integrated Intel Arc/Xe GPUs.
- **[Qiming-Liu](https://github.com/Qiming-Liu)**: the Simplified Chinese translation.
- **[andrecabralgit](https://github.com/andrecabralgit)**: the game's audio at full level.
- **[Jgamrot](https://github.com/Jgamrot)**: the in-game menu's checkboxes and sliders.
- **[GerasimosKan](https://github.com/GerasimosKan)**: trophy names without the key, and the
  sound when one is earned.
- **[artemkaVG](https://github.com/artemkaVG)**: a stencil buffer fix.
- **[parsifal295](https://github.com/parsifal295)**: the touchpad halves on Xbox pads.
- **[AyrtonSanabio](https://github.com/AyrtonSanabio)**: the in-game menu's language without the launcher.
- **[Aryxa](https://github.com/Aryxa)**: DLSS in the AppImage on NVIDIA.
- **[AndiMajore](https://github.com/AndiMajore)**: crash debugging (`BB_FAULT_WAIT`).
- **[iannitram](https://github.com/iannitram)**: FSR 3.1 without colour noise on the Ryzen Z1 (ROG Ally, Legion Go).
- **[whp199](https://github.com/whp199)**: the GX occlusion query guard against the 0x2169edc crash.
- **[nick24051998](https://github.com/nick24051998)**: the SRT walker without faults on null tables.

## Help and testing

- **[willthehuman](https://github.com/willthehuman)**: detailed reports with logs, and testing the fixes.
- **[nr1971](https://github.com/nr1971)**: the game not starting on some graphics cards, the
  camera speeding up on diagonals, and a crash on quitting.
- **[Joomzie](https://github.com/Joomzie)**: swapping A and B on Nintendo-style controllers.
- **[Kaka556Kevin](https://github.com/Kaka556Kevin)**: testing the video memory fix.
- **[segasonicye](https://github.com/segasonicye)**: why the game did not start in the Steam Deck's Game Mode.
- **[Monochrome0907](https://github.com/Monochrome0907)**: which effects freeze loading screens on NVIDIA.
- **[bruxis](https://github.com/bruxis)**: the log that showed why Steam Input did not reach the game.
- **[shauryasagar](https://github.com/shauryasagar)** and **[ZeroSTF](https://github.com/ZeroSTF)**: the Hunter's Dream going black after long sessions.
- **[popcar2](https://github.com/popcar2)**: ideas for the launcher.
- **[shaneo88](https://github.com/shaneo88)**: shadPS4's patch file in the patches folder.
- **[n3vrs0ft](https://github.com/n3vrs0ft)**: the "Transaction failed" crash on Seamless Hunt, the logs that stopped a BBSC guest from following a stranger's world, and testing BBSC 0.0.2 with a Windows player.
- **[cappp](https://github.com/cappp)**: the "Transaction failed" crash on Seamless Hunt.
- **[simo1730](https://github.com/simo1730)**: the Trophies page not finding the dump's files.
- **[Nahnahchi](https://github.com/Nahnahchi)**: logs and tests of a GPU freeze in a boss fight on NVIDIA, a crash in Yahar'gul, stretched models, a crash on the Steam Deck, effects turning black, rainbow textures, crashes in the game's memory manager, frame rate drops on NVIDIA, and Exit to Desktop with online play.
- **[thomasgarafano1](https://github.com/thomasgarafano1)**: Hunter's Atlas not preparing the map with a GOTY dump, and testing the fix.
- **[TacticalBill](https://github.com/TacticalBill)**: marking trophies already earned on the PS4.
- **[holydingus](https://github.com/holydingus)**: BBSC's items not given to a new character.
- **[OPGZ2](https://github.com/OPGZ2)**: the launcher's blank window at start.
- **[kuday248](https://github.com/kuday248)**: settings from the in-game menu that the launcher overwrote.
- **[BlazinKarp](https://github.com/BlazinKarp)**: the Steam overlay in the game.
- **[molnar-a](https://github.com/molnar-a)**: a crash on the Steam Deck after lamp travel, and testing the fix.
- **[Aman9das](https://github.com/Aman9das)**: asking for bbport 0.6's keyboard layout.
- **[eberhardweber](https://github.com/eberhardweber)**: logs and tests of AMD FX processors, fullscreen on Wayland with several monitors, and the AppImage's version in Gear Lever.
- **[GitBire](https://github.com/GitBire)**: the storage box with keyboard and mouse.
- **[npc-xc](https://github.com/npc-xc)**: logs of frame rate drops on NVIDIA.
