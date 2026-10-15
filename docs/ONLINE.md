# Online play and co-op

Online play is a beta. Messages, bloodstains and ghosts come from the community game server,
[The Hunter's Dream](https://thehuntersdream.com). Bells and summons go through a co-op pool,
and then the players' games connect to each other. Linux and Windows players can play together:
everyone needs the game at version 1.09 and the same pool.

> **shadPS4's public shadNet server no longer accepts bbport builds**: it signs the game out
> right after the login ("This shadNet server doesn't accept your shadPS4 build" in the log), and
> the launcher says so. The two pools for bbport are The Hunter's Dream's and a server of your own.

## The Hunter's Dream (with bbhost's players)

Choose **The Hunter's Dream (with bbhost players)** in the launcher's **Online** page.
[bbbridge](../bbbridge/README.md) by MaskZeus starts with the game, stands in for a shadNet server
on this computer and talks to The Hunter's Dream the way bbhost does, its relay included, so no
router port is needed. The account is The Hunter's Dream's, kept in `user/bbbridge` (no password):

- **Sign in with Discord**: the launcher shows a code and opens The Hunter's Dream's page; approve
  it there. The account is the same one bbhost uses.
- **Without Discord**: type a name and **Create**. Keep the recovery code the launcher shows:
  with the name, it brings the account back on another computer (**Recover**).

The game's play log (its own telemetry) stays blocked, so The Hunter's Dream's live map does not
show you.

## Your own server

Its owner creates the account ([SERVER.md](SERVER.md)).

1. In the launcher's **Online** page, turn on **Play online**, choose **Your own server** with
   its address, and enter the **account name** (not the email) and the password. The password is
   kept on this computer with the launcher's settings.
2. **Test the connection**: the game server, the shadNet server, its UDP port and its WebAPI
   should all answer, and with the account filled in, the sign-in should work. A wrong name or
   password shows there (the server does not say which of the two).

If the game says you are not signed in to PlayStation Network, the shadNet login failed: the log
then has a shadNet login error (code 8 is a wrong name or password). If the server did not answer
when the game started, the game keeps trying in the background.

## Seamless co-op (BBSC)

[BBSC](https://github.com/Classmg22/BBSC) (Bloodborne Seamless Co-op, by CLS_AMG) keeps a co-op
session going through deaths, lamps, areas, bosses and the Hunter's Dream, for up to 5 hunters:
the guest follows the host through lamps, sees the host's world (doors, bosses, lifts), keeps the
items and echoes it gets, and enemies get stronger for every guest. It runs inside the game
(`bbsc/`, loaded as `libbbsc.so`). It is new, and its own author marks much of it as untested.

1. In the launcher's **Online** page, turn on **Seamless co-op (BBSC)**. **BBSC settings** has its
   options (the same as in BBSC's Windows launcher); the defaults are BBSC's.
2. Every player of the session needs BBSC, the same version: on Linux this port, on Windows
   BBSC's package for the Windows port (its *BBport* release). A player without it plays the
   normal game.
3. The server decides how much of it works:
   - **BBSC's game server** (your group's, [SERVER.md](SERVER.md#seamless-co-op-bbsc), or BBSC's
     public one): everything, summons across areas and 5 hunters included. Set it as the
     **Game server** of the Online page.
   - **The Hunter's Dream**: the session stays together (deaths, lamps, bosses), but summons are
     the normal game's: BBSC turns its own summon changes and the 5 hunters off on public servers.
     Its messages go straight between the players.

   With BBSC and BBSC's game server, two players who cannot reach each other directly (CGNAT,
   strict routers, two games on one PC) are connected through that server's UDP relay (port
   3478); `SHADPS4_P2P_RELAY=0` turns it off. Without BBSC, and on The Hunter's Dream (bbbridge
   relays by itself), the relay is off.

BBSC gives every character its own items, which cost no Insight: the **Hunt Bell** (call other
players), the **Kin Bell** (join another player), the **Bloodlust Bell** (invade), the **Duel Bell**
(PvP on and off during co-op) and the **Parting Blank** (end co-op). It takes the game's Beckoning
Bell, Small Resonant Bell and Silencing Blank out of the inventory, and they do not come back when
BBSC is turned off. Before changing anything it backs the saves up to `user/bbsc/save-backups/`:
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
Tailscale ([SERVER.md](SERVER.md)) it goes through Tailscale: turn **UPnP** off and skip this
section. Otherwise each player has to be reachable from the Internet:

1. **The router.** With **UPnP** on (the default), the game opens its port on the router itself:
   the log says `UPNP: mapped UDP port <port>`. A router without UPnP needs a port forward by
   hand (UDP, the pinned port below, to your computer's LAN address).
2. **Pin the port** when you open it by hand or in a firewall: **Co-op port (UDP)** in the
   Online page, for example 3658 (0, the default, is a random port each time). The log then says
   `P2P transport ready: UDP physical_port=3658`.
3. **Open it in the firewall.** UPnP opens the port on the router only, not in this computer's
   firewall. With ufw or firewalld on, the launcher's **Online** page says
   so and gives the commands. For ufw:
   ```sh
   sudo ufw allow 3658/udp
   sudo ufw allow from <router IP> proto udp    # the router's UPnP answers
   ```
   On Windows, in a terminal as administrator:
   ```
   netsh advfirewall firewall add rule name="Bloodborne co-op" dir=in action=allow protocol=UDP localport=3658
   ```

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
| `Online: the shadNet server ... does not accept this build` | The server refuses bbport (shadPS4's public one): use The Hunter's Dream or your own server. |
| `event=0(DEAD)` | The connection gave up. |
