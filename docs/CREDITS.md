# Credits

Everyone whose work is in this fork, and every project it took something from. Everyone listed
under *People* and *Help and testing* also appears in the launcher's **About** section. Components and their licenses: [BBPORT.md](../BBPORT.md#credits-and-licenses).

## Projects

| Project | What this fork takes from it |
|---|---|
| [deadinside28/bloodborne_pc](https://github.com/deadinside28/bloodborne_pc) | **bbport**, the native Linux port everything here is built on. Its README is [BBPORT.md](../BBPORT.md). |
| [Supermedo/bloodborne_pc](https://github.com/Supermedo/bloodborne_pc) | The Windows port: online play, DLSS, the cheats page, Add to Steam, the icon, the direct mouse camera, ultrawide, Quit to Desktop, the keyboard sprint and many fixes. |
| [Awakenchan/LanternEngine](https://github.com/Awakenchan/LanternEngine) (formerly BloodBorneButPc) | Video memory on 4 GB cards, crash fixes, fewer stutters while areas load, stick options, save import and the version selector. |
| [shadPS4](https://github.com/shadps4-emu/shadPS4) | The renderer and shader recompiler, and the online code. |
| [Wozzardman/shadp2p](https://github.com/Wozzardman/shadp2p) | The network and PSN libraries for online play. |
| [Wozzardman/shadnet-p2p](https://github.com/Wozzardman/shadnet-p2p) | The shadNet server for a group's own co-op server ([SERVER.md](SERVER.md)). |
| [MaskZeus/bbbridge](https://github.com/MaskZeus/bbbridge) | Co-op on The Hunter's Dream's pool ([bbbridge/](../bbbridge/)). |
| [Classmg22/BBSC](https://github.com/Classmg22/BBSC) | Seamless Co-op, by CLS_AMG, with Wozzardman's seamless summon ([bbsc/](../bbsc/)). |
| [fhody125-web/NoDreamForHunter](https://github.com/fhody125-web/NoDreamForHunter) | The base of BBSC's game server. |
| [MikeTat1988/HuntersAtlas](https://github.com/MikeTat1988/HuntersAtlas) | Hunter's Atlas: the fullscreen in-game map, its quick-menu tile, lamp travel and the map generator ([tools/hunters-atlas](../tools/hunters-atlas)), which runs with Grimrukh's [soulstruct](https://github.com/Grimrukh/soulstruct). |
| [The Hunter's Dream](https://thehuntersdream.com) | The online server, by droogie and its team; droogie's bbhost also brought fast loading after a death or travel. |
| [IFreemz/shadPS4-Bloodborne-DLSS-FSR](https://github.com/IFreemz/shadPS4-Bloodborne-DLSS-FSR) | The groundwork for DLSS, and the FSR 4 model without trails. |
| [NVIDIA DLSS SDK](https://github.com/NVIDIA/DLSS) | DLSS. |
| [FireBurn/FSR-Vulkan](https://github.com/FireBurn/FSR-Vulkan) | FSR 3.1, with the AMD FidelityFX SDK. |
| [pkgforge-dev/Anylinux-AppImages](https://github.com/pkgforge-dev/Anylinux-AppImages) | quick-sharun, which builds the AppImage. |
| [paulomanrique/ps4-pkg-extractor](https://github.com/paulomanrique/ps4-pkg-extractor) | The launcher's *Install from PKG*, on [orbis-pkg-util](https://crates.io/crates/orbis-pkg-util). |
| [herumi/xbyak](https://github.com/herumi/xbyak), [fmtlib/fmt](https://github.com/fmtlib/fmt) | Used by BBSC's Linux build. |
| [GoldHEN_Patch_Repository](https://github.com/GoldHEN/GoldHEN_Patch_Repository) | Game patches by Kyo, Lance McDonald, auser1337, illusion, emoose and the Bloodborne community: high frame rates, resolution, ultrawide and more. |
| [Nexus Mods: mod 30](https://www.nexusmods.com/bloodborne/mods/30) | Dommo's Xbox and Switch button prompts and stripped-down gestures menu, uploaded by goomab ([assets/menu_prompts](../assets/menu_prompts)). |
| [Nexus Mods: mod 537](https://www.nexusmods.com/bloodborne/mods/537) | Abken's KBM Icons Generator, which showed which textures keyboard prompts need (after [mod 460](https://www.nexusmods.com/bloodborne/mods/460)). |

## People

- **[deadinside28](https://github.com/deadinside28)**: bbport, the port this whole project is built on.
- **[Supermedo](https://github.com/Supermedo)**: online play, DLSS, the cheats page, Add to Steam,
  the icon, and many fixes from the Windows port.
- **[0xCydral](https://github.com/0xCydral)**: gathered and adapted dozens of fixes (crashes while
  loading, black images, the upscaler, the performance line in the log).
- **[Awakenchan](https://github.com/Awakenchan)**: video memory on 4 GB cards and crash fixes,
  fewer stutters while areas load, stick options, the controller in use, save import, the
  version selector, occlusion counters in command order, and vertex shaders with the right
  bindings.
- **[Classmg22](https://github.com/Classmg22)** (CLS_AMG): BBSC, Seamless Co-op.
- **[MaskZeus](https://github.com/MaskZeus)**: bbbridge.
- **[Wozzardman](https://github.com/Wozzardman)**: the online libraries and the co-op server.
- **[droogie](https://github.com/droogie)**: The Hunter's Dream server, and fast loading (bbhost).
- **[fhody125-web](https://github.com/fhody125-web)**: NoDreamForHunter, the base of BBSC's game server.
- **[MikeTat1988](https://github.com/MikeTat1988)**: Hunter's Atlas, the fullscreen in-game map.
- **[IFreemz](https://github.com/IFreemz)**: the groundwork for DLSS, and FSR 4 without trails.
- **[FireBurn](https://github.com/FireBurn)**: FSR 3.1.
- **[Jhony-Jhansen](https://github.com/Jhony-Jhansen)**: keyboard movement and the direct mouse camera.
- **[mcrib884](https://github.com/mcrib884)**: the bbmouse mouse camera, the basis of the direct camera.
- **[HatsyRei](https://github.com/HatsyRei)**: the keyboard walk key (in Mrsuss60's port).
- **[msisovic](https://github.com/msisovic)**: why loading hung after a lamp travel (guest thread handles above 40 bits).
- **[axpico](https://github.com/axpico)**: with VRAM full, the game waits for evicted textures to be freed instead of closing.
- **[pmwork-personal](https://github.com/pmwork-personal)**: ultrawide monitors without a stretched picture.
- **[emurphy04](https://github.com/emurphy04)**: ultrawide output and the HUD position, Quit to
  Desktop in the game's menus, and a video player crash when it stops.
- **[cassioKenji](https://github.com/cassioKenji)**: the keyboard sprint measurements.
- **[jpramosjp](https://github.com/jpramosjp)**: summons through the public shadNet server.
- **[yumlevi](https://github.com/yumlevi)**: the black character preview, the loading screen's
  picture and the texture cache's memory.
- **[devilismyfriend](https://github.com/devilismyfriend)**: the texture cache frees video memory in time.
- **[GoncaloLobo0](https://github.com/GoncaloLobo0)**: crashes while loading areas.
- **[bmy](https://github.com/bmy)**: the interface outside 1080p, motion vectors for the large
  beasts, and a memory fault.
- **[Mrsuss60](https://github.com/Mrsuss60)**: crashes when loading some maps, and the gestures
  menu from the keyboard.
- **[SrShadowy](https://github.com/SrShadowy)**: the on-screen keyboard for the character's name,
  and the shader compiling notice.
- **[Obrikash](https://github.com/Obrikash)**: the game starts when DLSS cannot be used.
- **[Qiming-Liu](https://github.com/Qiming-Liu)**: the Simplified Chinese translation.
- **[andrecabralgit](https://github.com/andrecabralgit)**: the game's audio at full level.
- **[Jgamrot](https://github.com/Jgamrot)**: the in-game menu's checkboxes and sliders.
- **[GerasimosKan](https://github.com/GerasimosKan)**: trophy names without the key, and the
  sound when one is earned.
- **[artemkaVG](https://github.com/artemkaVG)**: a stencil buffer fix.
- **[Vorshim92](https://github.com/Vorshim92)**: staying signed in on the public shadNet server.
- **[parsifal295](https://github.com/parsifal295)**: quitting from the menu with a controller,
  the menu within the screen, and the touchpad halves on Xbox pads.
- **[AyrtonSanabio](https://github.com/AyrtonSanabio)**: the in-game menu's language without the launcher.
- **[Aryxa](https://github.com/Aryxa)**: DLSS in the AppImage on NVIDIA.
- **[AndiMajore](https://github.com/AndiMajore)**: crash debugging (`BB_FAULT_WAIT`).
- **[AwesomeObserver](https://github.com/AwesomeObserver)**: large recorded command groups, and
  the swapchain after display changes.

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
- **[popcar2](https://github.com/popcar2)**: Quit to Desktop with online play on, and ideas for the launcher.
- **[shaneo88](https://github.com/shaneo88)**: shadPS4's patch file in the patches folder.
- **[n3vrs0ft](https://github.com/n3vrs0ft)**: the "Transaction failed" crash on Seamless Hunt, and the logs that stopped a BBSC guest from following a stranger's world.
- **[cappp](https://github.com/cappp)**: the "Transaction failed" crash on Seamless Hunt.
- **[simo1730](https://github.com/simo1730)**: the Trophies page not finding the dump's files.
- **[Nahnahchi](https://github.com/Nahnahchi)**: logs and tests of a GPU freeze in a boss fight on NVIDIA, and of a crash in Yahar'gul.
- **[thomasgarafano1](https://github.com/thomasgarafano1)**: Hunter's Atlas not preparing the map with a GOTY dump, and testing the fix.
