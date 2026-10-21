# SPDX-License-Identifier: GPL-2.0-or-later
"""Local co-op: one game per player on this PC, each in its part of the display, with its own
controller, saves and bbport.ini (the launcher's "Local co-op" group).

Every game takes the launcher's settings. Player 1 plays with them as they are (its saves, its
online account); players 2 to 4 get a data folder of their own under the launcher's (coop/
player<N>: generated files, saves, bbport.ini copied from player 1's the first time), no online
account and no Discord status. On top come the variables of the co-op groundwork (docs/
ENVIRONMENT.md): BB_GAMEPAD (the controller's device path, which tells two of one model apart),
BB_GAMEPAD_STRICT, BB_KEYBOARD=0 for the controller players, BB_PAD_BACKGROUND and BB_WINDOW_RECT
(a part of the display). The windows are placed through X11 (SDL_VIDEO_DRIVER=x11): Wayland lets no
window place itself.
"""
import os
import shutil
from pathlib import Path

MAX_PLAYERS = 4
KEYBOARD = "keyboard"  # a player's controller value for the keyboard and mouse

# The windows' parts of the display (x, y, width, height as fractions). Two players: one above the
# other or side by side; three and four: the quarters.
LAYOUTS = {
    "rows": [(0, 0, 1, 0.5), (0, 0.5, 1, 0.5)],
    "columns": [(0, 0, 0.5, 1), (0.5, 0, 0.5, 1)],
}
QUARTERS = [(0, 0, 0.5, 0.5), (0.5, 0, 0.5, 0.5), (0, 0.5, 0.5, 0.5), (0.5, 0.5, 0.5, 0.5)]

# The launcher settings players 2-4 do not share with player 1.
OWN_SETTINGS = {"user_dir": "", "gamepad": "", "gamepad_name": "", "discord": False,
                "online": False, "online_npid": "", "online_password": "", "online_accounts": {},
                "bbsc": False}
# Variables of the launcher's own environment that would send players 2-4 to player 1's files.
PLAYER_ONE_FILES = ("BB_USER_DIR", "BB_GPU_USER_DIR", "BB_CONFIG", "BB_PRESENCE_DIR")


def layout_rects(players, layout="rows"):
    """The window parts for `players` (2-4); three or four always take the quarters."""
    if not 2 <= players <= MAX_PLAYERS:
        raise ValueError(f"local co-op takes 2 to {MAX_PLAYERS} players")
    return LAYOUTS.get(layout, LAYOUTS["rows"]) if players == 2 else QUARTERS[:players]


def rect_text(rect):
    """BB_WINDOW_RECT's value: fractions with a point, whatever the locale."""
    return ",".join(f"{value:g}" for value in rect)


def data_dir(launcher_data, player):
    """Player 2-4's data folder; player 1's is the launcher's own."""
    return Path(launcher_data) / "coop" / f"player{player}"


def prepare_data_dir(launcher_data, player, ini_file):
    """Makes player 2-4's data folder, with player 1's bbport.ini the first time (the same
    graphics); an existing one is kept as the player left it."""
    folder = data_dir(launcher_data, player)
    folder.mkdir(parents=True, exist_ok=True)
    ini = folder / "bbport.ini"
    if not ini.exists() and Path(ini_file).is_file():
        shutil.copyfile(ini_file, ini)
    return folder


def player_settings(settings, player):
    """The launcher settings player `player` (1-based) plays with."""
    own = dict(settings)
    if player > 1:
        own.update(OWN_SETTINGS)
    return own


def player_environment(env, player, players, controller, layout="rows", sound_first_only=True,
                       folder=None):
    """`env` (the game's environment from player_settings) with player `player`'s window part,
    controller (a device path, or KEYBOARD) and, for players 2-4, data folder."""
    env = dict(env)
    env.update(SDL_VIDEO_DRIVER="x11", BB_PAD_BACKGROUND="1", BB_GAMEPAD_STRICT="1",
               BB_WINDOW_RECT=rect_text(layout_rects(players, layout)[player - 1]),
               BB_FULLSCREEN="0")
    if controller == KEYBOARD:
        env.pop("BB_GAMEPAD", None)  # strict and none chosen: no controller at all
        env.pop("BB_KEYBOARD", None)
    else:
        env["BB_GAMEPAD"] = controller
        env["BB_KEYBOARD"] = "0"
    if sound_first_only and player > 1:
        env["BB_AUDIO"] = "none"
    if folder is not None:
        for key in PLAYER_ONE_FILES:
            env.pop(key, None)
        env["BB_DATA_DIR"] = str(folder)
    return env


def problems(players, controllers, environ=None):
    """What keeps local co-op from starting: "x11" (no X server: the windows are placed through
    X11, XWayland in a Wayland session), "controller" (a player without one), "same controller"
    (two players with one) or "keyboard twice"."""
    chosen = list(controllers[:players])
    found = []
    if not (os.environ if environ is None else environ).get("DISPLAY"):
        found.append("x11")
    if len(chosen) < players or not all(chosen):
        found.append("controller")
    pads = [c for c in chosen if c and c != KEYBOARD]
    if len(pads) != len(set(pads)):
        found.append("same controller")
    if chosen.count(KEYBOARD) > 1:
        found.append("keyboard twice")
    return found
