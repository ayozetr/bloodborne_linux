# FAQ

## Is this an emulator?

No. The game's own code runs directly on the CPU, and its graphics are translated to Vulkan. It is
built on [bbport](https://github.com/deadinside28/bloodborne_pc) by deadinside28.

## Where do I get the game?

From your own PS4: a dump of your copy with update 1.09. No game files are included, and none can
be shared here.

## Can I play with Windows players?

Yes. On Seamless Hunt or The Hunter's Dream, Linux and Windows players play together; for seamless
co-op everyone needs the same BBSC version (0.0.2). [Online play](ONLINE.md).

## Summons take a long time

Some waiting is normal: the game checks for summon signs about every 35 seconds, as the PS4's
servers had it, so a sign can take over half a minute to show up.

## My friend never gets summoned with the Kin Bell

It depends on the server:

- On **Seamless Hunt** (or your own server with BBSC's game server), seamless co-op works fully:
  summons across areas and up to 5 hunters.
- On **The Hunter's Dream** there is no seamless co-op: summons are the normal game's, with the
  Beckoning Bell and the Small Resonant Bell. Both hunters must be in the **same area**, the area's
  boss must still be alive in the host's world, and your levels must be within range (or use the
  same password).

[Seamless co-op on each server](ONLINE.md#seamless-co-op-bbsc).

## Do I need to open ports on my router?

Usually not: with **UPnP** on (the default) the game opens its port on the router by itself, and
with seamless co-op (BBSC) on Seamless Hunt relays players who cannot reach each other directly. A
router without UPnP, or a firewall on your computer, needs UDP 3658 opened
([ports](ONLINE.md#ports)). With [your own server](SERVER.md), Tailscale takes care of it.

## How do I use the in-game map?

In the launcher, **Mods → Map (Hunter's Atlas)**: turn on **In-game map** and press **Prepare**
once. It makes the maps from your own game files (it downloads about 200 MB of tools the first
time). In the game, choose **Map** in the quick menu (its fourth tile), press **M**, or with a
controller open the game's menu and click the right stick (R3). The port's menu (Insert, or hold
L3 + R3) changes the key and the controller shortcut.
**Travel to lamps from the map** and **Items on the map** are in the same launcher group.

## How do I get FSR 4.1.2 (INT8, for RDNA2 and the Steam Deck)?

FSR 4.1.2's models are built from AMD's own files, which can't be shipped here. In
**Graphics → Upscaler**, on **FSR 4.1.2 from AMD's driver**, press **Choose a file…** and pick
AMD's Adrenalin 26.10.1 or newer installer (the `.exe`) or the `amdxcffx64.dll` inside it. It also
needs AMD's FSR 4.1.x upscaler DLL (`amd_fidelityfx_upscaler_dx12.dll`, from OptiScaler or a game
with FSR 4.1): if you built FSR 4.1.1 before, it uses that one, otherwise it asks for it. It takes
about 4 minutes. In the game, the port's menu chooses the model (INT8 RDNA2 or INT8 Lite).

## How do I get a log on the Steam Deck?

Turn on *Advanced → Developer → Save the log and statistics to a file* once in Desktop Mode; Game
Mode sessions then save theirs too. [Getting a log](logs.md).

## The game updated and my Steam shortcut stopped working

Press **Add to Steam** again in the launcher: it updates the shortcut.
