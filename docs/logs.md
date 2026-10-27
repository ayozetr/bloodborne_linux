# Getting a log

A log is the first thing needed to fix a problem: it says what the game and the GPU were doing.

## From the launcher

1. Turn on *Advanced → Developer → Save the log and statistics to a file*. It stays on.
2. Play until the problem happens, then close the game.
3. The log is in `~/.local/share/bbport/logs`, named after the time the game started
   (`20261026_183438.log`). The launcher's **Log** page shows the last one too.

This also works when the game is started from Steam or from the Steam Deck's Game Mode: turn the
option on once in the launcher, and every session saves its log.

## Sending it

Open an [issue](https://github.com/ayozetr/bloodborne_linux/issues/new/choose) and attach the
`.log` file. It helps a lot to say:

- what happened, and roughly when (an area, a boss, a menu, after a lamp travel);
- your distribution, GPU and driver;
- the upscaler, preset and output resolution;
- for online problems, which server and whether seamless co-op (BBSC) was on, and the other
  player's log too if you can.

!!! note "Crashes"
    *Advanced → Developer → Crash diagnostics* adds checks that point at what went wrong in some
    crashes. The game runs a bit slower with it on: turn it on when asked in an issue.
