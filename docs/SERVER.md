# Hosting your own co-op server

Bells and summons go through a shadNet server. Players who connect through shadPS4's public one
(`srv.shadps4.net`) get no co-op at the moment: it does not answer on its UDP port, so a summon
never connects ([deadinside28/bloodborne_pc#121](https://github.com/deadinside28/bloodborne_pc/issues/121)).
A group of friends can run their own server instead:
[shadnet-p2p](https://github.com/Wozzardman/shadnet-p2p) by Wozzardman, the shadNet server with
that UDP port working and a summon service of its own.

Messages, bloodstains and ghosts still come from The Hunter's Dream, whichever shadNet server you
use. Windows players of [Supermedo's port](https://github.com/Supermedo/bloodborne_pc) can join
the same server.

Tested with two players, one on this Linux port and one on Supermedo's Windows port, over
Tailscale, with the server below on a home server (Ubuntu 26.04): summons, a boss fight together
and summoning again after the helper died.

## How it fits together

- **One always-on computer runs the server:** a VPS, a home server, or one of the players' PCs
  (then it has to be on while you play).
- **Everyone joins one [Tailscale](https://tailscale.com) network** (a *tailnet*): the server and
  every player. Tailscale gives each computer an address starting with `100.` and encrypts the
  traffic between them. This matters: shadNet's login on TCP 31313 is not encrypted, so it should
  not be open to the Internet. And the games then reach each other over Tailscale too, so nobody
  has to open ports on their router.

| Protocol | Port | Used for |
|---|---|---|
| TCP | 31313 | Login and matchmaking |
| UDP | 31314 | Each player's address, for the other player of a summon |
| TCP | 31315 | WebAPI and the summon service |

## 1. Tailscale

On the server and on every player's computer, install Tailscale
([download](https://tailscale.com/download); on Linux `curl -fsSL https://tailscale.com/install.sh | sh`)
and sign in:

```sh
sudo tailscale up
```

The server's owner invites the players from the
[admin console](https://login.tailscale.com/admin/users) (**Users → Invite external users**),
and each player accepts the invitation and signs in on the computer they play on. Then, on the
server:

```sh
tailscale ip -4    # the server's address, 100.x.y.z: the players need it
tailscale status   # every player's computer should be listed
```

## 2. The server

### With Docker (any Linux)

This repository has a Docker image for it: [tools/shadnet-server](../tools/shadnet-server). It
builds shadnet-p2p on Debian 13, because shadnet-p2p needs Qt 6.8 or newer and some
distributions are older (Ubuntu 24.04 has Qt 6.4). It runs on any Linux with Docker, Ubuntu 24.04
included.

```sh
mkdir shadnet-server && cd shadnet-server
for f in Dockerfile entrypoint.sh; do
    curl -fsSLO "https://raw.githubusercontent.com/ayozetr/bloodborne_linux/main/tools/shadnet-server/$f"
done
docker build -t bbport-shadnet .
```

Then start it, with the server's Tailscale address and a signup code of your own (letters,
digits, `-` and `_`; the players never need it, only you, to create their accounts):

```sh
docker run -d --name shadnet --restart unless-stopped --network host \
    -v shadnet-data:/data \
    -e SHADNET_HOST=100.x.y.z \
    -e SHADNET_REGISTRATION_KEY=a-long-code-of-your-own \
    bbport-shadnet
docker logs shadnet
```

The log should end with the three listeners on the Tailscale address:

```text
Unsecured TCP listener on: 100.x.y.z:31313. No encryption, use it only on trusted networks
STUN UDP listener on: 100.x.y.z:31314
WebApiServer listening on: 100.x.y.z:31315
```

`SHADNET_HOST` keeps the server off the computer's other networks. After a reboot, it waits until
Tailscale is up. The configuration (`shadnet.cfg`) and the accounts (`db/shadnet.db`) live in the
`shadnet-data` volume. To stop or update the server:

```sh
docker stop shadnet && docker rm shadnet    # the volume, with the accounts, stays
docker build -t bbport-shadnet .            # after downloading a newer Dockerfile
```

Then run the same `docker run` again.

### Without Docker

Follow [shadnet-p2p's README](https://github.com/Wozzardman/shadnet-p2p#readme). It needs Qt 6.8
or newer: Arch Linux and its derivatives, Debian 13, Ubuntu 26.04, Fedora 41 or newer. On Debian
and Ubuntu, install `qt6-websockets-dev` along with the packages it lists, or CMake does not find
Qt's HTTP server module (checked on Debian 13 and Ubuntu 26.04). In `build/shadnet.cfg`, set `Host` to the server's Tailscale address (or
`0.0.0.0`), `Matching2Enabled=true` and `RegistrationSecretKey` to your signup code.

### A firewall on the server

With ufw, let the tailnet in:

```sh
sudo ufw allow in on tailscale0
```

## 3. Accounts

One account per player, created on the server with the signup code. The name is 3 to 16
letters, digits, `-` or `_`:

```sh
docker exec shadnet shadnet-sample 127.0.0.1 31313 register <name> <password> <email> <signup code>
```

`127.0.0.1` works only when the server listens on every address (`SHADNET_HOST` unset or
`0.0.0.0`). With `SHADNET_HOST` set, use that address instead. The tool answers
`Account created successfully.`, or `FAILED: Unauthorized` when the code is wrong. Give each player
their own name and password.

To back up the accounts, stop the server and copy the volume's `db/shadnet.db`.

## 4. Each player's launcher

In the **Online** page:

| Setting | Value |
|---|---|
| Play online | On |
| shadNet server | **Your own server** |
| Server address | `100.x.y.z` (the port, 31313, is added) |
| WebAPI address | Empty (the server's port 31315) |
| Online ID / Password | The player's own account |
| UPnP | Off (Tailscale needs no router ports) |

Then **Test the connection**. Every line should be green, the shadNet server's UDP among them: it
shows the address the server sees for you, a `100.` one through Tailscale. A red UDP line means
summons cannot connect: check that the server is running and that its log lists the UDP listener.

Summons go through the server's own summon service: the log of a game says
`Co-op: summon signs through http://100.x.y.z:31315`.

Windows players set the same server, WebAPI and account in the Windows port's launcher.

## Seamless co-op (experimental)

shadnet-p2p can also summon between different areas: the guest is moved to the host's area. To
use it, the server and every player must have it on:

- The server: add `-e SHADNET_BLOODBORNE_SEAMLESS_COOP=1` to `docker run`, or set
  `BloodborneSeamlessCoop=true` in `shadnet.cfg`. Its log then says `seamless co-op enabled`.
- Each player: **Seamless co-op (experimental)** in the launcher's Online page.

Ring the host's Beckoning Bell first, then the guest's Small Resonant Bell. Travelling together
by lantern once the session has started does not work yet.

## Troubleshooting

- **The log shows `127.0.0.1` or another address in the listeners:** check `SHADNET_HOST`, or
  `Host` in the `shadnet.cfg` beside the server's executable.
- **`Waiting for 100.x.y.z` in the log:** Tailscale is not up on the server, or the address is
  wrong (`tailscale ip -4`).
- **The game says it is not signed in to PlayStation Network:** a wrong name or password (code 8 in
  the log), or two players using one account.
- **The test is green but summons fail:** every player's computer must be in the tailnet, not only
  the server; `tailscale ping <player>` from each side. Everyone needs the game at version 1.09
  and the same co-op mode.

See also [ONLINE.md](ONLINE.md) for the bells, passwords and log lines of a summon.
