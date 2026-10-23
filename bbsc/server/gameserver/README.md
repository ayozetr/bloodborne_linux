# BBSC game server

The server that makes Bloodborne believe it is online, run by your own group instead of somebody
else.

## Why it exists

Before Bloodborne turns on any online feature it fetches its **server list**:

```
https://ss4.scej-network.jp:20443/bb-eu/ss.info
```

That file is base64-encoded XML. Its `<gameurl2>` block names one URL per game service (sign-in,
notices, messages, ghosts, summons, play logs) plus the timing and matching values the online
systems run on, and the game goes wherever it says. A private server works by answering that one
address. This one does, so a group's co-op does not depend on anybody else's machine staying up.

## What it does

| Service | Where it goes |
|---|---|
| The four `api_SummonData*` (summon signs) | The group's shadNet server, where co-op happens |
| Messages and bloodstains | Kept here and shared between the players (`--data`) |
| BBSC's relay (port 20444) | Here: warps, world sync and enemy scaling for BBSC |
| bbhost's services (port 18671, STUN/relay on UDP 3478) | Here, for players who cannot reach each other directly |
| Everything else (notices, play logs…) | Answered here, with empty but valid replies where nothing is kept |

## Running it

It is one Python 3 file with nothing to install:

```sh
python3 bbsc_gameserver.py --shadnet 100.x.y.z --host 100.x.y.z
```

Most groups run it with Docker next to their shadNet server instead: see
[the hosting guide](../README.md) and [docs/SERVER.md](../../../docs/SERVER.md#seamless-co-op-bbsc).
Players then set **Game server** to `http://100.x.y.z:20443` in the launcher's
**Multiplayer → Online** tab, which points the game's `ss.info` request here.

It logs every request it answers (`logs/gameserver-*.log`), the quickest way to see whether the
game is really talking to it.

| Option | Effect |
|---|---|
| `--shadnet ADDR` | **Required:** the shadNet server's address |
| `--host` / `--port` | Where to listen (`127.0.0.1:20443`) |
| `--advertise ADDR` | The address written into `ss.info`, when it differs from `--host` |
| `--relay-port N` | BBSC's relay port (20444; 0 turns it off) |
| `--summon-interval N` | Seconds between summon-sign checks (retail 35; 5 for quick summons) |
| `--level-range N` | Co-op level window (retail 20; 999 matches any level) |
| `--no-playlog` | No play-log uploads |
| `--no-bbhost` | Without bbhost's services |
| `--data FILE` | Where messages and bloodstains are kept (`online-data.json`) |
| `--log-dir DIR` | Where the logs go (`logs/`) |
| `--verbose` | Log request headers and bodies |

The defaults change nothing but the addresses: retuning is opt-in.

## Retail tuning values

From the real `ss.info`. They are not visible anywhere in the game, and several explain behaviour
that looks like a bug of the port.

| Tag | Retail | What it controls |
|---|---|---|
| `SummonDataGetListInterval2` | 35 | Seconds between checks for a summon sign |
| `SummonDataCreateInterval2` | 30 | How often a host posts its sign again |
| `SummonDataGetListGuardTimer2` | 60 | Guard timer on the sign list |
| `SummonDataGetListGetMaxCount2` | 20 | Most signs returned at once |
| `SummonDataCoopMatchingLevelUpperAbs2` | 20 | Co-op level window, upper |
| `SummonDataCoopMatchingLevelLowerAbs2` | −20 | Co-op level window, lower |
| `SummonDataBloodMadHunterPercent2` | 5 | Blood-mad hunter chance |
| `ReloadServerStatusInfoInterval2` | 300 | How often the game reads `ss.info` again |

`SummonDataGetListInterval2` is what "quick summoning" means: on retail values a sign can take over
half a minute to show up, and nothing inside the game changes that.

## Credits

By CLS_AMG, part of [BBSC](https://github.com/Classmg22/BBSC) (GPL-2.0-or-later). The `ss.info`
format, the list of services and the shapes of the replies come from
[NoDreamForHunter](https://github.com/fhody125-web) by fhody125 (MIT, `LICENSE.NoDreamForHunter`);
`ss_info_template.xml` is his file with the shadNet address left as a placeholder. This server is a
standalone rewrite of it, with no dependencies.
