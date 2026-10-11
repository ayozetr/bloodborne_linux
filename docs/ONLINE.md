# Online play and co-op

Online play is a beta. Messages, bloodstains and ghosts come from the community game server,
[The Hunter's Dream](https://thehuntersdream.com). Bells and summons go through a shadNet server,
and then the players' games connect to each other directly. Linux and Windows players can play
together: everyone needs the game at version 1.09 and the same servers.

> **Co-op does not connect through shadPS4's public server.** It does not answer the UDP ping
> that tells it each player's address, so a summon times out
> ([deadinside28/bloodborne_pc#121](https://github.com/deadinside28/bloodborne_pc/issues/121));
> the shadPS4 team does not support forks. Messages, bloodstains and ghosts work. For co-op, a
> group runs its own server: [SERVER.md](SERVER.md). *Test the connection* tells which case
> yours is: the shadNet server's UDP line is red on the public server.

## Account

1. On shadPS4's public server, register at [shadnet.shadps4.net](https://shadnet.shadps4.net).
   On your own server, its owner creates the account ([SERVER.md](SERVER.md)).
2. In the launcher's **Online** page, turn on **Play online**, choose the **shadNet server**
   (shadPS4's public one or your own, with its address), and enter the **account name** (not the
   email) and the password. The password is kept on this computer with the launcher's settings.
3. **Test the connection**: the game server, the shadNet server, its UDP port and its WebAPI
   should all answer.

If the game says you are not signed in to PlayStation Network, the shadNet login failed. The
usual cause is the password: the log then has a shadNet login error (code 8 is a wrong
password). *Test the connection* only checks that the servers answer, not the account.

## Summoning in the game

- The host rings the **Beckoning Bell** (one Insight each time); the helper rings the **Small
  Resonant Bell**.
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
| `peer '...' endpoint unresolved` | shadNet has no address for the other player: its UDP port did not answer (the public server, above). |
| `event=0(DEAD)` | The connection gave up. |
