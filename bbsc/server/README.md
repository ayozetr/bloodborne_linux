# Hosting BBSC for your group

Seamless co-op with everything on (summons across areas, five hunters) needs two servers that
your group shares:

| Server | What it does | Where it comes from |
|---|---|---|
| **shadNet** | Accounts, matchmaking, bells and summons | [shadnet-p2p](https://github.com/Wozzardman/shadnet-p2p) by Wozzardman |
| **BBSC's game server** | The server list, messages, bloodstains and BBSC's relay | [`gameserver/`](gameserver/README.md), in this folder |

Both can run on one always-on computer (a home server, a VPS, or one of the players' PCs) that every
player reaches through [Tailscale](https://tailscale.com), so no port is opened to the Internet.

## Quick start

The full guide, step by step, is [docs/SERVER.md](../../docs/SERVER.md). In short, on the server:

```sh
# shadNet, in seamless mode
docker build -t bbport-shadnet tools/shadnet-server
docker run -d --name shadnet --restart unless-stopped --network host -v shadnet-data:/data \
    -e SHADNET_HOST=100.x.y.z -e SHADNET_REGISTRATION_KEY=a-long-code-of-your-own \
    -e SHADNET_BLOODBORNE_SEAMLESS_COOP=1 bbport-shadnet

# BBSC's game server, next to it
docker build -t bbport-bbsc-server tools/bbsc-server
docker run -d --name bbsc-server --restart unless-stopped --network host \
    -v bbsc-data:/data -e BBSC_HOST=100.x.y.z bbport-bbsc-server
```

`100.x.y.z` is the server's Tailscale address (`tailscale ip -4`). Without Docker, the game server
is one Python file with nothing to install:

```sh
python3 bbsc/server/gameserver/bbsc_gameserver.py --shadnet 100.x.y.z --host 100.x.y.z
```

Then every player, in the launcher's **Multiplayer → Online** tab:

1. chooses **Your own server** with the server's address, and makes an account on it;
2. sets **Game server** to `http://100.x.y.z:20443`;
3. turns on BBSC in the **Seamless co-op (BBSC)** group.

## Ports

| Port | Protocol | Server | Used for |
|---|---|---|---|
| 31313 | TCP | shadNet | Sign-in and matchmaking |
| 31314 | UDP | shadNet | Finding each other's address (STUN) |
| 31315 | TCP | shadNet | Its web API: summon signs |
| 20443 | TCP | Game server | The server list, messages, bloodstains |
| 20444 | TCP | Game server | BBSC's relay: warps, world sync, enemy scaling |
| 18671 | TCP | Game server | Its bbhost-compatible service (`--no-bbhost` turns it off) |
| 3478 | UDP | Game server | Relay for players who cannot reach each other directly |

## What is in this folder

| Path | Contents |
|---|---|
| `gameserver/` | BBSC's game server (`bbsc_gameserver.py`), its `ss.info` template and notice text |
| `server/` | shadNet's settings as BBSC expects them (seamless co-op on, its ports, worlds and scoreboards) |

## Keep private

shadNet's registration key and its account database (the `shadnet-data` volume), and the game
server's data (`bbsc-data`), belong to your group: do not share them or publish them.
