# Online play and co-op

Online play is a beta. Messages, bloodstains and ghosts come from a community game server:
Seamless Hunt's (the default) or [The Hunter's Dream](https://thehuntersdream.com). Bells and summons go through a co-op pool,
and then the players' games connect to each other. Linux and Windows players can play together:
everyone needs the game at version 1.09 and the same pool.

> **shadPS4's public shadNet server no longer accepts bbport builds**: it signs the game out
> right after the login ("This shadNet server doesn't accept your shadPS4 build" in the log), and
> the launcher says so. The pools for bbport are Seamless Hunt (the default), The Hunter's Dream's and a server of your own.

## Seamless Hunt

[Seamless Hunt](https://install.seamlesshunt.com) is a community server for Seamless Co-op (BBSC),
where Windows players join with BBSC's package for the Windows port.

1. In the launcher's **Multiplayer → Online** tab, turn on **Play online** and choose **Seamless Hunt**: its
   shadNet server, WebAPI and game server come with it.
2. Type a name and a password under **Account** and press **Create** (once). The server wants an
   email for each account; the launcher makes one from the name, as Seamless Hunt's own tool does.
3. Turn on BBSC in the **Seamless co-op (BBSC)** group and press **Test** in the **Status** row.

Its bloodstains and death visions crash the game with "Transaction failed", on Windows too: they
are off by default, as in Seamless Hunt's package (**Bloodstains on Seamless Hunt** brings them
back). Messages, ghosts and summon signs are not affected.

## The Hunter's Dream (with bbhost's players)

Choose **The Hunter's Dream (with bbhost players)** in the launcher's **Multiplayer → Online** tab.
The game's online module talks to The Hunter's Dream itself, the way bbhost does (from bbport 0.7):
nothing else runs next to the game. Its account is your Discord sign-in, the same one bbhost uses:

1. Press **Sign in with Discord**. The launcher shows a code, copies it and opens The Hunter's
   Dream's page.
2. On that page, press *Sign in with Discord to link* and sign in; back on the page, enter the code
   in the code field (not in *Sign in with a code from the game*).

No password is kept: the launcher keeps the sign-in's token with its settings. **Sign out** forgets
it. **Test** checks The Hunter's Dream's game server and its co-op service. Seamless co-op (BBSC)
is not available there.

Report problems here ([issues](https://github.com/ayozetr/bloodborne_linux/issues)), not to The
Hunter's Dream's support.

## Your own server

Its owner creates the account ([hosting your own server](SERVER.md)), or you make it with **Create** under
**Account** when the server lets anyone register.

1. In the launcher's **Multiplayer → Online** tab, turn on **Play online**, choose **Your own server** with
   its address, and enter the **account name** (not the email) and the password. The password is
   kept on this computer with the launcher's settings.
2. Press **Test** in the **Status** row: the game server, the shadNet server, its UDP port and its WebAPI
   should all answer, and with the account filled in, the sign-in should work. A wrong name or
   password shows there (the server does not say which of the two).

If the game says you are not signed in to PlayStation Network, the shadNet login failed: the log
then has a shadNet login error (code 8 is a wrong name or password). If the server did not answer
when the game started, the game keeps trying in the background.

## Seamless co-op (BBSC)

[BBSC](https://github.com/Classmg22/BBSC) (Bloodborne Seamless Co-op, by CLS_AMG) keeps a co-op
session going through deaths, lamps, areas, bosses and the Hunter's Dream, for up to 5 hunters:
the guest follows the host through lamps, sees the host's world (doors, bosses, lifts), keeps the
items and echoes it gets, and enemies get stronger for every guest. It runs inside the game's
online module (`gpu/bbnet20/bbsc`, BBSC 0.0.2 from bbport 0.7). It is new, and its own author
marks much of it as untested.

1. In the launcher's **Multiplayer → Online** tab, **Enable BBSC** in the **Seamless co-op (BBSC)**
   group (on by default). While it is on, BBSC's bells replace the game's; turned off, the game's
   come back the next time the character is loaded (the save is copied to `save-backups` first).
2. Every player of the session needs BBSC, the same version: on Linux this port, on Windows
   BBSC's package for the Windows port (its *BBport* release). A player without it plays the
   normal game.
3. The server decides how much of it works:
   - **BBSC's game server** (Seamless Hunt's, which comes with it, or your group's,
     [hosted with it](SERVER.md#seamless-co-op-bbsc)): everything, summons across areas and 5 hunters included. Set it as the
     **Game server** of the Online tab.
   - **The Hunter's Dream** has no BBSC: the normal game's co-op, with bbhost's players.

   With BBSC and BBSC's game server, two players who cannot reach each other directly (CGNAT,
   strict routers, two games on one PC) are connected through that server's UDP relay (port
   3478); `SHADPS4_P2P_RELAY=0` turns it off.

BBSC gives every character its own items, which cost no Insight: the **Hunt Bell** (call other
players), the **Kin Bell** (join another player), the **Bloodlust Bell** (invade), the **Duel Bell**
(PvP on and off during co-op) and the **Parting Blank** (end co-op). It takes the game's Beckoning
Bell, Small Resonant Bell and Silencing Blank out of the inventory, and they do not come back when
BBSC is turned off; BBSC's own items stay, with their names (scripts/bbsc_kit_texts.py), and work again
when it is back on. Before changing anything it backs the saves up to `user/bbsc/save-backups/`:
copy a character's save from there to play it without BBSC with its old bells. Its texts follow the game's language (Spanish, French, German, Italian,
Portuguese and Russian; English otherwise). **F8** puts you back on the ground if you get stuck
inside another player.

**Not yet tested with more than one player on Linux:** one player alone works (its items, deaths,
lamps, the Hunter's Dream). Report what you find with the log.

Its log is in `user/bbsc/logs/` (in the AppImage, `~/.local/share/bbport/user/bbsc/logs/`), and
the game's log has its warnings (`BBSC:` lines). Not in the Linux build: BBSC's cinematic camera
(L3 + R3 opens bbport's menu) and its own Discord status (bbport has one).

## Summoning in the game

- The host rings the **Beckoning Bell** (one Insight each time); the helper rings the **Small
  Resonant Bell**. With BBSC: the **Hunt Bell** and the **Kin Bell**, at no Insight cost.
- Use the same **password** in the game's network settings, so you find each other whatever
  your levels.
- Be in the same area, close to each other, with the area's boss still alive in the host's
  world.

## Ports

Co-op traffic is UDP, straight between the players' computers. With your own server on
Tailscale ([hosting your own server](SERVER.md)) it goes through Tailscale: turn **UPnP** off and skip this
section. Otherwise each player has to be reachable from the Internet:

1. **The router.** With **UPnP** on (the default), the game opens its port on the router itself:
   the log says `UPNP: mapped UDP port <port>`. A router without UPnP needs a port forward by
   hand (UDP, the pinned port below, to your computer's LAN address).
2. **Pin the port** when you open it by hand or in a firewall: **Co-op port (UDP)** in the
   Online tab, for example 3658 (0, the default, is a random port each time). The log then says
   `P2P transport ready: UDP physical_port=3658`.
3. **Open it in the firewall.** UPnP opens the port on the router only, not in this computer's
   firewall. With ufw or firewalld on, the launcher's **Multiplayer → Online** tab says
   so and gives the commands. For ufw:
   ```sh
   sudo ufw allow 3658/udp
   sudo ufw allow from <router IP> proto udp    # the router's UPnP answers
   ```
   Windows players open the same UDP port in their own firewall.

A router whose public address is shared by many customers (CG-NAT) cannot forward ports: the
log's `UPNP: IGD found - external IP=...` should be your real public address. Tailscale works
behind CG-NAT too.

## Reading the log

Run with `BB_GPU_LOG=info` in the extra variables for the online details. In a summon:

| Line | Meaning |
|---|---|
| `Logged in npid='...'` | The shadNet login worked. |
| `summon_messenger/create` | Your sign is placed (helper). |
| `summon_messenger/get`, `sceNpMatching2CreateJoinRoom`, `summon_messenger/request` | The host found the sign, made the room and sent the summon. |
| `peer '...' endpoint unresolved` | shadNet has no address for the other player: its UDP port did not answer. |
| `Online: the shadNet server ... does not accept this build` | The server refuses bbport (shadPS4's public one): use Seamless Hunt, The Hunter's Dream or your own server. |
| `event=0(DEAD)` | The connection gave up. |
