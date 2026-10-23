# BBSC: Bloodborne Seamless Co-op

[BBSC](https://github.com/Classmg22/BBSC) by CLS_AMG keeps a co-op session together through deaths,
lamps, area changes, bosses and the Hunter's Dream, for up to five hunters who each keep their own
character. This folder holds BBSC 0.0.1 built for this port: the port's runtime loads it into the
game as `libbbsc.so`.

## What it does

- The session survives deaths, lamps, areas, bosses and trips to the Hunter's Dream; guests follow
  the host and come back with the group.
- Up to five hunters: the host and four guests.
- Everyone keeps their own levels, echoes and items; the host's boss kills and shortcuts can be
  shared with the guests' worlds.
- Enemies get stronger for every guest.
- Its own bells, with no Insight cost: the **Hunt Bell** (call others), the **Kin Bell** (join
  someone), the **Bloodlust Bell** (invade), the **Duel Bell** (PvP on or off) and the **Parting
  Blank** (end the session).

## Using it

In the launcher's **Multiplayer → Online** tab, turn on BBSC in the **Seamless co-op (BBSC)** group;
**BBSC settings** holds its options. Every player in the session needs BBSC, the same version. How much of it works
depends on the server (Seamless Hunt, a group's own server, or The Hunter's Dream): see
[docs/ONLINE.md](../docs/ONLINE.md#seamless-co-op-bbsc). To host a server for your group, see
[server/](server/README.md).

## What is in this folder

| Path | Contents |
|---|---|
| `emulator/src/core/` | BBSC's game code (`bloodborne_re.cpp`: the session, the bells, world sync) |
| `emulator/mod/` | The mod around it: relay, network channel, HTTP, settings (`mod.json`) |
| `emulator/mod/linux/` | The Linux side, written for this port: start-up, hooks, the Win32 names the mod uses |
| `server/` | Hosting a server: BBSC's game server and shadNet's settings |
| `translations/` | BBSC's texts in the game's languages |
| `third_party/` | fmt and xbyak |
| `CHANGES-bbport.md` | Every change this port made to BBSC, by date |

`build.sh` builds it into `out/bbsc/libbbsc.so`; on its own:

```sh
cmake -S bbsc -B out/bbsc -G Ninja -DCMAKE_BUILD_TYPE=Release
ninja -C out/bbsc
```

`LICENSE.txt`, `NOTICE.txt` and `SUPPORTERS.txt` are copied next to `libbbsc.so`, and BBSC stays off
without them, as it does in its own builds.

## Reporting problems

In this repository's [issues](https://github.com/ayozetr/bloodborne_linux/issues), with the game's
log from the launcher's **Log** page. Problems that also happen in BBSC's own builds belong in
[BBSC's repository](https://github.com/Classmg22/BBSC).

## License

GPL-2.0-or-later (`LICENSE`, `NOTICE.md`); the third-party parts keep their own licenses. BBSC's
credits are in `CREDITS.txt`, and this port's in [docs/CREDITS.md](../docs/CREDITS.md).
Bloodborne is by FromSoftware and Sony Interactive Entertainment; BBSC is a fan project, not
affiliated with either.
