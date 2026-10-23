# bbbridge

Co-op on **The Hunter's Dream** pool, with players of [bbhost](https://github.com/droogie/bbhost).

The game speaks shadNet, the online service shadPS4 uses; The Hunter's Dream speaks bbhost's
protocol. bbbridge sits between them on your own computer: to the game it is a shadNet server, and
to The Hunter's Dream it is one more bbhost client. It carries the matchmaking (rooms, bells,
summons), the traffic between the two games (with The Hunter's Dream's STUN and relay, so no router
port has to be opened) and the account. The game itself is not changed.

bbbridge is by [MaskZeus](https://github.com/MaskZeus/bbbridge). This folder holds its source, built
for Linux.

## How the port uses it

You never start it yourself:

1. In the launcher's **Multiplayer → Online** tab, choose **The Hunter's Dream (with bbhost players)**.
2. Sign in with Discord (the launcher shows a code and opens The Hunter's Dream's page), or make an
   account without Discord with **Create**, and keep the recovery code it shows.
3. Press **Play**: `run.sh` starts `bbbridge-cli` for that game and stops it when the game closes.

The account and the bridge's log are in `user/bbbridge/`. More in
[docs/ONLINE.md](../docs/ONLINE.md#the-hunters-dream-with-bbhosts-players).

> This connection is unofficial: The Hunter's Dream's team has not approved bbbridge and does not
> support this port. Report problems in this repository's
> [issues](https://github.com/ayozetr/bloodborne_linux/issues).

## Building and testing

`build.sh` builds it with the rest of the port, into `out/bbbridge/`. On its own:

```sh
cmake -S bbbridge -B out/bbbridge -G Ninja -DCMAKE_BUILD_TYPE=Release
ninja -C out/bbbridge bbbridge-cli bbbridge-unit
out/bbbridge/bbbridge-unit                                         # framing, signaling, STUN, protobuf
python3 bbbridge/tests/e2e/test_e2e.py out/bbbridge/bbbridge-cli   # against fake servers, offline
```

| Folder | Contents |
|---|---|
| `src/` | The bridge (`bridge.cpp`, `p2p.cpp`, `bbhost_client.cpp`…) and `main_cli.cpp`, the program the port runs |
| `tests/` | Unit tests (C++) and end-to-end tests (Python) |
| `third_party/` | nlohmann/json and Dear ImGui (MIT) |

`src/app.cpp` is bbbridge's own window, which only builds on Windows; the port does not use it.

## License

GPL-3.0-or-later (`LICENSE`); nlohmann/json and Dear ImGui are MIT (`THIRD_PARTY_NOTICES.txt`).
The protocol comes from bbhost and The Hunter's Dream by droogie. Not affiliated with Sony,
FromSoftware or The Hunter's Dream.
