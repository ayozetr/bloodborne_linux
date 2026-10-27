# Documentation

## For players

The same documents, with a few pages written for players, make up the
[players' guide](https://ayozetr.github.io/bloodborne_linux/) (built from this folder: `mkdocs.yml`; published with `tools/publish_guide.sh`).

- [getting-started.md](getting-started.md): what you need, the first launch, saves and updates.
- [steam-deck.md](steam-deck.md): Add to Steam, the Steam Deck's Game Mode, Steam Input and the overlay.
- [logs.md](logs.md): getting a log, also from Game Mode, and sending it.
- [faq.md](faq.md): the questions players ask most.
- [COMPATIBILITY.md](COMPATIBILITY.md): which releases of Bloodborne run, and which have been
  checked.
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md): common problems and what to do.
- [ONLINE.md](ONLINE.md): online play and co-op: the account, the bells, the ports.
- [SERVER.md](SERVER.md): hosting your own co-op server for a group of friends.
- [MODS.en.md](MODS.en.md): file mods and third-party patches.

## For developers

- [ENVIRONMENT.md](ENVIRONMENT.md): every environment variable the port reads, with its default
  and where in the code it is read.
- [DEBUGGING.md](DEBUGGING.md): catching a crash with a debugger (`BB_FAULT_WAIT`).
- [RELEASE_TEMPLATE.md](RELEASE_TEMPLATE.md): the format of every release's notes.
- [CREDITS.md](CREDITS.md): whose work is in the port, and its licenses.

## Design notes from upstream bbport

The port is built on [bbport](https://github.com/deadinside28/bloodborne_pc) by deadinside28. These
notes explain parts of its engine that this port still runs, and the code points to them. Some
describe plans or measurements at the date in their title.

- **GPU commands in parallel:** [parallel_gpu.md](parallel_gpu.md).
- **Upscaling, TAA and frame generation:** [upscaler.md](upscaler.md).
- **The translator that replaces emulation:** [TRANSLATOR_ARCHITECTURE.md](TRANSLATOR_ARCHITECTURE.md).
- **The GPU layer's memory module:** [MEMORY_MODULE_PLAN.md](MEMORY_MODULE_PLAN.md).

Upstream's release notes, roadmap, session logs and its other notes (most in Russian) stay in
[its docs folder](https://github.com/deadinside28/bloodborne_pc/tree/master/docs).
