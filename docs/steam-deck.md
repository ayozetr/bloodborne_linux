# Steam and the Steam Deck

## Add to Steam

**Setup → Game → Add to Steam** puts *Bloodborne* in your Steam library as a non-Steam game. It
starts the game straight away, with the launcher's settings, without opening the launcher. Steam
has to close for it, and the launcher offers to do that.

After updating from an older release, press **Add to Steam** once more so the shortcut points to
the right place.

## On the Steam Deck

1. In Desktop Mode, download the AppImage and set the game up in the launcher, as in
   [Getting started](getting-started.md). A resolution of **720p** with an upscaler (FSR) suits the
   Deck's screen.
2. Press **Add to Steam**.
3. Back in Game Mode, start *Bloodborne* from your library.

To change a setting later, go back to Desktop Mode and open the launcher: what you change there is
what Game Mode uses.

!!! tip "Logs in Game Mode"
    Turn on *Advanced → Developer → Save the log and statistics to a file* once in Desktop Mode:
    every session played from Game Mode then saves its log too. [Getting a log](logs.md).

## Controllers and Steam Input

With Steam Input on, the game gets Steam's virtual controller. On a Wayland desktop the game then
opens its window through Xwayland, so Steam's input reaches it. With Steam Input off, the game reads
the controller itself. [More](TROUBLESHOOTING.md#the-controller-does-nothing-when-the-game-is-started-from-steam).

## The Steam overlay

Shift+Tab, Steam's FPS counter and F12 screenshots need **Steam overlay**, under *Add to Steam* in
the launcher (off by default), and the game started from Steam.
[More](TROUBLESHOOTING.md#the-steam-overlay-does-not-open-in-the-game).
