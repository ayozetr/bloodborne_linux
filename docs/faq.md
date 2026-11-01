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
- On **The Hunter's Dream**, BBSC keeps the session together, but summons are the normal game's:
  both hunters must be in the **same area**, the area's boss must still be alive in the host's world,
  and your levels must be within range.

[Seamless co-op on each server](ONLINE.md#seamless-co-op-bbsc).

## Do I need to open ports on my router?

No. With seamless co-op (BBSC) on, Seamless Hunt relays players who cannot reach each other
directly, and The Hunter's Dream's bridge relays by itself. Only [your own server](SERVER.md) needs a few ports, through Tailscale.

## How do I get a log on the Steam Deck?

Turn on *Advanced → Developer → Save the log and statistics to a file* once in Desktop Mode; Game
Mode sessions then save theirs too. [Getting a log](logs.md).

## The game updated and my Steam shortcut stopped working

Press **Add to Steam** again in the launcher: it updates the shortcut.
