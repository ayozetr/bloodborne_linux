#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Bloodborne launcher for the native port (GTK4 / libadwaita).

Picks the game folder, edits the port's settings (bbport.ini: upscaler, preset, ...) and the
start-up tweaks passed as environment variables to run.sh, starts and stops the game and shows
its output. Launcher settings live in ~/.config/bbport-launcher/settings.json.
Russian, English, Brazilian Portuguese and Simplified Chinese (bbport_i18n: the Russian
text is the key).
"""

import json
import shutil
import os
import re
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from pathlib import Path
from bbport_assets import fsr411_problem
from bbport_i18n import language, set_language, system_game_language, tr
import bbport_cache
import bbport_atlas_maps
import bbport_coop
import bbport_steam
import bbport_update

import gi

# GTK's GPU renderers cut the top row of pixels off text at fractional display scales (115 %:
# the "I" of "Idioma" lost its serif); cairo draws it whole, and a settings window needs no GPU.
# The game draws with its own Vulkan. GSK_RENDERER set by the user still wins.
os.environ.setdefault("GSK_RENDERER", "cairo")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk, Pango  # noqa: E402

PORT_DIR = Path(__file__).resolve().parent.parent  # native_probe (or the package's copy)
sys.path.insert(0, str(PORT_DIR / 'scripts'))
from mods import discover as discover_mods, unrecognized as unrecognized_mods  # noqa: E402
from prepare import sfo  # noqa: E402
import game_check  # noqa: E402
import online  # noqa: E402
import bbsc  # noqa: E402
import save_import  # noqa: E402
from patches import external_patches  # noqa: E402
import trophies  # noqa: E402
# Packaged (AppImage): generated files, saves and bbport.ini live in BB_DATA_DIR.
PACKAGED = bool(os.environ.get("BB_PREBUILT"))
DATA_DIR = Path(os.environ.get("BB_DATA_DIR", PORT_DIR))
LANTERN_ENGINE_URL = "https://github.com/Awakenchan/LanternEngine"
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "bbport-launcher"
CONFIG_FILE = CONFIG_DIR / "settings.json"
# The Journal shows the last MAX_LOG_LINES lines; Copy and Export take the whole session.
MAX_LOG_LINES = 5000
# FSR 4.1.1 assets built from the user's AMD DLL (tools/fsr4cap, also in the package).
FSR4CAP_DIR = PORT_DIR / "tools" / "fsr4cap"
sys.path.insert(0, str(FSR4CAP_DIR))
# The package's own environment (its Mesa, libraries, GTK modules) must not reach Proton's
# container: Proton runs the DLL on the system's drivers.
PACKAGE_ONLY_ENV = (
    "LD_LIBRARY_PATH", "VK_DRIVER_FILES", "VK_ICD_FILENAMES", "VK_ADD_DRIVER_FILES",
    "VK_LAYER_PATH", "VK_ADD_LAYER_PATH", "__EGL_VENDOR_LIBRARY_DIRS", "GDK_PIXBUF_MODULE_FILE",
    "GIO_EXTRA_MODULES", "GI_TYPELIB_PATH", "FONTCONFIG_FILE", "GSETTINGS_SCHEMA_DIR", "PYTHONPATH",
    "PYTHONHOME",
)
# build_assets.sh exit statuses (see there).
FSR411_BUILD_ERRORS = {
    2: "DLL не подходит: подробности в журнале",
    3: ("Не найден подходящий Proton: установите GE-Proton 10 или новее (ProtonUp-Qt) или Proton "
        "Experimental / Proton-CachyOS в Steam. Если они есть — запустите в Steam любую игру с "
        "этим Proton, чтобы Steam поставил его рантайм"),
    4: "Не хватает программ для сборки: список в журнале",
    5: ("Ни один Proton не запустил FSR 4.1 из этой DLL. Либо они слишком старые (подходят "
        "GE-Proton 10+, Proton Experimental, Proton-CachyOS 11), либо DLL не включает FSR 4.1 на "
        "этой видеокарте (Steam Deck?): тогда соберите на ПК с Radeon RX 7000/9000 и скопируйте "
        "папку fsr4_411. Подробности в журнале"),
    6: ("Записанные проходы не совпали с тем, что повторяет bbport (другая версия DLL или "
        "новая видеокарта?): подробности в журнале"),
    7: "Не найден загрузчик FidelityFX 2.x",
    8: ("На NixOS запись идёт на самой системе (systemd --user) через umu-launcher из nix-shell, "
        "а здесь их не нашлось: установите umu-launcher или Nix. Подробности в журнале"),
}

# Choices: (label, value). The first entry is the default. Labels are translated when shown.
UI_LANGUAGES = [("Как в системе", ""), ("Русский", "ru"), ("English", "en"), ("Português (Brasil)", "pt_BR"),
                ("Español", "es"), ("Italiano", "it"), ("Français", "fr"), ("Deutsch", "de"),
                ("简体中文", "zh_CN")]
UPSCALERS = [("FSR 4", "fsr4"), ("FSR 4.1.1", "fsr411"), ("FSR 3", "fsr3"),
             ("DLSS (NVIDIA RTX)", "dlss"),
             ("TAA (нативное сглаживание)", "taa"), ("Выключен", "off")]
PRESETS = [("Native AA", 0), ("Quality (x1.5)", 1), ("Balanced (x1.7)", 2),
           ("Performance (x2)", 3), ("Ultra Performance (x3)", 4)]
# "auto": the monitor's size (bbport_settings.cpp output_auto), fitted to the aspect ratio below.
OUTPUT_RES = [("Авто (по монитору)", "auto"),
              ("1280×720 (16:9)", "1280x720"), ("1920×1080 (16:9)", "1920x1080"),
              ("2560×1440 (16:9)", "2560x1440"), ("3840×2160 (16:9)", "3840x2160"),
              ("2560×1080 (21:9)", "2560x1080"), ("3440×1440 (21:9)", "3440x1440"),
              ("3840×1600 (21:9)", "3840x1600"), ("5120×2160 (21:9)", "5120x2160"),
              ("3840×1080 (32:9)", "3840x1080"), ("5120×1440 (32:9)", "5120x1440")]
# bbport.ini aspect_ratio (bbport_settings.cpp): the picture's shape; auto follows the output.
ASPECTS = [("Авто", "auto"), ("4:3", "4:3"), ("16:10", "16:10"), ("16:9", "16:9"), ("21:9", "21:9"),
           ("32:9", "32:9")]
# Anti-aliasing (bbport.ini anti_aliasing; the game's own AA switch follows it): auto = the game's
# own without an upscaler, none with one; the game's AA step with FXAA2_GS (after Kyo's patch,
# live); SMAA 1x on the finished scene, without an upscaler.
ANTI_ALIASING = [("Авто (игры без апскейлера)", "auto", "С апскейлером сглаживание игры выключено: оно только мылит его вход"),
                 ("Собственное игры", "game"), ("FXAA2_GS (игры)", "fxaa", "Применяется сразу"),
                 ("SMAA (без апскейлера)", "smaa", "Применяется сразу; с апскейлером не работает"), ("Выкл", "off")]
# bbport.ini texture_quality: large textures in VRAM at full, half or a quarter size.
TEXTURE_QUALITY = [("Авто", "auto", "Половина при 3 ГБ видеопамяти и меньше"), ("Полное", "full", ""),
                   ("Половина", "half", "Вдвое меньше по каждой стороне"),
                   ("Четверть", "quarter", "Вчетверо меньше по каждой стороне")]
# Frame generation (bbport.ini frame_generation and frame_generation_multiplier): DLSS on RTX
# 40/50 (NVIDIA's libnvidia-ngx-dlssg.so beside DLSS's); FSR 3.1 on any GPU (its row adds it).
NGX_FG_PREFIX = "libnvidia-ngx-dlssg.so."
FRAME_GENS = [("Выключена", "off"), ("DLSS 2x (NVIDIA RTX 40/50)", "dlss2"),
              ("DLSS 3x (NVIDIA RTX 50)", "dlss3"), ("DLSS 4x (NVIDIA RTX 50)", "dlss4")]
# bbport.ini low_latency: NVIDIA Reflex with DLSS frame generation, AMD Anti-Lag 2 elsewhere.
# How long L3+R3 is held to open the in-game menu (bbport.ini menu_pad_hold_ms; 0: Insert only).
MENU_PAD_HOLDS = [("Удерживать 0,8 с", "800"), ("Удерживать 2 с", "2000"),
                  ("Выключено (только Insert)", "0")]
LOW_LATENCIES = [("Включена", "on"), ("Включена + Boost", "boost"), ("Выключена", "off")]
# Game effects (patches applied at start): bbport.ini key, title, default.
EFFECTS = [
    ("effect_chromatic_aberration", "Хроматическая аберрация", True),
    ("effect_dof", "Глубина резкости (DoF)", True),
    ("effect_motion_blur", "Размытие в движении", True),
    ("effect_ssao", "Затенение SSAO", True),
    ("effect_bloom", "Свечение (Bloom)", True),
    ("effect_dynamic_shadows", "Тени от динамических источников", True),
    ("effect_ssr", "Отражения SSR (не было в игре)", False),
    # Not graphics: under Mods, in their own group (GAME_MENU_EFFECTS).
    ("skip_intro", "Пропуск заставок при запуске", False),
    ("debug_camera", "Свободная камера (Cross + L3)", False),
    ("debug_menu", "Debug menu (левый touchpad / Tab; нужны шрифты)", False),
]
# The EFFECTS that change the game's menus or open its debug tools, not the picture.
GAME_MENU_EFFECTS = ("skip_intro", "debug_camera", "debug_menu")
# Cheats and gameplay tweaks (community patches for 1.09, applied at start): bbport.ini key, title,
# subtitle. All off by default.
CHEATS = [
    ("cheat_no_death", "Бессмертие", "Урон проходит, но здоровье не опускается ниже 1"),
    ("cheat_stealth", "Невидимость", "Враги не видят вас и не реагируют, пока вы не атакуете"),
    ("cheat_silent", "Бесшумность", "Враги не слышат вас, но видят"),
    ("cheat_rally_no_decay", "Rally не угасает", "Здоровье для Rally не исчезает со временем"),
    ("cheat_enemy_control", "Управление врагом", "R3: управлять целью, L3: вернуться. "
                                                  "Не вместе со свободной камерой"),
]
TWEAKS = [
    ("tweak_no_rally", "Без Rally", "Атаки не возвращают здоровье"),
    ("tweak_camera_distance", "Камера дальше", "Камера дальше от персонажа"),
    ("tweak_no_camera_rotation", "Без автоповорота камеры",
     "Камера не поворачивается сама при движении; ручное управление и захват цели работают"),
    ("tweak_easy_run", "Бег с меньшим наклоном стика", "Бег примерно с 70% наклона стика вместо 90%"),
    ("tweak_ragdoll", "Физика тел как в Dark Souls", "Тела и предметы разлетаются от ударов"),
]
# Loading and smoothness (patches from bbhost, applied at start): bbport.ini key, title, subtitle,
# default.
STREAMING = [
    ("tweak_quick_reentry", "Быстрая загрузка после смерти",
     "Загрузка после смерти или перемещения у лампы идёт, пока грузится область (2–3 с), а не "
     "минимум 12 с", True),
    ("tweak_fast_deflate", "Без рывка каждые ~50 с",
     "Игра быстрее сжимает запись игрока: пропадает рывок ~23 мс примерно каждые 50 с", True),
    ("tweak_post_processors", "Третий поток подготовки ресурсов",
     "Во время игры работают три потока подготовки ресурсов, а не два. Экспериментально", False),
]
MODEL_LOD = [("Как в игре", "0"), ("Максимальная (-2)", "-2"), ("Ниже (1)", "1"),
             ("Минимальная (2)", "2")]
FPS_MODES = [("Без ограничения (патч)", "uncap"), ("60", "60"), ("90", "90"),
             ("30 (как на PS4)", "30")]
PRESENT_MODES = [
    ("Mailbox", "Mailbox", "По умолчанию: без разрывов и с малой задержкой; видеокарта работает больше"),
    ("FIFO (VSync)", "Fifo", "Без разрывов, не чаще частоты экрана: чуть больше задержка, меньше нагрузка "
                             "(хорошо для Steam Deck)"),
    ("FIFO Relaxed", "FifoRelaxed", "Как VSync, но опоздавший кадр даёт разрыв вместо рывка"),
    ("Immediate", "Immediate", "Наименьшая задержка, с разрывами изображения"),
]
# A third element is a note shown under the row's title while that choice is selected: the
# choice labels stay short, so the selected one is shown in full.
DRAW_PIPE = [("Авто", "", "Включён при 8 и более потоках процессора"), ("Включён", "1"),
             ("Выключен", "0", "Стабильнее, но медленнее")]
# Hunter's Atlas's map preparation (bbport_atlas_maps): its steps and errors, and the languages
# of the names in the maps (the game's text folders, in their own language).
ATLAS_STEPS = {"uv": "Загрузка uv", "python": "Установка Python", "packages": "Установка библиотек генератора",
               "maps": "Создание карт", "names": "Названия на языке игры", "art": "Оформление карты",
               "install": "Установка карт"}
ATLAS_ERRORS = {
    "game": "Нет eboot.bin в папке игры",
    "space": "Недостаточно места в папке данных: нужно около 900 МБ",
    "uv": "Не удалось скачать uv ({}). Проверьте подключение к интернету и попробуйте снова",
    "python": "Не удалось установить Python ({}). Проверьте подключение к интернету и попробуйте снова",
    "packages": "Не удалось установить библиотеки генератора ({}). Проверьте подключение к интернету и попробуйте снова",
}
ATLAS_LANGUAGE_NAMES = {"engus": "English", "enggb": "English", "spaes": "Español", "spaar": "Español (LatAm)",
                        "frafr": "Français", "deude": "Deutsch", "itait": "Italiano", "porbr": "Português (BR)",
                        "porpt": "Português", "rusru": "Русский", "jpnjp": "日本語", "korkr": "한국어",
                        "zhocn": "简体中文", "zhotw": "繁體中文", "nldnl": "Nederlands", "polpl": "Polski",
                        "finfi": "Suomi", "swese": "Svenska", "dandk": "Dansk", "norno": "Norsk", "turtr": "Türkçe"}
COOP_LAYOUTS = [("Один над другим", "rows"), ("Рядом", "columns")]
# Local co-op: the other players start this many seconds apart (each prepares its files and takes
# its window's place in turn).
COOP_START_DELAY = 8
# The button prompts (bbport.ini button_prompts, runtime_pad/bindings.c): automatic follows the
# device used last; the game draws them live (gpu/shim/bbport_button_prompts.cpp).
PROMPT_CHOICES = [("Автоматически (по контроллеру)", "auto"), ("PlayStation (оригинал)", "playstation"),
                  ("Xbox", "xbox"), ("Nintendo Switch", "switch"), ("Клавиатура", "keyboard")]
# The game's language: the PS4 system language ("": from the desktop's locale).
LANGUAGES = [("Как в системе", ""), ("Английский", "1"), ("Русский", "8"), ("Японский", "0"), ("Французский", "2"),
             ("Испанский", "3"), ("Немецкий", "4"), ("Итальянский", "5")]
# Issue #269 (scripts/patches.py language_writes): the game's own text and voice language, any
# the files have, whatever the system language, the copy's region and the save chose.
GAME_TEXT_LANGUAGES = [("Как выберет игра", "auto"), ("English (US)", "enus"), ("English (UK)", "engb"),
                       ("Русский", "ruru"), ("日本語", "jajp"), ("Français", "frfr"), ("Italiano", "itit"),
                       ("Deutsch", "dede"), ("Español", "eses"), ("Español (Latinoamérica)", "esar"),
                       ("Português (Brasil)", "ptbr"), ("Português", "ptpt"), ("Nederlands", "nlnl"),
                       ("Polski", "plpl"), ("Dansk", "dadk"), ("Norsk", "nono"), ("Suomi", "fifi"),
                       ("Svenska", "svse"), ("Türkçe", "trtr"), ("中文（简体）", "zhcn"),
                       ("中文（繁體）", "zhtw"), ("한국어", "kokr")]
GAME_VOICE_LANGUAGES = [("Как выберет игра", "auto"), ("English", "engb"), ("日本語", "jajp"),
                        ("Français", "frfr"), ("Italiano", "itit"), ("Deutsch", "dede"),
                        ("Español", "eses"), ("Español (Latinoamérica)", "esar"),
                        ("Português (Brasil)", "ptbr")]
READBACKS = [("Мягкие", "", "По умолчанию: без них у персонажей «взрываются» вершины"),
             ("Выключены", "0", "Быстрее, но персонажи могут искажаться"),
             ("Точные", "2", "Самые точные и самые медленные: для поиска ошибок")]

DEFAULTS = {
    "ui_language": "",
    "game_dir": "" if PACKAGED else str(PORT_DIR.parent / "CUSA03173"),
    "user_dir": "",
    "dlc_dir": "",
    "mods_dir": "",
    "mods_enabled": True,
    "patches_dir": "",
    "language": "",
    "check_updates": True,
    "fullscreen": False,
    "hdr": False,
    "present_mode": "Mailbox",
    "gamepad": "",
    "gamepad_name": "",
    "display": "",
    # The GPU by its Vulkan name ("" = the port's choice: a discrete one first).
    "gpu": "",
    "skip_network_choice": True,
    "fps_mode": "uncap",
    "fps_limit": 0,
    "draw_pipe": "",
    "readbacks": "",
    "mangohud": False,
    "frame_stats": False,
    "save_log": False,
    "crash_diag": False,
    "gpu_profile": False,
    "vk_validation": False,
    "extra_env": "",
    "discord": True,
    # Off: BB_STEAM_OVERLAY=0 (run.sh); on, the packaged entry's choice (Steam's own overlay).
    "steam_overlay": True,
    # The PS4's trophy key (shadPS4's TrophyKey): the trophies' names (scripts/trophies.py).
    "trophy_key": "",
    # Co-op (Multiplayer, Online tab): off by default; Seamless Hunt's server and The Hunter's Dream.
    # online_server_kind: "own", "seamlesshunt" or "thd" (docs/SERVER.md); unset or the old "public"
    # (shadPS4's server, which signs this port out), online.server_kind gives Seamless Hunt.
    "online": False,
    "online_community": online.COMMUNITY_SERVER,
    "online_server_kind": None,
    "online_server": online.SHADNET_SERVER,
    "online_webapi": "",
    "online_npid": "",
    "online_password": "",
    # The account of each kind of server ({"own": {"npid", "password"}, "seamlesshunt": ...}): the
    # Online tab swaps them when the server changes; online_npid/password are the chosen one's.
    "online_accounts": {},
    "online_upnp": True,
    # Seamless Hunt's bloodstains and death visions, off by default: they crash the game there
    # (scripts/online.py, SEAMLESSHUNT_TOMBS).
    "online_seamlesshunt_tombs": False,
    "online_p2p_port": 0,  # 0: the online module's own, 3658 (BB_P2P_PORT)
    "online_seamless": False,
    # The Hunter's Dream: its address ("": thehuntersdream.com) and the Discord sign-in's account.
    "thd_server": "",
    "thd_online_id": "",
    "thd_token": "",
    # Seamless co-op (BBSC): on or off, and the options the player changed ({mod.json id: value}).
    "bbsc": True,
    "gestures_no_motion": False,  # the gestures menu without motion-control icons
    "bbsc_options": {},  # BBSC's options the player changed (scripts/bbsc.py)
    # Local co-op (its page, bbport_coop.py): the players, the layout for two, each player's
    # controller (a device path or "keyboard") and whether players 2-4 are silent.
    "coop_players": 2,
    "coop_layout": "rows",
    "coop_controllers": [],
    "coop_sound_first_only": True,
    # The monitor the players' windows share ("": the game's, Graphics → Monitor).
    "coop_display": "",
    # Hunter's Atlas (its group in Settings): the in-game map, off by default; lamp travel and items.
    "atlas": False,
    "atlas_travel": True,
    "atlas_items": True,
    # A copy of the saves before each game (Setup → Saves, save_import.auto_backup): off by
    # default; how many copies stay.
    # Play with an account set and "Play online" off asks which (on_launch), unless told not to.
    "ask_online_off": True,
    # The sticks' inner dead zone in percent of their travel (BB_PAD_DEADZONE, of 127; the port's
    # default 5 is 4 %).
    "pad_deadzone": 4,
    "pad_lightbar": False,
    "pad_lightbar_colour": "#b00000",
    "saves_auto_backup": False,
    "saves_auto_backup_keep": 5,
}

# bbport.ini keys the launcher edits; the rest of the file is kept.
INI_DEFAULTS = {
    "upscaler": "fsr4",
    "preset": "4",
    "sharpen": "1",
    "sharpness": "0.50",
    "object_motion": "1",
    "show_fps": "1",
    "output_res": "auto",
    "aspect_ratio": "auto",
    "anti_aliasing": "auto",
    "texture_quality": "auto",
    "vbao": "0",
    "model_lod": "0",
    "frame_generation": "off",
    "frame_generation_multiplier": "2",
    "low_latency": "on",
    "fov": "43",
    "mute_unfocused": "0",
    "game_text_language": "auto",
    "game_voice_language": "auto",
    "button_prompts": "auto",
    "mouse_look": "1",
    "mouse_sensitivity": "1.00",
    "mouse_invert_y": "0",
    "mouse_invert_x": "0",
    "menu_pad_hold_ms": "800",
    "camera_speed_x": "1.00",
    "camera_speed_y": "1.00",
    "keyboard_layout": "0.7",
    "pad_swap_sticks": "0",
    "pad_invert_look_x": "0",
    "pad_invert_look_y": "0",
    "pad_camera_diagonal": "0",
    **{key: "1" if default else "0" for key, _, default in EFFECTS},
    **{key: "0" for key, _, _ in CHEATS + TWEAKS},
    **{key: "1" if default else "0" for key, _, _, default in STREAMING},
}


def load_settings():
    settings = dict(DEFAULTS)
    try:
        settings.update(json.loads(CONFIG_FILE.read_text(encoding='utf-8')))
    except (OSError, ValueError):
        pass
    return settings


def number(value, default, kind=float, where="bbport.ini", key=""):
    """A saved setting as a number; one that is not (written by hand, or by another version) keeps
    the default instead of stopping the launcher (issue #18: a blank window). A decimal comma
    (bbport.ini as earlier AppImages wrote it in the user's language) reads as a point."""
    if kind is float and isinstance(value, str) and value.count(",") == 1 and "." not in value:
        value = value.replace(",", ".")
    try:
        return kind(value)
    except (TypeError, ValueError):
        print(f"{where}: {key}={value!r} is not a number; {default} is used", file=sys.stderr)
        return kind(default)


def save_settings(settings):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.touch(mode=0o600)
    CONFIG_FILE.chmod(0o600)  # it holds the shadNet password
    CONFIG_FILE.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")


def ini_path():
    return Path(os.environ.get("BB_CONFIG", DATA_DIR / "bbport.ini"))


def load_ini():
    values = dict(INI_DEFAULTS)
    lines = []
    try:
        lines = ini_path().read_text(encoding='utf-8').splitlines()
    except OSError:
        pass
    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values, lines


def save_ini(values, lines):
    """Rewrites the edited keys in place, appends missing ones, keeps comments and others; a key
    whose value is None is removed (a control binding back to its default)."""
    written = set()
    out = []
    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in values:
                if values[key] is not None:
                    out.append(f"{key}={values[key]}")
                written.add(key)
                continue
        out.append(line)
    if not lines:
        out.append("# bbport settings (in-game menu: Insert / L3+R3)")
    for key, value in values.items():
        if key not in written and value is not None:
            out.append(f"{key}={value}")
    ini_path().write_text("\n".join(out) + "\n", encoding="utf-8")


def keyboard_layout_once(settings, values, lines):
    """bbport 0.7's keys became the default (keyboard_layout=0.7, Dark Souls III's on PC); the
    Linux fork's own keys are keyboard_layout=classic (runtime_pad/bindings.c). Earlier launchers
    wrote keyboard_layout=bbport (the fork's keys) or 0.6 (0.7's) into bbport.ini: each player keeps
    the keys they had. Once."""
    if settings.get("keyboard_layout_07"):
        return
    old = values.get("keyboard_layout")
    if old in ("bbport", "0.6"):
        values["keyboard_layout"] = "classic" if old == "bbport" else "0.7"
        save_ini({"keyboard_layout": values["keyboard_layout"]}, lines)
        lines[:] = ini_path().read_text(encoding="utf-8").splitlines()
    settings["keyboard_layout_07"] = True
    save_settings(settings)


def button_prompts_once(settings, values, lines):
    """The button prompts moved from the launcher's settings (prompts, "" automatic) to bbport.ini
    (button_prompts), which the game reads and its menu edits. Once."""
    if "prompts" not in settings:
        return
    old = settings.pop("prompts") or "auto"
    if not any(line.strip().startswith("button_prompts=") for line in lines):
        values["button_prompts"] = old
        save_ini({"button_prompts": old}, lines)
        lines[:] = ini_path().read_text(encoding="utf-8").splitlines()
    save_settings(settings)


def migrate_ini(settings, values, lines):
    """Earlier launchers' settings as 0.7 reads them (keyboard layout, button prompts)."""
    keyboard_layout_once(settings, values, lines)
    button_prompts_once(settings, values, lines)


def patches_dir(settings):
    return Path(settings.get("patches_dir") or DATA_DIR / "patches").expanduser()


def dlc_addons(dlc, title_id):
    """Entitlement labels of this title's add-ons in a DLC folder: subfolders named by the label
    (as the runtime reports them, from <user>/addcont/<title id>/<label>) with a param.sfo of
    CATEGORY ac and this title's CONTENT_ID."""
    found = []
    for folder in sorted(Path(dlc).iterdir()) if Path(dlc).is_dir() else []:
        try:
            info = sfo((folder / "sce_sys/param.sfo").read_bytes())
        except (OSError, ValueError, IndexError):
            continue
        content = str(info.get("CONTENT_ID", ""))
        if info.get("CATEGORY") == "ac" and content[7:16] == title_id and content[20:] == folder.name:
            found.append(folder.name)
    return found


# DLSS (vk_dlss.cpp): the bridge (libbbport_dlss.so) and NVIDIA's runtime library
# libnvidia-ngx-dlss.so.<version>, beside bb-probe (the package, a build with DLSS_SDK_ROOT) or the
# player's own in <user>/dlss, which the game prefers. Linux needs the .so from NVIDIA's DLSS SDK
# (github.com/NVIDIA/DLSS, lib/Linux_x86_64/rel); a game's nvngx_dlss.dll is Windows-only.
NGX_PREFIX = "libnvidia-ngx-dlss.so."
DLSS_SDK_URL = "https://github.com/NVIDIA/DLSS/tree/main/lib/Linux_x86_64/rel"


def binaries_dir():
    return PORT_DIR / ("bin" if PACKAGED else "out")


def dlss_dir():
    """Where the game looks for the bridge and NVIDIA's library: BB_DLSS_DIR (the AppImage's
    copy, tools/build_dlss.sh), else beside bb-probe."""
    return Path(os.environ["BB_DLSS_DIR"]) if os.environ.get("BB_DLSS_DIR") else binaries_dir()


def ngx_libraries(directory, prefix=NGX_PREFIX):
    """NVIDIA's DLSS runtime libraries in directory (with NGX_FG_PREFIX, its frame generation's),
    newest version last."""
    def version(path):
        return tuple(int(p) if p.isdigit() else 0 for p in path.name[len(prefix):].split("."))
    try:
        return sorted((p for p in Path(directory).iterdir() if p.name.startswith(prefix)), key=version)
    except OSError:
        return []


def ngx_prefix_of(name):
    """Which of NVIDIA's libraries a file name is: NGX_PREFIX, NGX_FG_PREFIX or None."""
    for prefix in (NGX_FG_PREFIX, NGX_PREFIX):  # the longer first: "dlss.so." is not "dlssg.so."
        if name.startswith(prefix):
            return prefix
    return None


def frame_gen_choice(ini):
    """FRAME_GENS' value from bbport.ini frame_generation and frame_generation_multiplier."""
    mode = ini.get("frame_generation", "off")
    if mode == "dlss":
        multiplier = ini.get("frame_generation_multiplier", "2")
        return f"dlss{multiplier}" if multiplier in ("2", "3", "4") else "dlss2"
    return mode if mode in ("off", "fsr3") else "off"


def frame_gen_ini(choice):
    """bbport.ini's frame_generation and frame_generation_multiplier for a FRAME_GENS value."""
    if choice.startswith("dlss"):
        return {"frame_generation": "dlss", "frame_generation_multiplier": choice[4:] or "2"}
    return {"frame_generation": choice}


def fsr411_dir():
    """Where the FSR 4.1.1 assets are looked up, as run.sh does."""
    if os.environ.get("BB_FSR411_DIR"):
        return Path(os.environ["BB_FSR411_DIR"])
    return PORT_DIR / "fsr4_411" if (PORT_DIR / "fsr4_411").is_dir() else DATA_DIR / "fsr4_411"


def fsr411_build_command(upscaler, loader=None):
    """tools/fsr4cap/build_assets.sh for the user's DLL: command and environment. The package
    writes into the data directory (it is read-only itself) and removes the work folder after."""
    env = dict(os.environ)
    if PACKAGED:
        for key in PACKAGE_ONLY_ENV:
            env.pop(key, None)
        env["BB_FSR4CAP_WORK"] = str(DATA_DIR / "fsr4cap")
        env["BB_FSR4CAP_CLEAN"] = "1"
    tools = FSR4CAP_DIR / "bin"
    if (tools / "dxil-spirv").is_file() and (tools / "fsr4cap.exe").is_file():
        env["BB_FSR4CAP_TOOLS"] = str(tools)
    env["BB_FSR411_OUT"] = os.environ.get("BB_FSR411_DIR") or str(
        (DATA_DIR if PACKAGED else PORT_DIR) / "fsr4_411")
    command = ["bash", str(FSR4CAP_DIR / "build_assets.sh"), str(upscaler)]
    return command + ([str(loader)] if loader else []), env


# Trophy grades (scripts/trophies.py) as the Trophies page names them.
TROPHY_GRADES = {"P": "Платиновый", "G": "Золотой", "S": "Серебряный", "B": "Бронзовый"}

# Seamless co-op (BBSC, scripts/bbsc.py): the names and descriptions of its options, by id
# (scripts/bbsc_options.json), in the launcher's key language (bbport_i18n.py).
BBSC_OPTION_TEXTS = {
    "connect_first": ("Призыв между локациями",
                     "Сначала подключение, затем одна загрузка в локацию хозяина"),
    "warp_together": ("Путешествовать вместе",
                     "Гость следует за хозяином при переходах через фонари"),
    "world_sync": ("Синхронизация мира",
                  "Гость видит мир хозяина (двери, боссы, лифты)"),
    "dream": ("Сон Охотника вместе",
             "Гость пользуется Куклой, мастерской и посыльными"),
    "no_fog_walls": ("Без туманных стен",
                    "Можно покидать локацию во время кооператива"),
    "lamp": ("Фонари в кооперативе",
            "Хозяин может пользоваться фонарями во время сессии"),
    "host_dead": ("Остаться, если хозяин погиб",
                 "Гость не теряет сессию, когда хозяин умирает"),
    "spectate": ("Возрождение на месте",
                "Погибший игрок возрождается или наблюдает, а не уходит"),
    "full_echoes": ("Полные отголоски",
                   "Гость получает столько же отголосков, сколько хозяин, а не половину"),
    "no_hp_penalty": ("Без штрафа к здоровью гостя",
                     "Убирает снижение максимального здоровья гостя на 30 %"),
    "guest_items": ("Предметы гостя",
                   "Гость подбирает и сохраняет предметы"),
    "solid_npcs": ("Плотные NPC",
                  "Гость видит NPC обычными, а не серыми призраками"),
    "death_penalty": ("Пятно крови после смерти",
                     "Смерть без выхода из сессии всё равно оставляет пятно крови и отголоски"),
    "free_bell": ("Бесплатный Зовущий колокол",
                 "Колокол не тратит озарение"),
    "bells_anywhere": ("Колокола где угодно",
                      "Колокола BBSC звонят в любом месте, даже во Сне Охотника (роль, озарение и "
                      "подключение к сети по-прежнему учитываются)"),
    "five_hunters": ("Пять охотников",
                    "Хозяин может призвать до 4 гостей"),
    "messages": ("Тексты кооператива",
                "Тексты под бесшовную игру (без «Возвращение в свой мир»)"),
    "load_cover": ("Затемнение при подключении",
                  "Загрузки гостя проходят за чёрным экраном"),
    "floor_guard": ("Защита пола",
                   "Без вылета, если пол под персонажем был выгружен"),
    "scaling": ("Усиление врагов",
               "Враги и боссы сильнее за каждого гостя (вместо усиления боссов в игре)"),
    "scale_npc_hunters": ("Усиливать NPC-охотников",
                         "Хенрик, Джура и другие враждебные охотники тоже усиливаются"),
    "scale_enemy_hp": ("Здоровье врагов за гостя (%)",
                      "Дополнительное здоровье обычных врагов за каждого гостя"),
    "scale_boss_hp": ("Здоровье боссов за гостя (%)",
                     "Дополнительное здоровье боссов за каждого гостя"),
    "scale_damage": ("Урон врагов за гостя (%)",
                    "Дополнительный урон врагов и боссов за каждого гостя"),
    "scale_enemy_stagger": ("Устойчивость врагов за гостя (%)",
                           "Обычных врагов сложнее оглушить, за каждого гостя"),
    "scale_boss_stagger": ("Устойчивость боссов за гостя (%)",
                          "Боссов сложнее оглушить, за каждого гостя"),
    "shared_progress": ("Общий прогресс",
                       "Когда гость уходит, пройденные хозяином боссы, срезки, двери и фонари добавляются в мир гостя (только добавляет; сохранения копируются заранее)"),
    "relay": ("Адрес ретранслятора",
             "host:20444; пусто — адрес игрового сервера"),
}


# The Online tab's shadNet server choice (online.server_kind). shadPS4's public server is not one:
# it signs this port out since 2026-10-12.
SERVER_KINDS = [
    # Seamless Hunt's servers, as its guide sets them up (online.SEAMLESSHUNT_*).
    ("Seamless Hunt", "seamlesshunt", "play.seamlesshunt.com: сервер сообщества BBSC, с игроками на Windows"),
    ("Свой сервер", "own", "shadnet-p2p: на вашем ПК или VPS"),
]
# The Hunter's Dream, with bbhost's players: the online module talks to it itself
# (BB_NET_BACKEND=thd, gpu/bbnet20/thd); the account is a Discord sign-in (online.thd_sign_in).
THD_KIND = ("The Hunter's Dream (с игроками bbhost)", "thd",
            "Кооператив с игроками bbhost через The Hunter's Dream; вход через Discord")
SERVER_GUIDE_URL = f"{bbport_update.REPOSITORY_URL}/blob/main/docs/SERVER.md"


def pkg_extractor():
    """pkgextract for Install from PKG (scripts/pkg_install.py): BB_PKGEXTRACT (the AppImage's
    copy), build.sh's, else on PATH; None without it."""
    for candidate in (os.environ.get("BB_PKGEXTRACT"), PORT_DIR / "out/pkgextract/bin/pkgextract"):
        if candidate and Path(candidate).is_file():
            return str(candidate)
    return shutil.which("pkgextract")


def online_module():
    """The online module beside the GPU library (gpu/bbnet20, both pools and BBSC; a build without
    its libraries has none), or BB_NET_MODULE (the AppImage's copy)."""
    if os.environ.get("BB_NET_MODULE"):
        return Path(os.environ["BB_NET_MODULE"]).is_file()
    return (binaries_dir() / "gpu" / "libbbnet20.so").is_file()


def atlas_dir():
    """The maps Hunter's Atlas's generator made (tools/hunters-atlas: maps/ and art/), in the data
    folder or, for the launcher run from the repository, where the AppImage keeps them; None
    without them."""
    data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    for folder in (DATA_DIR / "navigation-map", data_home / "bbport" / "navigation-map"):
        if (folder / "maps" / "atlas.json").is_file() and (folder / "art").is_dir():
            return folder
    return None


def atlas_environment(s):
    """The game's Hunter's Atlas variables: the map on, where its files are and its options; off
    (BB_ATLAS_ENABLED=0: none of its code runs) when the switch is off or there are no maps."""
    folder = atlas_dir() if s.get("atlas") else None
    if folder is None:
        return {}
    return {
        "BB_ATLAS_ENABLED": "1",
        "BB_MAP_DIR": str(folder / "maps"),
        "BB_MAP_ART_DIR": str(folder / "art"),
        "BB_MAP_FONT": str(folder / "art" / "native-font.ttf"),
        "BB_MAP_CATALOG": str(folder / "maps" / "catalog.json"),
        "BB_MAP_CONFIG": str(folder / "settings.ini"),
        "BB_MAP_TRAVEL_ENABLED": "1" if s.get("atlas_travel", True) else "0",
        "BB_MAP_ITEMS_ENABLED": "1" if s.get("atlas_items", True) else "0",
        "BB_MAP_ITEM_CATEGORIES": "healing,insight,equipment,echoes",
        "BB_MAP_FOG_ENABLED": "0",
        "BB_MAP_NPC_MODE": "all",
    }


def game_environment(s):
    """Environment for run.sh from the launcher settings."""
    env = dict(os.environ)
    env["BB_GAME_DIR"] = str(Path(s["game_dir"]).expanduser())
    if s["user_dir"]:
        env["BB_USER_DIR"] = s["user_dir"]
    if s.get("dlc_dir"):
        env["BB_DLC_DIR"] = str(Path(s["dlc_dir"]).expanduser())
    env["BB_MODS_DIR"] = str(Path(s.get("mods_dir") or DATA_DIR / "mods").expanduser())
    env["BB_MODS_CONFIG"] = str(DATA_DIR / "mods.json")
    env["BB_MODS_ENABLED"] = "1" if s.get("mods_enabled", True) else "0"
    env["BB_PATCHES_DIR"] = str(patches_dir(s))
    env["BB_PATCHES_CONFIG"] = str(DATA_DIR / "patches.json")
    env["BB_LANGUAGE"] = s["language"] or str(system_game_language())
    # The in-game menu speaks the launcher's language until one is chosen in it (menu_language).
    env["BB_MENU_LANGUAGE"] = language()
    env["BB_FULLSCREEN"] = "1" if s["fullscreen"] else "0"
    env["BB_PRESENT_MODE"] = s["present_mode"]
    if s.get("gamepad"):
        env["BB_GAMEPAD"] = s["gamepad"]
    if s.get("display"):
        env["BB_DISPLAY"] = s["display"]
    deadzone = number(s.get("pad_deadzone", 4), 4, int, "settings.json", "pad_deadzone")
    if deadzone != 4:  # else the port's own default
        env["BB_PAD_DEADZONE"] = str(round(max(0, min(deadzone, 50)) * 127 / 100))
    if s.get("pad_lightbar") and re.fullmatch(r"#[0-9a-fA-F]{6}", s.get("pad_lightbar_colour", "")):
        env["BB_PAD_LIGHTBAR"] = s["pad_lightbar_colour"][1:]
    env["BB_SKIP_NETWORK_CHOICE"] = "1" if s.get("skip_network_choice", True) else "0"
    if s["hdr"]:
        env["BB_HDR"] = "1"
    env["BB_FPS"] = s["fps_mode"]
    if s["fps_limit"] > 0:
        env["BB_FPS_LIMIT"] = str(s["fps_limit"])
    if s["draw_pipe"]:
        env["BB_DRAW_PIPE"] = s["draw_pipe"]
    if s["readbacks"]:
        env["BB_READBACKS"] = s["readbacks"]
    if s["mangohud"]:
        env["MANGOHUD"] = "1"
        # Its default lines and the game's RAM and VRAM (a MANGOHUD_CONFIG of the user's wins;
        # set, it takes the config file's place).
        env.setdefault("MANGOHUD_CONFIG", "fps,frametime,frame_timing,gpu_stats,cpu_stats,ram,vram")
    if s["frame_stats"]:
        env["BB_FRAME_STATS"] = "1"
    if s.get("save_log"):
        env["BB_SAVE_LOG"] = "1"
    # The GPU chosen by name: its index in Vulkan's order now (BB_GPU_ID). One not found (taken
    # out, renamed by a driver update) leaves the choice to the port. BB_GPU_ID from the shell
    # wins.
    if s.get("gpu") and "BB_GPU_ID" not in os.environ:
        index = next((index for index, _vendor, _kind, name, _best in connected_gpus()
                      if name == s["gpu"]), None)
        if index is not None:
            env["BB_GPU_ID"] = str(index)
    if s.get("crash_diag"):
        env["BB_FREE_CHECK"] = "1"
        env["BB_WRITE_LOG"] = "1"
        env["BB_PRODUCER_CHECK"] = "1"
    if s["gpu_profile"]:
        env["BB_GPU_PROFILE"] = "1"
    if s["vk_validation"]:
        env["BB_VK_VALIDATION"] = "1"
    env["BB_DISCORD"] = "1" if s.get("discord", True) else "0"
    # On, the packaged entry's BB_STEAM_OVERLAY (Steam's preload, kept for the game) stays.
    if not s.get("steam_overlay", True):
        env["BB_STEAM_OVERLAY"] = "0"
    env["BB_GESTURES_NO_MOTION"] = "1" if s.get("gestures_no_motion") else "0"
    if s.get("trophy_key", "").strip():
        env["BB_TROPHY_KEY"] = s["trophy_key"].strip()
    if s.get("online") and online_module():
        env.update(online.environment(s))
    env.update(atlas_environment(s))
    for item in s["extra_env"].split():
        if "=" in item:
            key, value = item.split("=", 1)
            env[key] = value
    return env


def flat_button(icon, tooltip, handler):
    button = Gtk.Button(icon_name=icon, valign=Gtk.Align.CENTER, tooltip_text=tooltip)
    button.add_css_class("flat")
    button.connect("clicked", handler)
    return button


def folder_actions(row, change, more):
    """A folder row's actions in words: "Change…" as its button, the others ((label, handler)) in a
    "⋯" menu. Icons alone were hard to tell apart and gave a screen reader nothing to say.
    Returns the menu's actions, to turn one off (set_enabled)."""
    button = Gtk.Button(label=tr("Изменить…"), valign=Gtk.Align.CENTER)
    button.connect("clicked", change)
    row.add_suffix(button)
    group, menu, actions = Gio.SimpleActionGroup(), Gio.Menu(), []
    for number, (label, handler) in enumerate(more):
        action = Gio.SimpleAction(name=f"item{number}")
        action.connect("activate", lambda _a, _p, handler=handler: handler(None))
        group.add_action(action)
        menu.append(label, f"folder.item{number}")
        actions.append(action)
    row.insert_action_group("folder", group)
    row.add_suffix(Gtk.MenuButton(icon_name="view-more-symbolic", menu_model=menu, valign=Gtk.Align.CENTER,
                                  tooltip_text=tr("Ещё"), css_classes=["flat"]))
    return actions


def open_folder(window, path):
    """Opens `path` in the file manager (created first, so that a new saves folder opens)."""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    Gtk.FileLauncher.new(Gio.File.new_for_path(str(path))).launch(window, None, None)


def readable_choice(row):
    """The chosen value keeps up to 16 characters beside a long subtitle (it was cut to "Seamle…");
    a longer one still ends in "…" on a narrow window. It sits against the arrow, however short
    (left-aligned, "60" stood apart from it); the list keeps its own left-aligned items."""
    def setup(_factory, item, xalign):
        item.set_child(Gtk.Label(xalign=xalign, ellipsize=Pango.EllipsizeMode.END))

    def bind(_factory, item):
        model = row.get_model()
        longest = max((len(model.get_string(i)) for i in range(model.get_n_items())), default=0) if model else 0
        label = item.get_child()
        label.set_label(item.get_item().get_string())
        label.set_width_chars(min(longest, 16))

    def bind_list(_factory, item):
        item.get_child().set_label(item.get_item().get_string())
    factory = Gtk.SignalListItemFactory()
    factory.connect("setup", setup, 1)
    factory.connect("bind", bind)
    row.set_factory(factory)
    list_factory = Gtk.SignalListItemFactory()
    list_factory.connect("setup", setup, 0)
    list_factory.connect("bind", bind_list)
    row.set_list_factory(list_factory)
    return row


def combo_row(title, subtitle, choices, current):
    model = Gtk.StringList.new([tr(choice[0]) for choice in choices])
    row = readable_choice(Adw.ComboRow(title=title, model=model))
    values = [choice[1] for choice in choices]
    notes = [tr(choice[2]) if len(choice) > 2 else None for choice in choices]

    def show_note(*_):
        lines = [line for line in (subtitle, notes[row.get_selected()]) if line]
        row.set_subtitle("\n".join(lines))

    row.set_selected(values.index(current) if current in values else 0)
    show_note()
    row.connect("notify::selected", show_note)
    row.values = values
    return row


def combo_value(row):
    return row.values[row.get_selected()]


# Controls (runtime_pad.c): input, label, default keyboard keys, default gamepad buttons (SDL names).
# bbport.ini key.<input>= / pad.<input>= replace a default; no line keeps it. Mouse buttons and the
# wheel are keys ("Mouse Left", "Wheel Down"); they act while the game holds the mouse.
CONTROLS = [
    ("cross", "Крест", "Space", "a"),
    ("circle", "Круг", "Left Shift", "b"),
    ("square", "Квадрат", "E", "x"),
    ("triangle", "Треугольник", "Q", "y"),
    ("l1", "L1", "1, Mouse X2", "leftshoulder"),
    ("r1", "R1", "3, Mouse Left", "rightshoulder"),
    ("l2", "L2", "R, Mouse Right", "lefttrigger"),
    ("r2", "R2", "F, Mouse X1", "righttrigger"),
    ("l3", "L3", "Z", "leftstick"),
    ("r3", "R3", "C, Mouse Middle", "rightstick"),
    ("options", "Options", "Return", "start"),
    ("touchpad", "Тачпад, левая половина (жесты)", "Tab", "back, touchpad"),
    ("touchpad_right", "Тачпад, правая половина (личные вещи)", "Backspace", ""),
    ("up", "Крестовина вверх", "I, Wheel Up", "dpup"),
    ("down", "Крестовина вниз", "K, Wheel Down", "dpdown"),
    ("left", "Крестовина влево", "J", "dpleft"),
    ("right", "Крестовина вправо", "L", "dpright"),
    ("move_up", "Движение вперёд", "W", None),
    ("move_down", "Движение назад", "S", None),
    ("move_left", "Движение влево", "A", None),
    ("move_right", "Движение вправо", "D", None),
    ("look_up", "Камера вверх", "Up", None),
    ("look_down", "Камера вниз", "Down", None),
    ("look_left", "Камера влево", "Left", None),
    ("look_right", "Камера вправо", "Right", None),
    ("walk", "Шаг (удерживать с движением)", "Left Alt", None),
    ("sprint", "Бег (удерживать: Круг)", "", None),
    ("dodge", "Уклонение (короткое нажатие Круга; с бегом — прыжок)", "", None),
]
# The keyboard's default keys (runtime_pad/bindings.c): bbport 0.7's, Dark Souls III's on PC (as
# bbport 0.6's, issue #33). Circle has no key of its own there: sprint and dodge make it, Escape
# goes back in the game's menus. CONTROLS' keys are keyboard_layout=classic, the Linux fork's own.
KEY_DEFAULTS_07 = {
    "cross": "F, Return", "circle": "", "square": "Tab, R", "triangle": "Q",
    "l1": "E, Mouse X2", "r1": "Mouse Left", "l2": "Mouse Right",
    "r2": "Left Shift+Mouse Left, Mouse X1", "l3": "Left Ctrl", "r3": "C, Mouse Middle",
    "options": "Escape", "touchpad": "G", "touchpad_right": "Backspace",
    "up": "3, Up, Wheel Up", "down": "4, Down, Wheel Down", "left": "1, Left", "right": "2, Right",
    "move_up": "W", "move_down": "S", "move_left": "A", "move_right": "D",
    "look_up": "I", "look_down": "K", "look_left": "J", "look_right": "L",
    "walk": "Left Alt", "sprint": "Left Shift", "dodge": "Space",
}
KEYBOARD_LAYOUTS = [
    ("bbport 0.7 (как в Dark Souls III на ПК)", "0.7",
     "Пробел — уклонение, Shift — бег, Shift + Пробел — прыжок, F — действие, Escape — меню "
     "и назад в меню игры"),
    ("Классическая (Linux-версии)", "classic", "Пробел — Крест, левый Shift — Круг"),
]


GAMEPADS_KEPT = 3.0  # seconds: one look at the gamepads serves a whole build of the window
_gamepads = (0.0, None)


def connected_gamepads(types=False, paths=False, fresh=False, look=True):
    """(GUID, name) of the connected gamepads (bb-gpu-capabilities --gamepads), [] if unknown;
    with `types`, (GUID, name, SDL type) ("" for a generic gamepad); with `paths`, also the device
    path, which tells two of one model apart (local co-op). Each look starts the tool (0.3 s):
    one taken less than GAMEPADS_KEPT ago is used again, unless `fresh`. Without `look`, the last
    one whatever its age ([] before any): the window's lists, filled again once the launcher has
    looked in a thread (LauncherWindow.with_gamepads)."""
    global _gamepads
    taken, pads = _gamepads
    if not look:
        pads = pads or []
    elif fresh or pads is None or time.monotonic() - taken > GAMEPADS_KEPT:
        tool = PORT_DIR / ("bin" if PACKAGED else "out") / "bb-gpu-capabilities"
        try:
            run = subprocess.run([str(tool), "--gamepads"], capture_output=True, text=True, timeout=5)
        except (OSError, subprocess.SubprocessError):
            return []
        pads = [(line.split("\t") + ["", ""])[:4] for line in run.stdout.splitlines() if "\t" in line]
        _gamepads = (time.monotonic(), pads)
    return [tuple(pad if paths else pad[:3] if types else pad[:2]) for pad in pads]


def gamepad_type(s):
    """SDL type of the gamepad the game will use (the chosen one when connected, else the first
    one); None without a gamepad."""
    pads = connected_gamepads(types=True)
    want = s.get("gamepad", "").casefold()
    chosen = [pad for pad in pads if want and (want == pad[0].casefold() or want in pad[1].casefold())]
    return (chosen or pads or [(None, None, None)])[0][2]


def connected_displays():
    """(BB_DISPLAY value, label) of the monitors (bb-gpu-capabilities --displays), [] if unknown.
    The value is the monitor's name, or its number when two monitors share a name."""
    tool = PORT_DIR / ("bin" if PACKAGED else "out") / "bb-gpu-capabilities"
    try:
        run = subprocess.run([str(tool), "--displays"], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return []
    rows = [line.split("\t") for line in run.stdout.splitlines() if line.count("\t") == 2]
    names = [name for name, _, _ in rows]
    return [(name if names.count(name) == 1 else str(number),
             f"{number}: {name} ({size})" + (tr(", основной") if primary == "1" else ""))
            for number, (name, size, primary) in enumerate(rows, 1)]


def connected_gpus():
    """(index, vendor ID, type, name, the port's own choice) of the GPUs in Vulkan's order
    (bb-gpu-capabilities --gpus; BB_GPU_ID is the index), [] if unknown."""
    tool = PORT_DIR / ("bin" if PACKAGED else "out") / "bb-gpu-capabilities"
    env = {key: value for key, value in os.environ.items() if key != "BB_GPU_ID"}
    try:
        run = subprocess.run([str(tool), "--gpus"], capture_output=True, text=True, timeout=10,
                             env=env)
    except (OSError, subprocess.SubprocessError):
        return []
    rows = [line.split("\t") for line in run.stdout.splitlines() if line.count("\t") == 4]
    return [(int(index), vendor, kind, name, best == "1")
            for index, vendor, kind, name, best in rows if index.isdigit()]


# mods.py problem(): why a folder in the mods folder is not loaded.
MOD_PROBLEMS = {
    "empty": "папка пуста",
    "archive": "это ещё архив: распакуйте его сюда",
    "several": "несколько папок: каждый мод — в своей папке (с dvdroot_ps4 или папками вроде chr, "
               "parts, map)",
    "no-game-files": "нет файлов игры: нужна dvdroot_ps4 или папки вроде chr, parts, map",
}


class FolderList:
    """A preferences group with a folder row and one switch row per item below it."""

    def __init__(self, group):
        self.group = group
        self.rows = []

    def clear(self):
        for _, row in self.rows:
            self.group.remove(row)
        self.rows = []

    def add(self, key, row):
        self.group.add(row)
        self.rows.append((key, row))


# About → Thanks: everyone whose work is in this fork (code, translations, patches) or who helped
# it with reports and tests. Someone whose work is only looked at, not brought in, is not listed;
# add whoever a commit brings something from, in that commit.
def _github(user, what):
    return ("@" + user, what, "https://github.com/" + user)


def themed_icon(name):
    """The desktop icon theme's symbolic icon, or the launcher's own (launcher/icons/bbport-<name>.svg:
    GitHub's, Steam's and Discord's marks) for a theme without it. Not GTK's own fallback: for
    "steam-symbolic" it takes the installed app's colour icon."""
    display = Gdk.Display.get_default()
    if display and not Gtk.IconTheme.get_for_display(display).has_icon(name) and \
            (PORT_DIR / "launcher" / "icons" / f"bbport-{name}.svg").is_file():
        name = "bbport-" + name
    return Gtk.Image(icon_name=name)


THANKS = (
    ("Порт и его код", (
        _github("deadinside28", "bbport — порт, на котором построен весь этот проект, а также указатель "
                                "мыши в меню и раскладка клавиатуры из 0.6"),
        _github("Supermedo", "Игра по сети, страница читов, добавление в Steam, "
                             "пропуск конвейеров, которые драйвер не может создать, игра без "
                             "вылета при нехватке видеопамяти и пропуск отрисовок с пустой "
                             "таблицей вершин"),
        _github("0xCydral", "Собрал и адаптировал десятки исправлений: вылеты при загрузке, чёрные "
                            "изображения, апскейлер, строка производительности в журнале"),
        _github("yumlevi", "Чёрный предпросмотр персонажа, картинка экрана загрузки и вылет из-за нечитаемой программы шейдера"),
        _github("GoncaloLobo0", "Вылеты при загрузке областей"),
        _github("bmy", "Векторы движения больших чудовищ и ошибка памяти"),
        _github("Mrsuss60", "Меню жестов с клавиатуры, слот удалённого изображения и журнал неудачных резервирований памяти"),
        _github("SrShadowy", "Экранная клавиатура для имени персонажа и уведомление о компиляции "
                             "шейдеров"),
        _github("droogie", "Быстрая загрузка после смерти и перемещения (bbhost) и сервер "
                           "The Hunter's Dream"),
        _github("Wozzardman", "Сервер для своего кооператива и бесшовный призыв BBSC"),
        _github("IFreemz", "Модель FSR 4 без шлейфов за персонажами"),
        _github("FireBurn", "Апскейлер FSR 3.1"),
        _github("Qiming-Liu", "Перевод на упрощённый китайский"),
        _github("andrecabralgit", "Звук игры на полной громкости"),
        _github("Jgamrot", "Флажки и ползунки внутриигрового меню"),
        _github("GerasimosKan", "Названия трофеев на английском без ключа и звук при получении трофея"),
        _github("artemkaVG", "Буфер трафарета, в который писали цветные изображения"),
        _github("parsifal295", "Половины тачпада на Xbox"),
        _github("emurphy04", "Вылет видеоплеера при его остановке, поле зрения и защита от вылета онлайн"),
        _github("AyrtonSanabio", "Язык внутриигрового меню при запуске без окна лаунчера"),
        _github("Aryxa", "DLSS в AppImage на NVIDIA"),
        _github("Jhony-Jhansen", "Движение с клавиатуры: из двух противоположных клавиш побеждает нажатая последней"),
        _github("cassioKenji", "Измерения бега с клавиатуры: бег по большей оси стика, рывок обрывается при повороте на 45°"),
        _github("msisovic", "Причина зависания загрузки после путешествия через фонарь"),
        _github("axpico", "Видеопамять заполнена: игра ждёт, пока освободятся вытесненные текстуры, а не закрывается"),
        _github("AndiMajore", "Отладка вылетов: процесс ждёт отладчик (BB_FAULT_WAIT)"),
        _github("Classmg22", "BBSC (CLS_AMG): бесшовный кооператив"),
        _github("MikeTat1988", "Hunter's Atlas: карта на весь экран в игре"),
        _github("Awakenchan", "Вылеты: флипы, дескрипторы и ошибки страниц; смена стиков и инверсия камеры, геймпад, которым играют, импорт сохранений, выбор версии; вершинные шейдеры с правильными привязками, повторное чтение устаревших вершинных входов, буферы индексов непрямых отрисовок и векторы движения камеры без NaN"),
        _github("iannitram", "FSR 3.1 без цветного шума на Ryzen Z1 (ROG Ally, Legion Go)"),
        _github("whp199", "Защита GX-запросов окклюзии от вылета 0x2169edc"),
        _github("nick24051998", "Обход SRT без ошибок на нулевых таблицах"),
    )),
    ("Помощь и тесты", (
        _github("willthehuman", "Подробные отчёты с журналами и проверка исправлений"),
        _github("Joomzie", "Идея поменять местами A и B на контроллерах в стиле Nintendo"),
        _github("Kaka556Kevin", "Проверка исправления видеопамяти"),
        _github("nr1971", "Нашёл ошибку, из-за которой игра не запускалась на некоторых видеокартах, "
                          "ускорение камеры по диагонали и вылет при выходе из игры"),
        _github("segasonicye", "Нашёл, почему игра не запускалась в игровом режиме Steam Deck"),
        _github("Monochrome0907", "Нашёл, при каких эффектах зависают загрузки на NVIDIA"),
        _github("bruxis", "Журнал, показавший, почему Steam Input не доходил до игры"),
        _github("shauryasagar", "Чёрный Сон Охотника после долгой игры"),
        _github("ZeroSTF", "Чёрный Сон Охотника после долгой игры"),
        _github("popcar2", "Идеи для лаунчера"),
        _github("shaneo88", "Файл патчей shadPS4 в папке патчей"),
        _github("n3vrs0ft", "Вылет «Transaction failed» на Seamless Hunt, журналы, по которым гость "
                             "BBSC перестал следовать за чужим хозяином, и проверки BBSC 0.0.2 с "
                             "игроком на Windows"),
        _github("cappp", "Вылет «Transaction failed» на Seamless Hunt"),
        _github("simo1730", "Страница трофеев, не находившая файлы дампа"),
        _github("Nahnahchi", "Журналы и проверки: зависание GPU в битве с боссом на NVIDIA, вылет "
                              "в Яхар’гуле, растянутые модели, вылет на Steam Deck, чёрные эффекты, "
                              "радужные текстуры и вылеты в менеджере памяти игры"),
        _github("thomasgarafano1", "Hunter's Atlas, не готовивший карту с дампом GOTY, и проверка исправления"),
        _github("TacticalBill", "Отметка трофеев, уже полученных на PS4"),
        _github("holydingus", "Предметы BBSC, которые не выдавались новому персонажу"),
        _github("OPGZ2", "Пустое окно лаунчера при запуске"),
        _github("kuday248", "Настройки из меню игры, которые лаунчер перезаписывал"),
        _github("BlazinKarp", "Оверлей Steam в игре"),
        _github("molnar-a", "Вылет на Steam Deck после путешествия через фонарь и проверка исправления"),
        _github("Aman9das", "Просьба о раскладке клавиатуры из bbport 0.6"),
    )),
    ("Другие благодарности", (
        ("Dommo, goomab", "Иконки кнопок Xbox и Switch (Nexus Mods)",
         "https://www.nexusmods.com/bloodborne/mods/30"),
        ("Abken", "Показал, какие текстуры нужны иконкам клавиатуры (Nexus Mods)",
         "https://www.nexusmods.com/bloodborne/mods/537"),
        ("Kyo, Lance McDonald, auser1337, illusion, emoose", "Патчи игры: высокий FPS, разрешение и другое",
         "https://github.com/ayozetr/bloodborne_linux/blob/main/docs/CREDITS.md"),
        ("shadPS4", "Рендерер и компилятор шейдеров", "https://github.com/shadps4-emu/shadPS4"),
        ("pkgforge-dev", "Инструмент для сборки AppImage",
         "https://github.com/pkgforge-dev/Anylinux-AppImages"),
        ("paulomanrique", "ps4-pkg-extractor: установка игры из файлов .pkg",
         "https://github.com/paulomanrique/ps4-pkg-extractor"),
        ("fhody125-web", "NoDreamForHunter: основа игрового сервера BBSC",
         "https://github.com/fhody125-web/NoDreamForHunter"),
    )),
)


class LauncherWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Bloodborne")
        self.set_default_size(980, 820)
        # Narrow (the Steam Deck in game mode, a small window): the sidebar becomes a list of the
        # sections, each one opened over it with a back button.
        self.narrow = False
        breakpoint = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 640sp"))
        breakpoint.connect("apply", lambda *_: self.on_width_breakpoint(True))
        breakpoint.connect("unapply", lambda *_: self.on_width_breakpoint(False))
        self.add_breakpoint(breakpoint)
        self.settings = load_settings()
        set_language(self.settings.get("ui_language", ""))
        self.ini, self.ini_lines = load_ini()
        migrate_ini(self.settings, self.ini, self.ini_lines)
        self.ini_rows_seen = {}  # bbport.ini values as the rows showed them when last built or saved
        self.ini_controls_changed = {}  # key.* / pad.* bindings changed here, not yet saved
        self.process = None
        self.atlas_job = None  # bbport_atlas_maps prepare while it runs
        self.coop_processes = {}  # local co-op: players 2-4's games by player; player 1's is process
        self.stream = None
        self.log_spool = None  # every line of the Journal since it was last cleared; False: failed
        self.fsr411_build = None  # tools/fsr4cap/build_assets.sh while it runs
        self.latest = None  # bbport_update.latest_release() once checked
        self.releases = []  # bbport_update.releases(), the version selector's choices
        self.installing = None  # the release being (or just) installed
        self.update_state = "idle"  # idle, checking, downloading, installed
        # Operations in a thread (their buttons are the page's): a new launcher language rebuilds
        # the window once they, the game, a map preparation and an FSR 4.1.1 build are done.
        self.working = set()
        self.rebuild_waiting = False
        self.build()
        self.connect("close-request", self.on_close)

    def build(self):
        """(Re)creates the window's content in the current launcher language: the sections in a
        sidebar (collapsed into a list on a narrow window, the Steam Deck's), each one's page
        beside it, and Play always in the header."""
        # A rebuild (another launcher language) stays where it was.
        if hasattr(self, "stack"):
            where = (self.stack.get_visible_child_name(), self.multiplayer_stack.get_visible_child_name()
                     if hasattr(self, "multiplayer_stack") else None, self.split.get_show_content())
        else:  # the first start, or the game's folder still to be chosen: Setup
            where = ("graphics" if self.game_found() else "setup", None, False)
        self.split = Adw.NavigationSplitView(min_sidebar_width=210, max_sidebar_width=260,
                                             sidebar_width_fraction=0.26)
        self.stack = Adw.ViewStack()
        content = Adw.ToolbarView()
        header = Adw.HeaderBar()
        self.section_title = Adw.WindowTitle(title="Bloodborne")
        header.set_title_widget(self.section_title)
        self.launch_button = Gtk.Button()
        self.launch_button.connect("clicked", self.on_launch)
        header.pack_end(self.launch_button)
        content.add_top_bar(header)
        # Without the game Play stays grey: the banner says why, on every page (update_game_status).
        self.game_banner = Adw.Banner(button_label=tr("Начальная настройка"))
        self.game_banner.connect("button-clicked", lambda _banner: self.show_section("setup"))
        content.add_top_bar(self.game_banner)
        self.toasts = Adw.ToastOverlay()
        self.toasts.set_child(self.stack)
        content.set_content(self.toasts)
        self.split.set_content(Adw.NavigationPage(child=content, title="Bloodborne"))

        self.sidebar = Gtk.ListBox(css_classes=["navigation-sidebar"])
        self.sidebar.set_header_func(self.sidebar_header)
        self.sidebar.connect("row-activated", lambda _list, row: self.show_section(row.section))
        # The arrow keys move the selection: beside the page, the page follows it.
        self.sidebar.connect("row-selected", lambda _list, row: row is not None and not self.split.get_collapsed()
                             and self.show_section(row.section, reveal=False))
        sidebar = Adw.ToolbarView()
        sidebar.add_top_bar(Adw.HeaderBar(title_widget=Adw.WindowTitle(title="Bloodborne")))
        sidebar.set_content(Gtk.ScrolledWindow(child=self.sidebar,
                                               hscrollbar_policy=Gtk.PolicyType.NEVER))
        self.split.set_sidebar(Adw.NavigationPage(child=sidebar, title="Bloodborne"))
        self.set_content(self.split)
        self.split.set_collapsed(self.narrow)

        log_text = self.log_text() if hasattr(self, "log_view") else ""
        # Issue #18: an error while building a page left the window blank for good (a saved value
        # it could not read). A page that fails shows its error instead; the others are built.
        self.build_errors = []
        self.thanks = None  # in the language of this build (thanks_dialog)
        GLib.timeout_add(1500, lambda: self.thanks_dialog() and False)
        # Made by the settings' page, shown on the Online tab: not a failed rebuild's old one.
        self.netchoice_group = None
        self.section_groups = {}

        def built(build_page):
            try:
                return build_page()
            except Exception:
                error = traceback.format_exc()
                self.build_errors.append(error)
                print(error, file=sys.stderr, end="")
                return self.build_error_page(error)

        # The settings' groups are shared out among sections; a failure there marks them all.
        # Each failure keeps its own error: the sections are placed after other pages are built.
        def error_of(build_page):
            return self.build_errors[-1] if isinstance(built(build_page), Gtk.Widget) else None
        settings_failed = error_of(self.build_settings_page)
        cheats_failed = None if settings_failed else error_of(self.build_cheats_page)

        def placed(section, failed):
            if failed:
                return self.build_error_page(failed)
            page = Adw.PreferencesPage()
            for _rank, group in sorted(self.section_groups.get(section, []), key=lambda item: item[0]):
                page.add(group)
            return page

        multiplayer = built(self.build_multiplayer_page)
        sections = (
            ("graphics", tr("Графика"), "video-display-symbolic", placed("graphics", settings_failed)),
            ("controls", tr("Управление"), "input-gaming-symbolic", placed("controls", settings_failed)),
            ("multiplayer", tr("Мультиплеер"), "system-users-symbolic", multiplayer),
            ("mods", tr("Модификации"), "application-x-addon-symbolic",
             placed("mods", settings_failed or cheats_failed)),
            ("trophies", tr("Трофеи"), "starred-symbolic", built(self.build_trophies_page)),
            ("setup", tr("Начальная настройка"), "folder-symbolic", placed("setup", settings_failed)),
            ("advanced", tr("Дополнительно"), "preferences-other-symbolic", placed("advanced", settings_failed)),
            ("log", tr("Журнал"), "utilities-terminal-symbolic", built(self.build_log_page)),
            ("about", tr("О программе"), "help-about-symbolic", built(self.build_about_page)),
        )
        for name, title, icon, page in sections:
            self.stack.add_titled_with_icon(page, name, title, icon)
            row = Gtk.ListBoxRow()
            row.section = name
            box = Gtk.Box(spacing=12, margin_top=6, margin_bottom=6, margin_start=6, margin_end=6)
            box.append(Gtk.Image(icon_name=icon))
            box.append(Gtk.Label(label=title, xalign=0, hexpand=True, ellipsize=Pango.EllipsizeMode.END))
            row.set_child(box)
            row.set_tooltip_text(title)
            self.sidebar.append(row)
        self.stack.connect("notify::visible-child-name", lambda *_: self.on_section_changed())
        if where[1] and hasattr(self, "multiplayer_stack"):
            self.multiplayer_stack.set_visible_child_name(where[1])
        first = self.stack.get_visible_child_name()
        self.show_section(where[0] or "graphics", reveal=where[2])
        if self.stack.get_visible_child_name() == first:
            self.on_section_changed()  # already the visible page: no notify for the title
        if self.build_errors:
            # Some of the settings' rows may be missing: nothing is saved (the user's files stay
            # as they are) and the game is not started from a half-built window.
            self.launch_button.set_label(tr("Запустить"))
            self.update_launch_sensitivity()
            self.launch_button.set_tooltip_text(tr(
                "Лаунчер не смог открыть страницу: запуск отключён, настройки не сохраняются"))
            if hasattr(self, "log_view"):
                self.log_view.get_buffer().set_text(log_text + "".join(self.build_errors))
            return
        self.log_view.get_buffer().set_text(log_text)
        # What the rows show now is the file's: only later changes are written (store).
        self.ini_rows_seen = self.ini_rows()
        self.update_launch_button()
        self.update_game_status()
        self.update_user_status()
        self.update_dlc_status()
        self.update_upscaler_status()
        self.show_update_state()
        if self.settings.get("check_updates", True) and self.latest is None and \
                self.update_state == "idle":
            self.on_check_update(None, quiet=True)
        # The controller lists were filled from the last look (none on the first build): again
        # once the gamepads are looked at in a thread.
        self.with_gamepads(lambda: (self.fill_gamepads(), self.fill_coop_controllers()))

    def update_launch_button(self):
        running = self.process is not None
        self.launch_button.set_label(tr("Остановить") if running else tr("Запустить"))
        self.launch_button.remove_css_class("destructive-action" if not running else "suggested-action")
        self.launch_button.add_css_class("destructive-action" if running else "suggested-action")
        self.update_launch_sensitivity()
        if hasattr(self, "fsr411_button"):
            self.fsr411_button.set_sensitive(not running)
        if hasattr(self, "atlas_maps_row"):
            self.show_atlas()
        if hasattr(self, "cache_button"):
            self.show_cache()

    # --- settings page -------------------------------------------------------------------

    def build_settings_page(self):
        """The settings' groups, placed in their sections (place): Graphics, Controls, Mods,
        Setup and Advanced."""

        launcher = Adw.PreferencesGroup()
        # In English too, so that a language one cannot read still leads back here; once.
        title = tr("Язык лаунчера")
        if title != "Launcher language":
            title += " / Launcher language"
        self.ui_language_row = combo_row(title, None,
                                         UI_LANGUAGES, self.settings.get("ui_language", ""))
        self.ui_language_row.connect("notify::selected", self.on_ui_language)
        launcher.add(self.ui_language_row)
        self.place("setup", 10, launcher)

        game = Adw.PreferencesGroup(title=tr("Игра"))
        # The game from your own PS4 packages: extracted, the update merged, the add-ons apart.
        self.pkg_row = Adw.ActionRow(title=tr("Установить из PKG"),
                                     subtitle=tr("Игра, обновление 1.09 и DLC из ваших файлов .pkg"))
        self.pkg_button = Gtk.Button(label=tr("Выбрать .pkg…"), valign=Gtk.Align.CENTER)
        self.pkg_button.connect("clicked", self.on_install_pkg)
        self.pkg_row.add_suffix(self.pkg_button)
        self.pkg_row.set_visible(pkg_extractor() is not None)
        game.add(self.pkg_row)
        self.game_row = Adw.ActionRow(title=tr("Папка игры"))
        self.game_status = Gtk.Image()
        self.game_row.add_suffix(self.game_status)
        folder_actions(self.game_row, self.on_choose_game, [
            (tr("Открыть в файловом менеджере"), lambda _b: open_folder(self, self.game_dir()))])
        game.add(self.game_row)
        # Dumped add-ons (one folder each); their data ships with the 1.09 update.
        self.dlc_row = Adw.ActionRow(title=tr("Папка DLC"))
        self.dlc_status = Gtk.Image()
        self.dlc_row.add_suffix(self.dlc_status)
        self.dlc_reset, = folder_actions(self.dlc_row, self.on_choose_dlc, [
            (tr("Не использовать DLC"), self.on_reset_dlc)])
        game.add(self.dlc_row)
        self.language_row = combo_row(tr("Язык системы"), None, LANGUAGES, self.settings["language"])
        game.add(self.language_row)
        self.text_language_row = combo_row(tr("Язык текста игры"), None, GAME_TEXT_LANGUAGES,
                                           self.ini.get("game_text_language", "auto"))
        game.add(self.text_language_row)
        self.voice_language_row = combo_row(tr("Язык озвучки"), None, GAME_VOICE_LANGUAGES,
                                            self.ini.get("game_voice_language", "auto"))
        game.add(self.voice_language_row)
        steam = Adw.ActionRow(title=tr("Добавить в Steam"),
                              subtitle=tr("Игра в библиотеке Steam запускается сразу, с настройками "
                                          "этого лаунчера"))
        steam_button = Gtk.Button(label=tr("Добавить"), valign=Gtk.Align.CENTER)
        steam_button.connect("clicked", self.on_add_to_steam)
        steam.add_prefix(themed_icon("steam-symbolic"))
        steam.add_suffix(steam_button)
        game.add(steam)
        self.steam_overlay_row = Adw.SwitchRow(
            title=tr("Оверлей Steam"),
            subtitle=tr("Кнопка Steam, счётчик FPS и снимки экрана Steam, когда игра запущена из Steam"),
            active=self.settings.get("steam_overlay", False))
        # Saved at once: Steam starts the game with --play, which reads the saved settings, often
        # while this window is still open.
        self.steam_overlay_row.connect("notify::active", lambda *_: self.store())
        game.add(self.steam_overlay_row)
        self.discord_row = Adw.SwitchRow(title=tr("Статус в Discord"),
                                         subtitle=tr("«Играет в Bloodborne» в профиле Discord, онлайн или офлайн"),
                                         active=self.settings.get("discord", True))
        self.discord_row.add_prefix(themed_icon("discord-symbolic"))
        game.add(self.discord_row)
        self.setup_game_group = game  # "Mute in the background" joins it (the display's rows)
        self.place("setup", 20, game)

        # Saves and the shader cache: user/ in the data directory unless chosen. Exported into a
        # .zip and imported back (scripts/save_import.py).
        saves = Adw.PreferencesGroup(title=tr("Сохранения"))
        self.user_row = Adw.ActionRow(title=tr("Папка сохранений"))
        _open, _backups, self.user_reset = folder_actions(self.user_row, self.on_choose_user, [
            (tr("Открыть в файловом менеджере"), lambda _b: open_folder(self, self.user_dir())),
            (tr("Открыть резервные копии"), lambda _b: open_folder(self, self.user_dir() / "savedata-backups")),
            (tr("Вернуть папку по умолчанию"), self.on_reset_user)])
        saves.add(self.user_row)
        export = Adw.ActionRow(title=tr("Экспортировать сохранения"),
                               subtitle=tr("В архив .zip: резервная копия или сохранения для другого "
                                           "компьютера. Импортируется ниже"))
        export_button = Gtk.Button(label=tr("Экспортировать…"), valign=Gtk.Align.CENTER)
        export_button.connect("clicked", self.on_export_saves)
        export.add_suffix(export_button)
        saves.add(export)
        imports = Adw.ActionRow(title=tr("Импортировать сохранения"),
                                subtitle=tr("Из shadPS4, другого порта, расшифрованной копии с PS4 или "
                                            "экспортированного .zip. Текущие сначала копируются в "
                                            "savedata-backups"))
        menu = Gio.Menu()
        menu.append(tr("Из папки…"), "saves.folder")
        menu.append(tr("Из архива .zip…"), "saves.archive")
        actions = Gio.SimpleActionGroup()
        for name, handler in (("folder", self.on_import_saves), ("archive", self.on_import_saves_archive)):
            action = Gio.SimpleAction(name=name)
            action.connect("activate", lambda _a, _p, handler=handler: handler(None))
            actions.add_action(action)
        imports.insert_action_group("saves", actions)
        imports.add_suffix(Gtk.MenuButton(label=tr("Импортировать"), menu_model=menu,
                                          valign=Gtk.Align.CENTER))
        saves.add(imports)
        self.auto_backup_row = Adw.SwitchRow(
            title=tr("Автоматические копии"),
            subtitle=tr("Копия сохранений перед каждым запуском игры, в savedata-backups. "
                        "Восстанавливается через «Импортировать» → «Из папки…»"),
            active=self.settings["saves_auto_backup"])
        saves.add(self.auto_backup_row)
        self.auto_backup_keep_row = Adw.SpinRow.new_with_range(1, 50, 1)
        self.auto_backup_keep_row.set_title(tr("Сколько копий хранить"))
        self.auto_backup_keep_row.set_subtitle(tr("Самые старые удаляются"))
        self.auto_backup_keep_row.set_value(number(self.settings["saves_auto_backup_keep"], 5, int,
                                                   "settings.json", "saves_auto_backup_keep"))
        self.auto_backup_row.bind_property("active", self.auto_backup_keep_row, "sensitive",
                                           GObject.BindingFlags.SYNC_CREATE)
        saves.add(self.auto_backup_keep_row)
        self.place("setup", 30, saves)

        # The GPU the game runs on, as in shadPS4 (laptops with two GPUs).
        mode = Adw.PreferencesGroup()
        self.gpu_row = readable_choice(Adw.ComboRow(title=tr("Видеокарта")))
        self.gpu_row.add_suffix(flat_button("view-refresh-symbolic", tr("Обновить список"),
                                            lambda _button: self.fill_gpus()))
        self.fill_gpus()
        mode.add(self.gpu_row)
        self.place("advanced", 10, mode)

        self.mods_group = Adw.PreferencesGroup(
            title=tr("Моды"), description=tr(
                "Распакуйте каждый мод в отдельную папку (с dvdroot_ps4 или сразу с chr/, parts/ и т. п.). "
                "При совпадении файлов побеждает мод ниже в списке. Применяется при запуске."))
        self.mods_enabled_row = Adw.SwitchRow(title=tr("Загружать моды"),
                                               active=self.settings["mods_enabled"])
        self.mods_group.add(self.mods_enabled_row)
        self.mods_folder_row = Adw.ActionRow(title=tr("Папка модов"))
        folder_actions(self.mods_folder_row, self.on_choose_mods, [
            (tr("Открыть в файловом менеджере"), lambda _b: open_folder(self, self.mods_dir())),
            (tr("Обновить список"), self.on_refresh_mods)])
        self.mods_group.add(self.mods_folder_row)
        self.mod_list = FolderList(self.mods_group)
        self.refresh_mods()
        self.place("mods", 10, self.mods_group)

        self.patches_group = Adw.PreferencesGroup(
            title=tr("Сторонние патчи"),
            description=tr("XML-патчи в формате shadPS4 для версии 01.09 из папки патчей. "
                           "Применяются при запуске."))
        self.patches_folder_row = Adw.ActionRow(title=tr("Папка патчей"))
        folder_actions(self.patches_folder_row, self.on_choose_patches, [
            (tr("Открыть в файловом менеджере"), lambda _b: open_folder(self, patches_dir(self.settings))),
            (tr("Обновить список"), self.on_refresh_patches)])
        self.patches_group.add(self.patches_folder_row)
        self.patch_list = FolderList(self.patches_group)
        self.refresh_patches()
        self.place("mods", 20, self.patches_group)

        screen = Adw.PreferencesGroup(title=tr("Экран"))
        aspect = self.ini.get("aspect_ratio", "auto")
        self.aspect_row = combo_row(
            tr("Соотношение сторон"),
            tr("Шире 16:9 — больше обзор по бокам, выше — сверху и снизу; интерфейс у краёв экрана"),
            ASPECTS, aspect if aspect in [value for _, value in ASPECTS] else "auto")
        screen.add(self.aspect_row)
        # A size written by hand in bbport.ini (5120x2160, ...) stays a choice instead of 720p.
        output = self.ini.get("output_res", "auto")
        outputs = OUTPUT_RES + ([(output.replace("x", "×"), output)]
                                if output not in [value for _, value in OUTPUT_RES] else [])
        self.output_row = combo_row(tr("Разрешение вывода"),
                                    tr("Апскейлер дорисовывает кадр; Steam Deck — 1280×800 (16:10)"),
                                    outputs, output)
        screen.add(self.output_row)
        # bbport.ini fov (scripts/fov.py): every camera of the game's table scaled; 43 is the game's.
        self.fov_row = Adw.SpinRow.new_with_range(30, 90, 1)
        self.fov_row.set_title(tr("Поле зрения"))
        self.fov_row.set_subtitle(tr("Градусы по вертикали; в игре 43"))
        try:
            fov = min(max(number(self.ini.get("fov", "43"), "43", key="fov"), 30.0), 90.0)
        except ValueError:
            fov = 43.0
        self.fov_row.set_value(fov)
        screen.add(self.fov_row)
        self.fullscreen_row = Adw.SwitchRow(title=tr("Полноэкранный режим"),
                                            active=self.settings["fullscreen"])
        screen.add(self.fullscreen_row)
        self.mute_row = Adw.SwitchRow(title=tr("Без звука в фоне"),
                                      subtitle=tr("Пока окно игры не в фокусе"),
                                      active=self.ini.get("mute_unfocused", "0") == "1")
        self.setup_game_group.add(self.mute_row)  # how the game behaves on the desktop, as Discord
        # Issue #69: the window (and fullscreen) went to the monitor SDL calls primary.
        self.display_row = readable_choice(Adw.ComboRow(title=tr("Монитор")))
        self.display_row.add_suffix(flat_button("view-refresh-symbolic", tr("Обновить список"),
                                                lambda _button: self.fill_displays()))
        self.fill_displays()
        screen.add(self.display_row)
        self.present_row = combo_row(tr("Режим показа кадров"), None, PRESENT_MODES,
                                     self.settings["present_mode"])
        screen.add(self.present_row)
        self.hdr_row = Adw.SwitchRow(title=tr("Разрешить HDR"), active=self.settings["hdr"])
        screen.add(self.hdr_row)
        self.place("graphics", 10, screen)

        # Issue #15: the first gamepad SDL found was taken (wheels and other controllers too).
        # Controls: the gamepad, then the keyboard and the mouse.
        controls = Adw.PreferencesGroup(title=tr("Геймпад"))
        keys = Adw.PreferencesGroup(title=tr("Клавиатура и мышь"))
        self.gamepad_row = readable_choice(Adw.ComboRow(title=tr("Контроллер")))
        # Controller names are long: the selected one is shown in full under the title.
        self.gamepad_row.connect("notify::selected", lambda *_: self.show_gamepad())
        self.gamepad_row.add_suffix(flat_button("view-refresh-symbolic", tr("Обновить список"),
                                                lambda _button: self.with_gamepads(self.fill_gamepads)))
        self.fill_gamepads()
        controls.add(self.gamepad_row)
        # Xbox / Switch art: Dommo's (Nexus, Bloodborne mod 30); keyboard prompts show the keys
        # bound below. The game's menu changes it too.
        prompts = self.ini.get("button_prompts", "auto")
        self.prompts_row = combo_row(tr("Иконки кнопок"), None, PROMPT_CHOICES,
                                     prompts if prompts in [value for _, value in PROMPT_CHOICES] else "auto")
        controls.add(self.prompts_row)
        # Nintendo-style controllers (issue #3): cross on the east button (A there), circle on
        # the south one; the prompts follow the buttons (bbport_button_prompts.cpp).
        self.ab_swap_row = Adw.SwitchRow(
            title=tr("Поменять местами A и B"),
            subtitle=tr("Для контроллеров в стиле Nintendo: подтверждение на A, отмена на B. "
                        "Применяется при запуске игры"),
            active=self.ab_swapped())
        self.ab_swap_syncing = False
        self.ab_swap_row.connect("notify::active", lambda *_: self.on_ab_swap())
        controls.add(self.ab_swap_row)
        # Dommo's gestures menu without the motion-control icons (scripts/gestures_menu.py).
        self.gestures_row = Adw.SwitchRow(title=tr("Меню жестов без значков управления движением"),
                                          active=bool(self.settings.get("gestures_no_motion")))
        controls.add(self.gestures_row)
        # Controller sticks (runtime_pad.c): swapped, camera stick inverted.
        self.stick_rows = {}
        for key, title in (("pad_swap_sticks", tr("Поменять стики местами")),
                           ("pad_invert_look_x", tr("Инвертировать камеру геймпада по горизонтали")),
                           ("pad_invert_look_y", tr("Инвертировать камеру геймпада по вертикали")),
                           ("pad_camera_diagonal", tr("Ровная скорость камеры по диагонали"))):
            self.stick_rows[key] = Adw.SwitchRow(title=title, active=self.ini.get(key) == "1")
            controls.add(self.stick_rows[key])
        # The right stick's camera speed per axis (#208): the game turns both at the same angular
        # speed, which looks faster vertically (the view is narrower than it is wide).
        self.camera_speed_rows = {}
        for key, title in (("camera_speed_x", "Скорость камеры (стик) по горизонтали"),
                           ("camera_speed_y", "Скорость камеры (стик) по вертикали")):
            row = Adw.SpinRow.new_with_range(0.25, 2.0, 0.05)
            row.set_title(tr(title))
            row.set_digits(2)
            row.set_value(min(max(number(self.ini.get(key, "1.0"), "1.0", key=key), 0.25), 2.0))
            controls.add(row)
            self.camera_speed_rows[key] = row
        self.deadzone_row = Adw.SpinRow.new_with_range(0, 50, 1)
        self.deadzone_row.set_title(tr("Мёртвая зона стиков (%)"))
        self.deadzone_row.set_subtitle(tr("Насколько нужно отклонить стик, чтобы он сработал. "
                                          "Увеличьте, если персонаж или камера двигаются сами "
                                          "(по умолчанию 4); применяется при запуске игры"))
        self.deadzone_row.set_value(number(self.settings["pad_deadzone"], 4, int, "settings.json",
                                           "pad_deadzone"))
        controls.add(self.deadzone_row)
        # L3+R3 opens the port's menu only when held (bbport_overlay.cpp); in PvP both sticks get
        # pressed by accident (#38).
        self.menu_pad_row = combo_row(
            tr("Меню порта с геймпада (L3 + R3)"),
            tr("Сколько удерживать L3 + R3, чтобы открыть меню в игре; Insert открывает его всегда"),
            MENU_PAD_HOLDS, self.ini.get("menu_pad_hold_ms", "800"))
        controls.add(self.menu_pad_row)
        # The light bar of a DualShock 4 or DualSense (runtime_pad.c: BB_PAD_LIGHTBAR).
        self.lightbar_row = Adw.ActionRow(
            title=tr("Цвет световой полосы геймпада"),
            subtitle=tr("DualShock 4 и DualSense; выключено — цвет игрока. Применяется при запуске игры"))
        colour = Gdk.RGBA()
        if not colour.parse(self.settings.get("pad_lightbar_colour") or ""):
            colour.parse(DEFAULTS["pad_lightbar_colour"])
        self.lightbar_colour = Gtk.ColorDialogButton(dialog=Gtk.ColorDialog(with_alpha=False),
                                                     rgba=colour, valign=Gtk.Align.CENTER)
        self.lightbar_switch = Gtk.Switch(active=bool(self.settings.get("pad_lightbar")),
                                          valign=Gtk.Align.CENTER)
        self.lightbar_colour.set_sensitive(self.lightbar_switch.get_active())
        self.lightbar_switch.connect("notify::active", lambda switch, _p:
                                     self.lightbar_colour.set_sensitive(switch.get_active()))
        self.lightbar_row.add_suffix(self.lightbar_colour)
        self.lightbar_row.add_suffix(self.lightbar_switch)
        self.lightbar_row.set_activatable_widget(self.lightbar_switch)
        controls.add(self.lightbar_row)
        # The keyboard's layout (runtime_pad.c keyboard_layout): its keys are the defaults below.
        self.keyboard_layout_row = combo_row(tr("Раскладка клавиатуры"),
                                             tr("Назначенные вами клавиши сохраняются"),
                                             KEYBOARD_LAYOUTS,
                                             "classic" if self.ini.get("keyboard_layout") == "classic" else "0.7")
        keys.add(self.keyboard_layout_row)
        # Bindings: "Assign" waits for a key or button (bb-gpu-capabilities --read-input).
        self.control_rows = {}
        for kind, title, icon in (("key", tr("Клавиатура и мышь"), "input-keyboard-symbolic"),
                                  ("pad", tr("Геймпад"), "input-gaming-symbolic")):
            expander = Adw.ExpanderRow(title=title,
                                       subtitle=tr("Назначение кнопок; применяется при запуске игры"))
            for name, label, key_default, pad_default in CONTROLS:
                default = key_default if kind == "key" else pad_default
                if default is None:
                    continue
                row = Adw.ActionRow(title=tr(label))
                # The control's name in the tooltips too: a screen reader says which one they are for.
                row.add_suffix(flat_button(icon, f'{tr("Назначить")}: {tr(label)}',
                                           lambda _b, k=kind, n=name: self.assign_control(k, n)))
                row.add_suffix(flat_button("edit-undo-symbolic", f'{tr("Сбросить")}: {tr(label)}',
                                           lambda _b, k=kind, n=name: self.set_control(k, n, None)))
                expander.add_row(row)
                self.control_rows[(kind, name)] = (row, default)
                self.show_control(kind, name)
            (keys if kind == "key" else controls).add(expander)
        self.keyboard_layout_row.connect("notify::selected", lambda *_: self.on_keyboard_layout())
        # Mouse look (runtime_pad.c): a click in the game takes the mouse, F1 lets it go.
        self.mouse_look_row = Adw.SwitchRow(
            title=tr("Камера мышью"),
            subtitle=tr("Щелчок в окне игры захватывает мышь, F1 — отпускает"),
            active=self.ini.get("mouse_look", "1") == "1")
        keys.add(self.mouse_look_row)
        self.mouse_sensitivity_row = Adw.SpinRow.new_with_range(0.1, 10.0, 0.05)
        self.mouse_sensitivity_row.set_title(tr("Чувствительность мыши"))
        self.mouse_sensitivity_row.set_digits(2)
        self.mouse_sensitivity_row.set_value(number(self.ini.get("mouse_sensitivity", "1.0"), "1.0",
                                                    key="mouse_sensitivity"))
        keys.add(self.mouse_sensitivity_row)
        self.mouse_invert_row = Adw.SwitchRow(title=tr("Инвертировать мышь по вертикали"),
                                              active=self.ini.get("mouse_invert_y") == "1")
        keys.add(self.mouse_invert_row)
        self.mouse_invert_x_row = Adw.SwitchRow(title=tr("Инвертировать мышь по горизонтали"),
                                                active=self.ini.get("mouse_invert_x") == "1")
        keys.add(self.mouse_invert_x_row)
        def mouse_rows_sensitive(*_):
            for row in (self.mouse_sensitivity_row, self.mouse_invert_row, self.mouse_invert_x_row):
                row.set_sensitive(self.mouse_look_row.get_active())
        self.mouse_look_row.connect("notify::active", mouse_rows_sensitive)
        mouse_rows_sensitive()
        self.place("controls", 10, controls)
        self.place("controls", 20, keys)

        # Hunter's Atlas (MikeTat1988): a fullscreen map in the game's quick menu. Its maps are made
        # from the player's game files by its generator (bbport_atlas_maps: Prepare maps).
        atlas = Adw.PreferencesGroup(title=tr("Карта (Hunter's Atlas)"))
        self.atlas_row = Adw.SwitchRow(title=tr("Карта в игре"), active=self.settings["atlas"])
        atlas.add(self.atlas_row)
        self.atlas_travel_row = Adw.SwitchRow(title=tr("Путешествие к фонарям с карты"),
                                              active=self.settings["atlas_travel"])
        atlas.add(self.atlas_travel_row)
        self.atlas_items_row = Adw.SwitchRow(title=tr("Предметы на карте"), active=self.settings["atlas_items"])
        atlas.add(self.atlas_items_row)
        self.atlas_maps_row = Adw.ActionRow(title=tr("Карты"))
        self.atlas_prepare_button = Gtk.Button(valign=Gtk.Align.CENTER)
        self.atlas_prepare_button.connect("clicked", self.on_atlas_prepare)
        self.atlas_maps_row.add_suffix(self.atlas_prepare_button)
        self.atlas_delete_button = flat_button("user-trash-symbolic", tr("Удалить карты"),
                                               lambda _b: self.on_atlas_delete())
        self.atlas_maps_row.add_suffix(self.atlas_delete_button)
        atlas.add(self.atlas_maps_row)
        # While the maps are made: the step, its progress and Cancel.
        self.atlas_progress_row = Adw.ActionRow(title=tr("Подготовка карт"))
        self.atlas_progress = Gtk.ProgressBar(valign=Gtk.Align.CENTER, hexpand=True, show_text=True)
        self.atlas_progress_row.add_suffix(self.atlas_progress)
        self.atlas_cancel_button = Gtk.Button(label=tr("Отмена"), valign=Gtk.Align.CENTER)
        self.atlas_cancel_button.connect("clicked", lambda _b: self.stop_atlas_job())
        self.atlas_progress_row.add_suffix(self.atlas_cancel_button)
        self.atlas_progress_row.set_visible(False)
        atlas.add(self.atlas_progress_row)
        self.atlas_row.connect("notify::active", lambda *_: self.show_atlas())
        self.show_atlas()
        self.place("mods", 30, atlas)

        upscaler = Adw.PreferencesGroup(
            title=tr("Апскейлер"),
            description=tr("Хранится в bbport.ini; в игре меняется через меню (Insert или L3+R3)"))
        self.upscaler_row = combo_row(tr("Апскейлер"), None, UPSCALERS, self.ini["upscaler"])
        self.upscaler_row.connect("notify::selected", lambda *_: self.update_upscaler_status())
        upscaler.add(self.upscaler_row)
        # FSR 4.1.1 is built from the user's own AMD DLL (nothing of AMD's is shipped).
        self.fsr411_row = Adw.ActionRow(title=tr("FSR 4.1.1 из своей DLL AMD"))
        self.fsr411_button = Gtk.Button(valign=Gtk.Align.CENTER)
        self.fsr411_button.connect("clicked", self.on_fsr411_button)
        self.fsr411_row.add_suffix(self.fsr411_button)
        self.fsr411_row.set_visible((FSR4CAP_DIR / "build_assets.sh").is_file())
        upscaler.add(self.fsr411_row)
        # FSR 4.1.2's models (INT8 RDNA2, INT8 Lite) from AMD's driver, also the user's own.
        self.fsr412_row = Adw.ActionRow(title=tr("FSR 4.1.2 из драйвера AMD"))
        self.fsr412_button = Gtk.Button(valign=Gtk.Align.CENTER, label=tr("Выбрать файл…"))
        self.fsr412_button.connect("clicked", self.on_fsr412_button)
        self.fsr412_row.add_suffix(self.fsr412_button)
        self.fsr412_row.set_subtitle(tr(
            "Модели INT8 RDNA2 и INT8 Lite: установщик AMD Adrenalin 26.10.1+ (.exe) или "
            "amdxcffx64.dll из него. Нужна и DLL FSR 4.1.x (как для FSR 4.1.1); ~4 минуты. "
            "Модель выбирается в меню игры"))
        self.fsr412_row.set_visible((FSR4CAP_DIR / "driver_model.py").is_file())
        upscaler.add(self.fsr412_row)
        self.update_fsr411_row()
        # DLSS: NVIDIA's library, chosen like the FSR 4.1.1 DLL (the package may bring one).
        self.dlss_row = Adw.ActionRow(title=tr("DLSS: библиотека NVIDIA"))
        self.dlss_row.add_suffix(flat_button("document-open-symbolic", tr("Выбрать файл…"),
                                             lambda _b: self.choose_ngx()))
        self.dlss_reset_button = flat_button("edit-undo-symbolic", tr("Убрать выбранную"),
                                             lambda _b: self.reset_ngx())
        self.dlss_row.add_suffix(self.dlss_reset_button)
        upscaler.add(self.dlss_row)
        self.update_dlss_row()
        # Frame generation (the game's menu has it too): FSR 3.1 on any GPU (experimental), DLSS
        # where an NVIDIA GPU is connected (or the GPUs are unknown).
        vendors = {vendor.lower() for _index, vendor, _kind, _name, _best in connected_gpus()}
        nvidia = not vendors or any("10de" in vendor for vendor in vendors)
        frame_gens = [FRAME_GENS[0], ("FSR 3.1 (экспериментально)", "fsr3")]
        frame_gens += [entry for entry in FRAME_GENS[1:] if nvidia or self.ini.get("frame_generation") == "dlss"]
        self.frame_gen_row = combo_row(
            tr("Генерация кадров"),
            tr("Кадры между кадрами игры. FSR 3.1 — на любой видеокарте, пока экспериментально "
               "(возможны артефакты по краям). DLSS: нужны мост DLSS, libnvidia-ngx-dlssg.so от NVIDIA "
               "(выбирается выше, как библиотека DLSS) и GeForce RTX 40 или новее; 3x и 4x — RTX 50"),
            frame_gens, frame_gen_choice(self.ini))
        upscaler.add(self.frame_gen_row)
        self.preset_row = combo_row(tr("Пресет"), None, PRESETS,
                                    number(self.ini.get("preset", "4"), "4", int, key="preset"))
        self.preset_row.connect("notify::selected", lambda *_: self.update_upscaler_status())
        self.output_row.connect("notify::selected", lambda *_: self.update_upscaler_status())
        upscaler.add(self.preset_row)
        self.sharpen_row = Adw.SwitchRow(title=tr("Резкость (RCAS)"),
                                         subtitle=tr("И без апскейлера: поверх сглаживания игры или FXAA"),
                                         active=self.ini.get("sharpen") == "1")
        upscaler.add(self.sharpen_row)
        self.sharpness_row = Adw.SpinRow.new_with_range(0.0, 2.0, 0.05)
        self.sharpness_row.set_title(tr("Сила резкости"))
        self.sharpness_row.set_digits(2)
        self.sharpness_row.set_value(number(self.ini.get("sharpness", "0.5"), "0.5",
                                            key="sharpness"))
        upscaler.add(self.sharpness_row)
        self.motion_row = Adw.SwitchRow(
            title=tr("Векторы движения объектов"),
            subtitle=tr("Меньше гостинга на персонажах; стоит около 10% FPS"),
            active=self.ini.get("object_motion") == "1")
        upscaler.add(self.motion_row)
        self.show_fps_row = Adw.SwitchRow(title=tr("Показывать FPS"),
                                          active=self.ini.get("show_fps") == "1")
        upscaler.add(self.show_fps_row)
        self.place("graphics", 20, upscaler)

        effects = Adw.PreferencesGroup(title=tr("Эффекты игры"),
                                       description=tr("Патчи игры, применяются при запуске"))
        self.lod_row = combo_row(tr("Детализация моделей"), None, MODEL_LOD,
                                 self.ini.get("model_lod", "0"))
        effects.add(self.lod_row)
        self.texture_row = combo_row(tr("Качество текстур"), tr("Крупные текстуры в видеопамяти"),
                                     TEXTURE_QUALITY, self.ini.get("texture_quality", "auto"))
        effects.add(self.texture_row)
        # anti_aliasing replaces effect_game_aa (bbport_settings.cpp reads the old key the same way).
        saved_aa = self.ini.get("anti_aliasing") or ("off" if self.ini.get("effect_game_aa") == "0" else "auto")
        self.aa_row = combo_row(tr("Сглаживание"), None, ANTI_ALIASING, saved_aa)
        effects.add(self.aa_row)
        self.vbao_row = Adw.SwitchRow(title=tr("Затенение GT-VBAO"),
                                      subtitle=tr("Вместо SSAO игры (нужно затенение SSAO)"),
                                      active=self.ini.get("vbao") == "1")
        effects.add(self.vbao_row)
        self.effect_rows = {}
        menus = Adw.PreferencesGroup(title=tr("Меню и отладка"),
                                     description=tr("Патчи игры, применяются при запуске"))
        for key, title, default in sorted(EFFECTS, key=lambda e: e[0] in GAME_MENU_EFFECTS
                                          and GAME_MENU_EFFECTS.index(e[0]) + 1):
            row = Adw.SwitchRow(title=tr(title),
                                active=self.ini.get(key, "1" if default else "0") == "1")
            if key == "debug_menu":
                row.set_subtitle(tr("Нужна папка adhoc из мода Nexus #253 (шрифты adhoc/font) — в "
                                    "dvdroot_ps4 игры или модом; без неё патч не применяется"))
            self.effect_rows[key] = row
            (menus if key in GAME_MENU_EFFECTS else effects).add(row)
        # The title's "play online / play offline": answered as the Online page's switch.
        self.skip_network_row = Adw.SwitchRow(
            title=tr("Пропускать выбор «по сети / вне сети»"),
            subtitle=tr("Игра сразу открывает главное меню: в сети, если включена игра по сети, "
                        "иначе вне сети (патч игры)"),
            active=self.settings.get("skip_network_choice", True))
        # On the Multiplayer page's online tab (build_online_page).
        self.netchoice_group = Adw.PreferencesGroup()
        self.netchoice_group.add(self.skip_network_row)
        self.place("graphics", 40, effects)
        self.place("mods", 45, menus)

        streaming = Adw.PreferencesGroup(title=tr("Загрузки и плавность"),
                                         description=tr("Патчи игры из bbhost, применяются при запуске"))
        self.streaming_rows = {}
        for key, title, subtitle, default in STREAMING:
            row = Adw.SwitchRow(title=tr(title), subtitle=tr(subtitle),
                                active=self.ini.get(key, "1" if default else "0") == "1")
            self.streaming_rows[key] = row
            streaming.add(row)
        self.place("advanced", 25, streaming)

        frames = Adw.PreferencesGroup(title=tr("Частота кадров"))
        self.fps_row = combo_row(tr("Режим"), tr("Какой патч частоты кадров применить к игре"),
                                 FPS_MODES, self.settings["fps_mode"])
        frames.add(self.fps_row)
        self.limit_row = Adw.SpinRow.new_with_range(0, 480, 1)
        self.limit_row.set_title(tr("Ограничение FPS"))
        self.limit_row.set_subtitle(tr("0 — без ограничения; укажите число, чтобы ограничить FPS"))
        self.limit_row.set_value(number(self.settings["fps_limit"], 0, int, "settings.json",
                                        "fps_limit"))
        # Above about 120 FPS the game's movement timing breaks (Supermedo 51cac0e): a cap above it
        # is marked, and says why.
        self.limit_warning = Gtk.Image(icon_name="dialog-warning-symbolic", visible=False,
                                       tooltip_text=tr("Выше 120 FPS движение в игре может ломаться: "
                                                       "бег и перекаты замедляются"))
        self.limit_row.add_prefix(self.limit_warning)

        def show_limit(*_):
            high = self.limit_row.get_value() > 120
            self.limit_warning.set_visible(high)
            self.limit_row.set_subtitle(self.limit_warning.get_tooltip_text() if high else
                                        tr("0 — без ограничения; укажите число, чтобы ограничить FPS"))
        self.limit_row.connect("notify::value", show_limit)
        show_limit()
        frames.add(self.limit_row)
        self.place("graphics", 30, frames)

        perf = Adw.PreferencesGroup(title=tr("Производительность"))
        # Low latency (Reflex, Anti-Lag 2): with DLSS frame generation at least on (the game enforces
        # it; the row follows so that what is shown is what runs).
        low_latency = self.ini.get("low_latency", "on")
        self.low_latency_row = combo_row(
            tr("Низкая задержка (NVIDIA Reflex / AMD Anti-Lag 2)"),
            tr("Поток игры ждёт драйвер перед каждым кадром, чтобы кадры не копились перед "
               "видеокартой: меньше задержка ввода. NVIDIA: Reflex, драйвер 550 и новее; AMD и Intel: "
               "Anti-Lag 2 (Boost — то же, что «Включена»). С генерацией кадров DLSS всегда не ниже "
               "«Включена»"),
            LOW_LATENCIES, low_latency if low_latency in ("on", "boost", "off") else "on")

        def enforce_low_latency(*_):
            if combo_value(self.frame_gen_row).startswith("dlss") and combo_value(self.low_latency_row) == "off":
                self.low_latency_row.set_selected(0)  # "on"
        self.frame_gen_row.connect("notify::selected", enforce_low_latency)
        self.low_latency_row.connect("notify::selected", enforce_low_latency)
        enforce_low_latency()
        perf.add(self.low_latency_row)
        self.pipe_row = combo_row(
            tr("Двухстадийный конвейер GPU"),
            tr("Быстрее на 20–30%; при нестабильности выключите"), DRAW_PIPE,
            self.settings["draw_pipe"])
        perf.add(self.pipe_row)
        self.readbacks_row = combo_row(tr("Чтение данных GPU процессором"), None, READBACKS,
                                       self.settings["readbacks"])
        perf.add(self.readbacks_row)
        self.cache_row = Adw.ActionRow(title=tr("Кэш шейдеров"))
        self.cache_button = Gtk.Button(label=tr("Очистить"), valign=Gtk.Align.CENTER)
        self.cache_button.connect("clicked", self.on_clear_cache)
        self.cache_row.add_suffix(self.cache_button)
        perf.add(self.cache_row)
        self.show_cache()
        self.place("advanced", 20, perf)

        dev = Adw.PreferencesGroup(title=tr("Для разработчика"))
        self.mangohud_row = Adw.SwitchRow(title="MangoHud", active=self.settings["mangohud"])
        dev.add(self.mangohud_row)
        self.save_log_row = Adw.SwitchRow(
            title=tr("Сохранять журнал и статистику в файл"),
            subtitle=tr("В папку logs в каталоге данных: для разбора рывков и вылетов"),
            active=self.settings.get("save_log", False))
        dev.add(self.save_log_row)
        self.crash_diag_row = Adw.SwitchRow(
            title=tr("Диагностика вылетов"),
            subtitle=tr("Проверяет кучу игры и записывает записи в её память; немного медленнее"),
            active=self.settings.get("crash_diag", False))
        dev.add(self.crash_diag_row)
        self.stats_row = Adw.SwitchRow(title=tr("Статистика кадров в журнале"),
                                       subtitle="BB_FRAME_STATS",
                                       active=self.settings["frame_stats"])
        dev.add(self.stats_row)
        self.profile_row = Adw.SwitchRow(title=tr("Профиль GPU в журнале"),
                                         subtitle="BB_GPU_PROFILE",
                                         active=self.settings["gpu_profile"])
        dev.add(self.profile_row)
        self.validation_row = Adw.SwitchRow(title=tr("Слои валидации Vulkan"),
                                            subtitle=tr("Сильно замедляет"),
                                            active=self.settings["vk_validation"])
        dev.add(self.validation_row)
        self.extra_row = Adw.EntryRow(title=tr("Доп. переменные (ИМЯ=значение через пробел)"),
                                      text=self.settings["extra_env"])
        dev.add(self.extra_row)
        self.place("advanced", 30, dev)

    def on_ui_language(self, row, _param):
        choice = combo_value(row)
        if choice == self.settings.get("ui_language", ""):
            return
        self.store()
        self.settings["ui_language"] = choice
        save_settings(self.settings)
        if self.busy():
            set_language(choice)
            self.rebuild_waiting = True
            self.toasts.add_toast(Adw.Toast(
                title=tr("Язык лаунчера сменится, когда закончатся игра и текущие операции")))
            return
        set_language(choice)
        # After this handler returns: the row that emitted the signal is replaced.
        GLib.idle_add(lambda: self.build() and False)

    def game_dir(self):
        return Path(self.settings["game_dir"]).expanduser()

    def show_cache(self):
        """The shader cache's size; it can be cleared while the game is not running."""
        size = bbport_cache.size(self.user_dir())
        self.cache_row.set_subtitle(
            tr("{}. Если после обновления картинка выглядит странно, очистите его: шейдеры "
               "соберутся заново (первые минуты в каждой зоне возможны рывки)").format(
                GLib.format_size(size)) if size else tr("Пусто: шейдеры соберутся при игре"))
        self.cache_button.set_sensitive(bool(size) and self.process is None)

    def on_clear_cache(self, _button):
        dialog = Adw.AlertDialog(heading=tr("Очистить кэш шейдеров?"), body=tr(
            "Игра соберёт шейдеры заново: первые минуты в каждой зоне возможны рывки. Сохранения "
            "и настройки не затрагиваются."))
        dialog.add_response("cancel", tr("Отмена"))
        dialog.add_response("clear", tr("Очистить"))
        dialog.set_response_appearance("clear", Adw.ResponseAppearance.DESTRUCTIVE)

        def answered(_dialog, response):
            if response == "clear" and self.process is None:
                try:
                    bbport_cache.clear(self.user_dir())
                except OSError as error:
                    self.alert(tr("Очистить кэш шейдеров?"), tr("Не удалось очистить кэш: {}").format(error))
                self.show_cache()

        dialog.connect("response", answered)
        self.present_dialog(dialog)

    def user_dir(self):
        return Path(self.settings["user_dir"]).expanduser() if self.settings["user_dir"] \
            else DATA_DIR / "user"

    def update_user_status(self):
        path = self.user_dir()
        custom = bool(self.settings["user_dir"])
        saves = path / "savedata"
        found = saves.is_dir() and any(saves.iterdir())
        self.user_row.set_subtitle(GLib.markup_escape_text("\n".join((
            str(path) if custom else tr("По умолчанию: {}").format(path),
            tr("Найдены сохранения") if found else tr("Сохранений пока нет: игра создаст их здесь")))))
        self.user_reset.set_enabled(custom)
        if hasattr(self, "cache_row"):
            self.show_cache()

    def update_dlc_status(self):
        path = self.settings.get("dlc_dir", "")
        found = []
        if path:
            try:
                info = sfo((self.game_dir() / "sce_sys/param.sfo").read_bytes())
                found = dlc_addons(Path(path).expanduser(), info.get("TITLE_ID"))
            except (OSError, ValueError, IndexError):
                pass
        self.dlc_row.set_subtitle(f"{path}\n{tr('Найдено DLC: {}').format(len(found))}" if path
                                  else tr("Не используется"))
        self.dlc_status.set_from_icon_name("object-select-symbolic" if found else
                                           "dialog-warning-symbolic" if path else None)
        self.dlc_status.set_tooltip_text(", ".join(found)
                                         or (tr("Нет DLC этой игры в папке") if path else None))
        self.dlc_reset.set_enabled(bool(path))

    def on_choose_dlc(self, _button):
        def chosen(path):
            self.settings["dlc_dir"] = path
            self.update_dlc_status()
            self.store()
        self.choose_folder(tr("Папка DLC"), self.settings.get("dlc_dir") or self.game_dir(), chosen)

    def on_reset_dlc(self, _button):
        self.settings["dlc_dir"] = ""
        self.update_dlc_status()
        self.store()

    def choose_folder(self, title, current, done):
        dialog = Gtk.FileDialog(title=title)
        if Path(current).is_dir():
            dialog.set_initial_folder(Gio.File.new_for_path(str(current)))

        def finish(dialog, result):
            try:
                folder = dialog.select_folder_finish(result)
            except GLib.Error:
                return
            if folder:
                done(folder.get_path())
        dialog.select_folder(self, None, finish)

    def on_choose_user(self, _button):
        def chosen(path):
            self.settings["user_dir"] = path
            self.update_user_status()
            self.store()
        self.choose_folder(tr("Папка сохранений"), self.user_dir(), chosen)

    def on_import_saves(self, _button):
        """Saves from shadPS4, another port or a decrypted PS4 export (scripts/save_import.py)."""
        if self.process is not None or save_import.game_running():
            self.alert(tr("Импорт сохранений"), tr("Сначала закройте игру"))
            return
        shadps4 = Path.home() / ".local/share/shadPS4"
        self.choose_folder(tr("Папка с сохранениями Bloodborne"),
                           shadps4 if shadps4.is_dir() else Path.home(), self.confirm_import_saves)

    def on_export_saves(self, _button):
        """The saves in use into a .zip, a backup or the saves for another computer; Import takes
        it back (scripts/save_import.py)."""
        if self.process is not None or save_import.game_running():
            self.alert(tr("Экспорт сохранений"), tr("Сначала закройте игру"))
            return
        if save_import.saves_in_use(self.user_dir(), self.settings["game_dir"] or None) is None:
            self.alert(tr("Экспорт сохранений"), tr("Сохранений пока нет: игра создаст их здесь"))
            return
        dialog = Gtk.FileDialog(title=tr("Экспорт сохранений"))
        dialog.set_initial_name(f"Bloodborne-saves-{time.strftime('%Y-%m-%d')}.zip")

        def finish(dialog, result):
            try:
                chosen = dialog.save_finish(result)
            except GLib.Error:
                return
            if not chosen or not chosen.get_path():
                return
            target = Path(chosen.get_path())
            if target.suffix.lower() != ".zip":
                target = target.with_name(target.name + ".zip")
            try:
                count = save_import.export_saves(self.user_dir(), target, self.settings["game_dir"] or None)
            except (save_import.SaveImportError, OSError) as error:
                self.alert(tr("Не удалось экспортировать сохранения"), str(error))
                return
            self.append_log(f"Saves exported into {target} ({count} files)\n")
            self.toasts.add_toast(Adw.Toast(title=tr("Сохранения экспортированы: {}").format(target)))
        dialog.save(self, None, finish)

    def on_import_saves_archive(self, _button):
        """A .zip exported here (or a PS4 export zipped): its save files are read out into a
        folder of its own, then imported as a folder would be."""
        if self.process is not None or save_import.game_running():
            self.alert(tr("Импорт сохранений"), tr("Сначала закройте игру"))
            return
        dialog = Gtk.FileDialog(title=tr("Архив с сохранениями (.zip)"))
        archives = Gtk.FileFilter()
        archives.set_name("ZIP")
        archives.add_pattern("*.zip")
        archives.add_pattern("*.ZIP")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(archives)
        dialog.set_filters(filters)
        dialog.set_default_filter(archives)

        def finish(dialog, result):
            try:
                chosen = dialog.open_finish(result)
            except GLib.Error:
                return
            if not chosen or not chosen.get_path():
                return
            unpacked = Path(tempfile.mkdtemp(prefix="bbport-saves-")) / save_import.SAVE_DIR
            try:
                save_import.unpack_export(chosen.get_path(), unpacked)
            except (save_import.SaveImportError, OSError) as error:
                shutil.rmtree(unpacked.parent, ignore_errors=True)
                self.alert(tr("Не удалось импортировать сохранения"), str(error))
                return
            self.confirm_import_saves(unpacked, shown=chosen.get_path(),
                                      done=lambda: shutil.rmtree(unpacked.parent, ignore_errors=True))
        dialog.open(self, None, finish)

    def confirm_import_saves(self, folder, shown=None, done=None):
        found = save_import.find(folder)
        if not found:
            self.alert(tr("Импорт сохранений"), tr(
                "Это копия с PS4 на флешке (sdimg_*): она зашифрована ключами консоли. Экспортируйте "
                "сохранение без шифрования на PS4 (Apollo Save Tool) или через Save Wizard")
                if save_import.encrypted_ps4_save(folder)
                else tr("В этой папке нет сохранений Bloodborne (SPRJ0005, userdata)"))
            if done:
                done()
            return
        source, when = found[0]
        dialog = Adw.AlertDialog(heading=tr("Импортировать сохранения?"), body=tr(
            "Из {} (изменены {}). Текущие сохранения сначала копируются в {}").format(
                shown or source, time.strftime("%Y-%m-%d %H:%M", time.localtime(when)),
                self.user_dir() / "savedata-backups"))
        dialog.add_response("cancel", tr("Отмена"))
        dialog.add_response("import", tr("Импортировать"))
        dialog.set_response_appearance("import", Adw.ResponseAppearance.SUGGESTED)

        def answered(_dialog, response):
            try:
                if response == "import":
                    imported(*save_import_now())
            finally:
                if done:
                    done()  # an archive's unpacked copy

        def save_import_now():
            if self.process is not None or save_import.game_running():
                self.alert(tr("Импорт сохранений"), tr("Сначала закройте игру"))
                return None, None
            try:
                return save_import.import_saves(source, self.user_dir(), self.settings["game_dir"] or None)
            except (save_import.SaveImportError, OSError) as error:
                self.alert(tr("Не удалось импортировать сохранения"), str(error))
                return None, None

        def imported(target, backup):
            if target is None:
                return
            self.append_log(f"Saves imported from {shown or source} into {target}"
                            + (f"; previous saves in {backup}\n" if backup else "\n"))
            self.update_user_status()
            self.toasts.add_toast(Adw.Toast(title=tr("Сохранения импортированы")))

        dialog.connect("response", answered)
        self.present_dialog(dialog)

    def on_reset_user(self, _button):
        self.settings["user_dir"] = ""
        self.update_user_status()
        self.store()

    def update_upscaler_status(self):
        value = combo_value(self.upscaler_row)
        if value == "fsr4":
            ok = (PORT_DIR / "fsr4_shaders").is_dir()
            hint = tr("Ассеты найдены") if ok else tr("Нет ассетов: tools/fetch_fsr4_assets.sh")
        elif value == "fsr411":
            directory = fsr411_dir()
            problem = fsr411_problem(directory, combo_value(self.output_row),
                                     int(combo_value(self.preset_row)))
            hint = tr("Ассеты для выбранного режима найдены") if not problem else (
                tr("{}. Соберите FSR 4.1.1 из своей DLL кнопкой «Выбрать DLL…» ниже").format(problem))
        elif value == "dlss":
            # The bridge and NVIDIA's library (vk_dlss.cpp); without them DLSS falls back to FSR 3.1.
            binaries = dlss_dir()
            found = (binaries / "libbbport_dlss.so").is_file() and bool(
                ngx_libraries(self.user_dir() / "dlss") or ngx_libraries(binaries))
            hint = tr("DLSS найден (нужна видеокарта NVIDIA RTX)") if found else tr(
                "DLSS не найден: выберите библиотеку NVIDIA ниже (и нужна сборка с мостом DLSS). Игра включит FSR 3.1")
        else:
            hint = tr("Сглаживание в разрешении вывода без модели FSR") if value == "taa" else None
        self.preset_row.set_sensitive(value not in ("taa", "off"))
        self.sharpen_row.set_sensitive(value != "off")
        self.sharpness_row.set_sensitive(value != "off")
        self.upscaler_row.set_subtitle(hint or "")

    def game_problem(self, path):
        """game_check.problem for the folder, kept until its eboot.bin or param.sfo changes (the
        image hash reads ~90 MB)."""
        try:
            key = (str(path),) + tuple(
                (f.stat().st_size, f.stat().st_mtime_ns) for f in (path / "eboot.bin", path / "sce_sys/param.sfo"))
        except OSError:
            key = (str(path),)
        if getattr(self, "_game_problem_key", None) != key:
            self._game_problem_key = key
            self._game_problem = game_check.problem(path)
        return self._game_problem

    def busy(self):
        return (self.process is not None or self.atlas_job is not None
                or self.fsr411_build is not None or bool(self.working))

    def work_done(self, name=None):
        """An operation has ended: the rebuild a language change waits for, once nothing runs."""
        self.working.discard(name)
        if self.rebuild_waiting and not self.busy():
            self.rebuild_waiting = False
            # What changed meanwhile (an account signed in included) is kept: build() reads the
            # settings and bbport.ini, and starts change tracking (issue #21) afresh.
            GLib.idle_add(self.waited_rebuild)

    def waited_rebuild(self):
        if self.busy():  # the game started meanwhile (Play right after the work)
            self.rebuild_waiting = True
        else:
            self.store()
            self.build()
        return False

    def game_found(self):
        return bool(self.settings["game_dir"]) and (self.game_dir() / "eboot.bin").is_file()

    def with_gamepads(self, then):
        """Looks at the gamepads in a thread (bb-gpu-capabilities, 0.3 s) and then calls `then` on
        the main loop, with the look fresh in connected_gamepads: Play (the button prompts follow
        the controller), local co-op and Refresh no longer freeze the window. Play waits for it."""
        if "gamepads" in self.working:
            return
        self.working.add("gamepads")
        self.update_launch_sensitivity()

        def work():
            connected_gamepads(fresh=True)
            GLib.idle_add(done)

        def done():
            self.work_done("gamepads")
            self.update_launch_sensitivity()
            then()
            return False
        threading.Thread(target=work, daemon=True).start()

    def can_start(self):
        """Whether a game can start now: not from a half-built window (build), not without the
        game, and not with an FSR 4.1.1 build (both want the GPU, the build replaces the assets
        the game reads) or the map's files being made (the game would read half-made maps)."""
        return (not self.build_errors and self.process is None and self.game_found()
                and self.fsr411_build is None and self.atlas_job is None
                and "gamepads" not in self.working)

    def update_launch_sensitivity(self):
        # Stop is always there.
        self.launch_button.set_sensitive(self.process is not None or self.can_start())
        if hasattr(self, "coop_button"):
            self.coop_button.set_sensitive(self.can_start())

    def update_game_status(self):
        path = self.game_dir()
        ok = self.game_found()
        self.game_row.set_subtitle(str(path) if self.settings["game_dir"] else tr("не выбрана"))
        # The title ID of the release in the folder (CUSA00900, CUSA03173, ...), from its param.sfo.
        try:
            title_id = str(sfo((path / "sce_sys/param.sfo").read_bytes()).get("TITLE_ID", "")) if ok else ""
        except (OSError, ValueError, IndexError):
            title_id = ""
        self.game_row.set_title(tr("Папка игры ({})").format(title_id) if title_id else tr("Папка игры"))
        # Other versions of the game start and then crash in its code (issues #7, #13, #14).
        problem = self.game_problem(path) if ok else None
        if not self.settings["game_dir"]:
            tooltip = tr("Сначала выберите папку игры")
        elif not ok:
            tooltip = tr("Нет eboot.bin в папке")
            self.game_row.set_subtitle(f"{path}\n{tooltip}")  # the reason, not only in a tooltip
        elif problem:
            kind, title, version = problem
            tooltip = {
                "missing_update": tr("Нужно обновление 1.09: скопируйте файлы дампа обновления 1.09 в папку игры с заменой (найдена версия {})").format(version),
                "wrong_eboot": tr("eboot.bin не от версии 1.09: скопируйте eboot.bin из дампа обновления 1.09 в папку игры с заменой"),
                "patched_eboot": tr("eboot.bin с вшитым патчем 60 FPS от Lance McDonald: из-за него игра падает в меню жестов. Скопируйте чистый eboot.bin из дампа обновления 1.09 в папку игры с заменой"),
                "other_title": tr("Это не магазинное издание Bloodborne (найдено {}): нужен Bloodborne любого региона с обновлением 1.09").format(title),
                "unreadable": tr("eboot.bin не читается как расшифрованный исполняемый файл PS4: сделайте дамп заново"),
                "damaged_files": tr("Файлы игры повреждены при распаковке: шейдеры не распаковываются, игра зависнет на загрузке. Распакуйте игру и обновление 1.09 заново исправленным инструментом (issue #81)"),
            }[kind]
            self.game_row.set_subtitle(f"{path}\n{tooltip}")
        else:
            tooltip = tr("Bloodborne {}, версия 1.09").format(title_id or "")
        self.game_banner.set_title(tr("Чтобы играть, выберите папку игры") if not self.settings["game_dir"]
                                   else tr("В папке игры нет eboot.bin: выберите другую"))
        self.game_banner.set_revealed(not ok)
        self.game_status.set_from_icon_name("object-select-symbolic" if ok and not problem else "dialog-warning-symbolic")
        self.game_status.set_tooltip_text(tooltip)
        self.update_launch_sensitivity()

    def on_install_pkg(self, _button):
        """The packages, then the folder to install into; scripts/pkg_install.py does the rest."""
        dialog = Gtk.FileDialog(title=tr("Файлы .pkg: игра, обновление, DLC"))
        pkg_filter = Gtk.FileFilter(name="PS4 .pkg")
        pkg_filter.add_pattern("*.pkg")
        pkg_filter.add_pattern("*.PKG")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(pkg_filter)
        dialog.set_filters(filters)

        def picked(dialog, result):
            try:
                files = dialog.open_multiple_finish(result)
            except GLib.Error:
                return
            pkgs = [files.get_item(i).get_path() for i in range(files.get_n_items())]
            if pkgs:
                self.choose_folder(tr("Куда установить игру"), Path(pkgs[0]).parent,
                                   lambda dest: self.install_pkg(pkgs, dest))
        dialog.open_multiple(self, None, picked)

    def install_pkg(self, pkgs, dest):
        self.pkg_button.set_sensitive(False)
        self.working.add("pkg")
        self.pkg_row.set_subtitle(tr("Установка…"))
        command = [sys.executable, str(PORT_DIR / "scripts/pkg_install.py"), "--dest", dest,
                   "--extractor", pkg_extractor(), *pkgs]

        def line(text):
            self.append_log(text + "\n")
            if text.startswith("Install: "):
                self.pkg_row.set_subtitle(GLib.markup_escape_text(text[len("Install: "):]))
            return False

        def finished(status, found):
            self.pkg_button.set_sensitive(True)
            self.work_done("pkg")
            if "GAME_DIR" in found:
                self.settings["game_dir"] = found["GAME_DIR"]
                if "DLC_DIR" in found:
                    self.settings["dlc_dir"] = found["DLC_DIR"]
                self.update_game_status()
                self.update_dlc_status()
                self.store()
            if status == 0:
                self.toasts.add_toast(Adw.Toast(title=tr("Игра установлена: {}").format(found["GAME_DIR"])))
            elif status != 3:   # 3: installed, and the game check says what is missing
                self.pkg_row.set_subtitle(tr("Не удалось установить: подробности в журнале"))
            return False

        def work():
            found, status = {}, 1
            try:
                with subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT, text=True) as process:
                    for text in process.stdout:
                        text = text.rstrip("\n")
                        key, sep, value = text.partition("=")
                        if sep and key in ("GAME_DIR", "DLC_DIR"):
                            found[key] = value
                        GLib.idle_add(line, text)
                status = process.returncode
            except OSError as error:
                GLib.idle_add(line, f"Install failed: {error}")
            GLib.idle_add(finished, status, found)
        threading.Thread(target=work, daemon=True).start()

    def on_choose_game(self, _button):
        def chosen(path):
            self.settings["game_dir"] = path
            self.update_game_status()
            self.update_dlc_status()
            self.store()
        self.choose_folder(tr("Папка игры (с eboot.bin)"), self.game_dir(), chosen)

    def on_keyboard_layout(self):
        for name, _label, key_default, _pad in CONTROLS:
            if ("key", name) in self.control_rows:
                self.show_control("key", name)
        self.store()

    def show_control(self, kind, name):
        row, default = self.control_rows[(kind, name)]
        if kind == "key" and combo_value(self.keyboard_layout_row) != "classic":
            default = KEY_DEFAULTS_07.get(name, default)
        value = self.ini.get(f"{kind}.{name}")
        if value is None:
            row.set_subtitle(tr("{} (по умолчанию)").format(default) if default else tr("не назначено"))
        else:
            row.set_subtitle(value or tr("не назначено"))

    def set_control(self, kind, name, value):
        """value: the binding, or None for the default."""
        self.ini[f"{kind}.{name}"] = value
        self.ini_controls_changed[f"{kind}.{name}"] = value
        self.show_control(kind, name)
        self.store()
        if kind == "pad" and name in ("cross", "circle"):
            self.ab_swap_syncing = True
            self.ab_swap_row.set_active(self.ab_swapped())
            self.ab_swap_syncing = False

    def ab_swapped(self):
        """Cross on the gamepad's b (east) button and circle on a (south)."""
        return ((self.ini.get("pad.cross") or "").casefold() == "b"
                and (self.ini.get("pad.circle") or "").casefold() == "a")

    def on_ab_swap(self):
        if self.ab_swap_syncing:
            return
        swap = self.ab_swap_row.get_active()
        self.set_control("pad", "cross", "b" if swap else None)
        self.set_control("pad", "circle", "a" if swap else None)

    def assign_control(self, kind, name):
        tool = PORT_DIR / ("bin" if PACKAGED else "out") / "bb-gpu-capabilities"
        try:
            process = Gio.Subprocess.new([str(tool), "--read-input", kind],
                                         Gio.SubprocessFlags.STDOUT_PIPE)
        except GLib.Error as error:
            self.toasts.add_toast(Adw.Toast(title=tr("Не удалось запустить: {}").format(error.message)))
            return
        row, _default = self.control_rows[(kind, name)]
        row.set_subtitle(tr("Нажмите клавишу или кнопку… (Esc — отмена)"))

        def done(proc, result):
            try:
                _ok, out, _err = proc.communicate_utf8_finish(result)
            except GLib.Error:
                out = ""
            words = (out or "").strip().split(" ", 1)
            if len(words) == 2 and words[0] == kind:
                self.set_control(kind, name, words[1])
            else:
                self.show_control(kind, name)
        process.communicate_utf8_async(None, None, done)

    def fill_gamepads(self):
        """The controller choices: the first connected one, the connected ones, and the chosen
        one while it is not connected (on Refresh, the row's choice, saved or not)."""
        if hasattr(self.gamepad_row, "values"):
            current = combo_value(self.gamepad_row)
            chosen = self.gamepad_row.names[self.gamepad_row.get_selected()]
        else:
            current = self.settings.get("gamepad", "")
            chosen = self.settings.get("gamepad_name") or current
        choices = [(tr("Авто"), "", tr("Тот, которым играете"))]
        choices += [(name, guid, name) for guid, name in connected_gamepads(look=False)]
        if current and current not in [guid for _, guid, _ in choices]:
            choices.append((tr("{} (не подключён)").format(chosen), current, chosen))
        self.gamepad_row.set_model(Gtk.StringList.new([label for label, _, _ in choices]))
        self.gamepad_row.values = [guid for _, guid, _ in choices]
        self.gamepad_row.names = [name for _, _, name in choices]
        self.gamepad_row.set_selected(self.gamepad_row.values.index(current) if current in self.gamepad_row.values else 0)
        self.show_gamepad()

    def fill_displays(self, row=None, key="display", first=None):
        """A monitor row's choices (Graphics → Monitor, or local co-op's): the primary one (or
        `first`), the connected ones, and the chosen one while it is not connected (on Refresh,
        the row's choice, saved or not)."""
        row = row or self.display_row
        current = combo_value(row) if hasattr(row, "values") else self.settings.get(key, "")
        choices = [(first or tr("Основной"), "")] + [(label, value) for value, label in connected_displays()]
        if current and current not in [value for _, value in choices]:
            choices.append((tr("{} (не подключён)").format(current), current))
        row.set_model(Gtk.StringList.new([label for label, _ in choices]))
        row.values = [value for _, value in choices]
        row.set_selected(row.values.index(current) if current in row.values else 0)

    def fill_gpus(self):
        """The GPU choices: the port's own (named), the GPUs found, and the saved one while it is
        not found."""
        current = self.settings.get("gpu", "")
        gpus = connected_gpus()
        best = [name for _index, _vendor, _kind, name, is_best in gpus if is_best]
        auto = tr("Авто") + (f" ({best[0]})" if best else "")
        choices = [(auto, "")]
        for _index, _vendor, kind, name, _best in gpus:
            note = {"integrated": tr("встроенная"), "cpu": tr("программная, очень медленно")}.get(kind)
            choices.append((f"{name} ({note})" if note else name, name))
        if current and current not in [value for _, value in choices]:
            choices.append((tr("{} (не найдена)").format(current), current))
        self.gpu_row.set_model(Gtk.StringList.new([label for label, _ in choices]))
        self.gpu_row.values = [value for _, value in choices]
        self.gpu_row.set_selected(self.gpu_row.values.index(current) if current in self.gpu_row.values else 0)
        self.gpu_row.set_subtitle(tr("На ноутбуке с двумя видеокартами — дискретная; применяется при запуске игры"))

    def show_gamepad(self):
        names = getattr(self.gamepad_row, "names", None)
        selected = names[self.gamepad_row.get_selected()] if names else ""
        self.gamepad_row.set_subtitle("\n".join(
            line for line in (selected, tr("Выбранный берётся, как только подключится")) if line))

    def store(self):
        if self.build_errors:
            return  # a page failed to build (issue #18): its rows may be missing
        s = self.settings
        s["gamepad"] = combo_value(self.gamepad_row)
        s["gamepad_name"] = self.gamepad_row.names[self.gamepad_row.get_selected()]
        s["display"] = combo_value(self.display_row)
        s["gpu"] = combo_value(self.gpu_row)
        s["skip_network_choice"] = self.skip_network_row.get_active()
        s["language"] = combo_value(self.language_row)
        s["check_updates"] = self.check_updates_row.get_active()
        s["fullscreen"] = self.fullscreen_row.get_active()
        s["present_mode"] = combo_value(self.present_row)
        s["hdr"] = self.hdr_row.get_active()
        s["fps_mode"] = combo_value(self.fps_row)
        s["fps_limit"] = int(self.limit_row.get_value())
        s["draw_pipe"] = combo_value(self.pipe_row)
        s["readbacks"] = combo_value(self.readbacks_row)
        s["mangohud"] = self.mangohud_row.get_active()
        s["frame_stats"] = self.stats_row.get_active()
        s["save_log"] = self.save_log_row.get_active()
        s["crash_diag"] = self.crash_diag_row.get_active()
        s["gpu_profile"] = self.profile_row.get_active()
        s["vk_validation"] = self.validation_row.get_active()
        s["extra_env"] = self.extra_row.get_text().strip()
        s["mods_enabled"] = self.mods_enabled_row.get_active()
        s["discord"] = self.discord_row.get_active()
        s["steam_overlay"] = self.steam_overlay_row.get_active()
        s["gestures_no_motion"] = self.gestures_row.get_active()
        s["trophy_key"] = self.trophy_key_row.get_text().strip()
        s["online"] = self.online_row.get_active()
        s.update(self.online_settings())
        s["atlas"] = self.atlas_row.get_active()
        s["atlas_travel"] = self.atlas_travel_row.get_active()
        s["atlas_items"] = self.atlas_items_row.get_active()
        s["coop_players"] = int(self.coop_players_row.get_value())
        s["coop_layout"] = combo_value(self.coop_layout_row)
        s["coop_controllers"] = [combo_value(row) for row in self.coop_pad_rows]
        s["coop_sound_first_only"] = self.coop_sound_row.get_active()
        s["coop_display"] = combo_value(self.coop_display_row)
        s["pad_deadzone"] = int(self.deadzone_row.get_value())
        s["pad_lightbar"] = self.lightbar_switch.get_active()
        rgba = self.lightbar_colour.get_rgba()
        s["pad_lightbar_colour"] = "#{:02x}{:02x}{:02x}".format(
            *(round(max(0.0, min(c, 1.0)) * 255) for c in (rgba.red, rgba.green, rgba.blue)))
        s["saves_auto_backup"] = self.auto_backup_row.get_active()
        s["saves_auto_backup_keep"] = int(self.auto_backup_keep_row.get_value())
        self.save_mod_profile()
        self.save_patch_profile()
        save_settings(s)
        # Issue #21: only what was changed here (since the page was built or last saved) is
        # written; every other key keeps the file's current value. The whole page used to be
        # written back, on Play and on closing the launcher, so a setting changed in the game's
        # menu or by hand while the launcher was open went back to the launcher's old value.
        rows = self.ini_rows()
        _values, lines = load_ini()
        present = {line.split("=", 1)[0].strip() for line in lines
                   if "=" in line and not line.lstrip().startswith("#")}
        changed = {key: value for key, value in rows.items()
                   if key not in present or self.ini_rows_seen.get(key) != value}
        changed.update(self.ini_controls_changed)
        save_ini(changed, lines)
        self.ini_rows_seen = rows
        self.ini_controls_changed = {}
        self.ini, self.ini_lines = load_ini()

    def ini_rows(self):
        """The bbport.ini values the launcher's rows show."""
        return {
            "upscaler": combo_value(self.upscaler_row),
            "preset": str(combo_value(self.preset_row)),
            "sharpen": "1" if self.sharpen_row.get_active() else "0",
            "sharpness": f"{self.sharpness_row.get_value():.2f}",
            "object_motion": "1" if self.motion_row.get_active() else "0",
            "show_fps": "1" if self.show_fps_row.get_active() else "0",
            "output_res": combo_value(self.output_row),
            "aspect_ratio": combo_value(self.aspect_row),
            "anti_aliasing": combo_value(self.aa_row),
            "texture_quality": combo_value(self.texture_row),
            "vbao": "1" if self.vbao_row.get_active() else "0",
            "model_lod": combo_value(self.lod_row),
            **frame_gen_ini(combo_value(self.frame_gen_row)),
            "low_latency": combo_value(self.low_latency_row),
            "fov": str(int(self.fov_row.get_value())),
            "mute_unfocused": "1" if self.mute_row.get_active() else "0",
            "game_text_language": combo_value(self.text_language_row),
            "game_voice_language": combo_value(self.voice_language_row),
            "button_prompts": combo_value(self.prompts_row),
            "mouse_look": "1" if self.mouse_look_row.get_active() else "0",
            "mouse_sensitivity": f"{self.mouse_sensitivity_row.get_value():.2f}",
            "mouse_invert_y": "1" if self.mouse_invert_row.get_active() else "0",
            "mouse_invert_x": "1" if self.mouse_invert_x_row.get_active() else "0",
            **{key: f"{row.get_value():.2f}" for key, row in self.camera_speed_rows.items()},
            "keyboard_layout": combo_value(self.keyboard_layout_row),
            "menu_pad_hold_ms": combo_value(self.menu_pad_row),
            **{key: "1" if row.get_active() else "0" for key, row in self.stick_rows.items()},
            **{key: "1" if row.get_active() else "0" for key, row in self.effect_rows.items()},
            **{key: "1" if row.get_active() else "0" for key, row in self.cheat_rows.items()},
            **{key: "1" if row.get_active() else "0" for key, row in self.streaming_rows.items()},
        }

    def environment(self):
        return game_environment(self.settings)

    # --- Steam ---------------------------------------------------------------------------

    def on_add_to_steam(self, _button):
        """Bloodborne in the Steam library: a non-Steam game that runs --play (no window)."""
        steam = bbport_steam.steam_folder()
        configs = bbport_steam.user_configs(steam) if steam else []
        flatpak = bool(steam) and bbport_steam.is_flatpak(steam)
        if not configs or not bbport_steam.steam_command(flatpak):
            self.alert("Steam", tr("Steam не найден (или в него ещё никто не входил)"))
            return
        self.store()  # --play starts the game with the saved settings
        if flatpak and not bbport_steam.flatpak_can_spawn():
            self.ask_flatpak_spawn(steam, configs)
            return
        self.close_steam_then_add(steam, configs)

    def ask_flatpak_spawn(self, steam, configs):
        """Flathub's Steam runs its games in its sandbox: the shortcut needs flatpak-spawn --host."""
        body = tr("Steam из Flatpak запускает игры в своей песочнице, где нет ни папки игры, ни драйверов: "
                  "ярлык должен запускать игру вне её (flatpak-spawn --host). Для этого Steam нужно право "
                  "org.freedesktop.Flatpak, с которым он может запускать программы в вашей системе. Выдать его?")
        if not hasattr(Adw, "AlertDialog"):
            self.alert("Steam", body)
            return
        dialog = Adw.AlertDialog(heading="Steam (Flatpak)", body=body)
        dialog.add_response("cancel", tr("Отмена"))
        dialog.add_response("allow", tr("Выдать право"))
        dialog.set_response_appearance("allow", Adw.ResponseAppearance.SUGGESTED)

        def on_response(_dialog, response):
            if response != "allow":
                return
            try:
                bbport_steam.allow_flatpak_spawn()
            except (OSError, subprocess.CalledProcessError) as error:
                detail = getattr(error, "stderr", "") or str(error)
                self.alert("Steam", tr("Не удалось выдать право Steam: {}").format(detail.strip()))
                return
            self.close_steam_then_add(steam, configs)
        dialog.connect("response", on_response)
        self.present_dialog(dialog)

    def close_steam_then_add(self, steam, configs):
        if not bbport_steam.steam_running():
            self.add_to_steam(steam, configs, restart=False)
            return
        if not hasattr(Adw, "AlertDialog"):
            self.alert("Steam", tr("Закройте Steam и нажмите «Добавить» ещё раз"))
            return
        dialog = Adw.AlertDialog(heading="Steam", body=tr(
            "Пока игра добавляется, Steam нужно закрыть; потом он запустится снова. Закрыть Steam?"))
        dialog.add_response("cancel", tr("Отмена"))
        dialog.add_response("close", tr("Закрыть Steam"))
        dialog.set_response_appearance("close", Adw.ResponseAppearance.SUGGESTED)

        def on_response(_dialog, response):
            if response == "close":
                bbport_steam.shutdown_steam(bbport_steam.is_flatpak(steam))
                self.wait_for_steam(steam, configs, tries=60)
        dialog.connect("response", on_response)
        self.present_dialog(dialog)

    def wait_for_steam(self, steam, configs, tries):
        """Polls until Steam has exited (it writes its files as it goes), then adds the game."""
        def poll():
            nonlocal tries
            if bbport_steam.steam_running():
                tries -= 1
                if tries == 0:
                    self.alert("Steam", tr("Steam не закрылся. Закройте его сами и попробуйте ещё раз"))
                    return False
                return True
            GLib.timeout_add(1000, lambda: self.add_to_steam(steam, configs, restart=True) and False)
            return False
        GLib.timeout_add(500, poll)

    def add_to_steam(self, steam, configs, restart):
        # Packaged: the AppImage itself; from a checkout: the launcher script.
        appimage = os.environ.get("APPIMAGE")
        target = appimage or str(PORT_DIR / "launcher" / "bb-launcher.sh")
        icon = PORT_DIR / "launcher" / "bloodborne.png"
        start_dir = str(PORT_DIR)
        if appimage:
            # PORT_DIR is the AppImage's mount, gone once it closes: the shortcut starts in the
            # AppImage's folder, with a copy of the icon in the data folder.
            start_dir = str(Path(appimage).parent)
            try:
                kept = DATA_DIR / "bloodborne.png"
                kept.write_bytes(icon.read_bytes())
                icon = kept
            except OSError:
                pass
        exe, start_dir, options = bbport_steam.shortcut_command(target, start_dir, "--play", steam)
        icon = str(icon)
        try:
            for config in configs:
                bbport_steam.add_shortcut(config / "shortcuts.vdf", "Bloodborne", exe,
                                          start_dir, icon, options)
        except (OSError, ValueError) as error:
            self.alert("Steam", tr("Не удалось добавить игру в Steam: {}").format(error))
            return
        if restart:
            bbport_steam.start_steam(bbport_steam.is_flatpak(steam))
        self.toasts.add_toast(Adw.Toast(title=tr("Bloodborne добавлен в библиотеку Steam"), timeout=6))

    # --- mods ----------------------------------------------------------------------------

    def mods_dir(self):
        return Path(self.settings.get("mods_dir") or DATA_DIR / "mods").expanduser()

    def save_mod_profile(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        rows = self.mod_list.rows
        profile = {"order": [name for name, _ in rows],
                   "disabled": [name for name, row in rows if not row.get_active()]}
        (DATA_DIR / "mods.json").write_text(json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def refresh_mods(self):
        self.mod_list.clear()
        self.mods_folder_row.set_subtitle(str(self.mods_dir()))
        try:
            profile = json.loads((DATA_DIR / "mods.json").read_text(encoding='utf-8'))
        except (OSError, ValueError):
            profile = {}
        available = discover_mods(self.mods_dir())
        order = list(dict.fromkeys(n for n in [*profile.get("order", []), *available] if n in available))
        for name in order:
            row = Adw.SwitchRow(title=name, active=name not in profile.get("disabled", []))
            row.add_suffix(flat_button("go-up-symbolic", tr("Загрузить раньше"),
                                        lambda _b, n=name: self.move_mod(n, -1)))
            row.add_suffix(flat_button("go-down-symbolic", tr("Загрузить позже"),
                                        lambda _b, n=name: self.move_mod(n, 1)))
            self.mod_list.add(name, row)
        if not order:
            self.mods_folder_row.set_subtitle(f"{self.mods_dir()} — {tr('Модов нет')}")
        # Folders that are not mods are named, with why, instead of left out without a word.
        for row in getattr(self, "mod_problem_rows", []):
            self.mod_list.group.remove(row)
        self.mod_problem_rows = []
        for name, problem in unrecognized_mods(self.mods_dir()):
            row = Adw.ActionRow(title=name, subtitle=f"{tr('Не загружен')}: {tr(MOD_PROBLEMS[problem])}")
            row.add_css_class("dim-label")
            self.mod_list.group.add(row)
            self.mod_problem_rows.append(row)

    def move_mod(self, name, direction):
        rows = self.mod_list.rows
        index = next(i for i, (n, _) in enumerate(rows) if n == name)
        target = index + direction
        if 0 <= target < len(rows):
            rows[index], rows[target] = rows[target], rows[index]
            self.save_mod_profile()
            self.refresh_mods()

    def on_refresh_mods(self, _button):
        self.save_mod_profile()
        self.refresh_mods()

    def on_choose_mods(self, _button):
        self.save_mod_profile()

        def chosen(path):
            self.settings["mods_dir"] = path
            self.refresh_mods()
            self.store()
        self.choose_folder(tr("Папка модов"), self.mods_dir(), chosen)

    # --- third-party patches -------------------------------------------------------------

    def save_patch_profile(self):
        """patches.json: the switches that differ from each file's isEnabled."""
        enabled, disabled = [], []
        for key, row in self.patch_list.rows:
            if row.get_active() != row.default:
                (enabled if row.get_active() else disabled).append(key)
        path = DATA_DIR / "patches.json"
        try:
            profile = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            profile = {}
        # Patches of files not listed now (another folder) keep their choice.
        shown = {key for key, _ in self.patch_list.rows}
        profile = {"enabled": sorted({k for k in profile.get("enabled", []) if k not in shown} | set(enabled)),
                   "disabled": sorted({k for k in profile.get("disabled", []) if k not in shown} | set(disabled))}
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def refresh_patches(self):
        self.patch_list.clear()
        directory = patches_dir(self.settings)
        try:
            profile = json.loads((DATA_DIR / "patches.json").read_text(encoding='utf-8'))
        except (OSError, ValueError):
            profile = {}
        found = external_patches(directory)
        for key, _path, meta in found:
            default = meta.get("isEnabled", "false").lower() == "true"
            active = key in profile.get("enabled", []) or (default and key not in profile.get("disabled", []))
            subtitle = key.split("/", 1)[0]
            if meta.get("Author"):
                subtitle += " · " + tr("Автор: {}").format(meta.get("Author"))
            row = Adw.SwitchRow(title=GLib.markup_escape_text(meta.get("Name") or key),
                                subtitle=GLib.markup_escape_text(subtitle), active=active)
            if meta.get("Note"):
                row.set_tooltip_text(meta.get("Note").replace("\\n", "\n"))
            row.default = default
            self.patch_list.add(key, row)
        self.patches_folder_row.set_subtitle(
            str(directory) if found else f"{directory} — {tr('Патчей нет')}")

    def on_refresh_patches(self, _button):
        self.save_patch_profile()
        self.refresh_patches()

    def on_choose_patches(self, _button):
        self.save_patch_profile()

        def chosen(path):
            self.settings["patches_dir"] = path
            self.refresh_patches()
            self.store()
        self.choose_folder(tr("Папка патчей"), patches_dir(self.settings), chosen)

    # --- log page ------------------------------------------------------------------------

    # --- online page ---------------------------------------------------------------------

    def build_online_page(self):
        s = self.settings
        self.online_page_built = False  # until its rows are all there (show_thd_account)
        page = Adw.PreferencesPage()
        # Its description says where what comes from on the chosen server (show_server_kind).
        self.play_group = play = Adw.PreferencesGroup()
        # Whether the account works, at a glance: the connection test, which signs in; its
        # results go just below.
        self.online_status_row = Adw.ActionRow(title=tr("Состояние"))
        self.online_status_icon = Gtk.Image()
        self.online_status_row.add_prefix(self.online_status_icon)
        self.test_button = Gtk.Button(label=tr("Проверить"), valign=Gtk.Align.CENTER)
        self.test_button.connect("clicked", self.on_test_connection)
        self.online_status_row.add_suffix(self.test_button)
        play.add(self.online_status_row)
        self.online_row = Adw.SwitchRow(title=tr("Играть онлайн"), active=s["online"])
        play.add(self.online_row)
        if online_module():
            self.online_row.connect("notify::active", lambda *_: self.show_online_switch())
            self.online_row.connect("notify::active", lambda row, _p: row.get_active()
                                    and self.settings.update(ask_online_off=True))
            self.show_online_switch()
        else:
            self.online_row.set_sensitive(False)
            self.online_row.set_subtitle(tr("Эта сборка без модуля онлайна (libbbnet20.so): игра только офлайн"))
        page.add(play)
        self.test_group = Adw.PreferencesGroup(title=tr("Проверка соединения"), visible=False)
        self.test_rows = []
        page.add(self.test_group)

        game = Adw.PreferencesGroup(title=tr("Игровой сервер (сообщения, пятна крови, призраки)"))
        self.community_row = Adw.EntryRow(title=tr("Игровой сервер"), text=s["online_community"])
        game.add(self.community_row)
        self.tombs_row = Adw.SwitchRow(
            title=tr("Пятна крови на Seamless Hunt"),
            subtitle=tr("Пятна крови и видения смерти этого сервера вызывают вылет «Transaction failed»: "
                        "без них игра не вылетает"),
            active=s["online_seamlesshunt_tombs"])
        game.add(self.tombs_row)
        self.game_group = game

        coop = Adw.PreferencesGroup(title=tr("Сервер кооператива (колокола и призывы)"))
        kinds = SERVER_KINDS + [THD_KIND]
        kind = online.server_kind(s)
        self.server_kind_row = combo_row(tr("Сервер shadNet"), None, kinds,
                                         kind if kind in (k[1] for k in kinds) else "seamlesshunt")
        coop.add(self.server_kind_row)
        # The address of an own server, also when it is the default's (0.7's default is Seamless
        # Hunt's, which the Linux fork's guide had players enter as their own server): left out,
        # the field showed empty and saving it lost the server.
        own = (s["online_server"] if kind == "own" or s["online_server"] != online.SHADNET_SERVER
               else "")
        self.server_row = Adw.EntryRow(title=tr("Адрес сервера (host:port)"), text=own)
        self.webapi_row = Adw.EntryRow(title=tr("Адрес WebAPI (пусто: порт 31315 сервера)"),
                                       text=s["online_webapi"])
        guide = Adw.ActionRow(title=tr("Как запустить свой сервер"), subtitle=SERVER_GUIDE_URL,
                              activatable=True)
        guide.add_suffix(Gtk.Image(icon_name="adw-external-link-symbolic"))
        guide.connect("activated", lambda _row: self.open_uri(SERVER_GUIDE_URL))
        for row in (self.server_row, self.webapi_row, guide):
            coop.add(row)
        self.own_server_rows = (self.server_row, self.webapi_row, guide)

        # Seamless co-op: BBSC (gpu/bbnet20/bbsc, CLS_AMG) in the game, on Seamless Hunt or an own
        # server with BBSC's game server.
        seamless = Adw.PreferencesGroup(
            title=tr("Бесшовный кооператив (BBSC)"),
            description=tr("Сессия переживает смерти, фонари, смену локаций, боссов и Сон "
                           "Охотника; до 5 охотников. BBSC от CLS_AMG. Он нужен всем игрокам "
                           "сессии"))
        self.bbsc_row = Adw.SwitchRow(
            title=tr("Включить BBSC"),
            subtitle=tr("Пока включено, колокола игры заменены колоколами BBSC; после выключения "
                        "прежние вернутся при следующей загрузке персонажа (сохранение копируется "
                        "в save-backups)"),
            active=bool(s.get("bbsc", True)))
        seamless.add(self.bbsc_row)
        # BBSC's own options (scripts/bbsc.py), folded away; kept only where the player changed them.
        self.bbsc_option_rows = {}
        if bbsc.options():
            options = Adw.ExpanderRow(title=tr("Настройки BBSC"),
                                      subtitle=tr("Применяются при запуске игры"))
            chosen = s.get("bbsc_options") or {}
            for option in bbsc.options():
                name, about = BBSC_OPTION_TEXTS.get(option["id"], (option.get("name", ""),
                                                                    option.get("description", "")))
                value = bbsc.value_of(option, chosen)
                if option["type"] == "bool":
                    row = Adw.SwitchRow(title=tr(name), subtitle=tr(about), active=value)
                elif option["type"] == "int":
                    row = Adw.SpinRow.new_with_range(option.get("min", 0), option.get("max", 1000), 5)
                    row.set_title(tr(name))
                    row.set_subtitle(tr(about))
                    row.set_value(value)
                else:
                    row = Adw.EntryRow(title=tr(name), text=value)
                    row.set_tooltip_text(tr(about))
                options.add_row(row)
                self.bbsc_option_rows[option["id"]] = (row, option)
            seamless.add(options)
            self.bbsc_row.bind_property("active", options, "sensitive",
                                        GObject.BindingFlags.SYNC_CREATE)
        self.bbsc_group = seamless

        # The Hunter's Dream: a Discord sign-in, as in bbhost (a code approved on the website).
        self.thd_group = Adw.PreferencesGroup(
            title=tr("Учётная запись The Hunter's Dream"),
            description=tr("Вход через Discord, как в bbhost: на сайте нужно подтвердить код. Пароль не "
                           "нужен, токен хранится на этом компьютере вместе с настройками лаунчера"))
        self.thd_server_row = Adw.EntryRow(title=tr("Адрес сервера"), text=s.get("thd_server", ""))
        self.thd_server_row.set_tooltip_text(online.HUNTERS_DREAM_SERVER)
        self.thd_group.add(self.thd_server_row)
        self.thd_account_row = Adw.ActionRow()
        self.thd_sign_button = Gtk.Button(valign=Gtk.Align.CENTER)
        self.thd_sign_button.connect("clicked", self.on_thd_sign)
        self.thd_account_row.add_suffix(self.thd_sign_button)
        self.thd_group.add(self.thd_account_row)
        self.thd_id, self.thd_token = s.get("thd_online_id", ""), s.get("thd_token", "")
        self.thd_signing = False
        self.thd_cancel = False
        self.show_thd_account()

        account = Adw.PreferencesGroup(
            title=tr("Учётная запись"),
            description=tr("Имя учётной записи shadNet, не email: создайте её кнопкой «Создать» "
                           "ниже или спросите владельца сервера. Пароль хранится на этом компьютере "
                           "вместе с настройками лаунчера"))
        self.account_kind = combo_value(self.server_kind_row)
        self.online_accounts = {kind: dict(zip(("npid", "password"), online.account(s, kind)))
                                for kind in ("public", "own", "seamlesshunt", "thd")}  # "public": kept, unused
        npid, password = online.account(s, self.account_kind)
        self.npid_row = Adw.EntryRow(title=tr("Online ID (NPID)"), text=npid)
        self.password_row = Adw.PasswordEntryRow(title=tr("Пароль"), text=password)
        account.add(self.npid_row)
        account.add(self.password_row)
        # A private server's account made from here, as Seamless Hunt's account tool does on Windows.
        self.register_row = Adw.ActionRow(title=tr("Создать учётную запись"),
                                          subtitle=tr("На этом сервере, с именем и паролем выше"))
        self.register_button = Gtk.Button(label=tr("Создать"), valign=Gtk.Align.CENTER)
        self.register_button.connect("clicked", self.on_register)
        self.register_row.add_suffix(self.register_button)
        account.add(self.register_row)
        self.server_kind_row.connect("notify::selected", lambda *_: self.swap_account())
        self.account_group = account

        connection = Adw.PreferencesGroup(
            title=tr("Соединение"),
            description=tr("У всех в сессии должны быть одна версия игры (1.09) и один сервер. "
                           "Читы меняют игру и для других игроков: выключайте их при совместной игре"))
        self.upnp_row = Adw.SwitchRow(title=tr("UPnP (открыть порт на роутере автоматически)"),
                                      subtitle=tr("Выключите при Tailscale или другом VPN"),
                                      active=s["online_upnp"])
        connection.add(self.upnp_row)
        self.p2p_port_row = Adw.SpinRow.new_with_range(0, 65535, 1)
        self.p2p_port_row.set_title(tr("Порт кооператива (UDP)"))
        self.p2p_port_row.set_subtitle(tr("0: порт по умолчанию, {}. Его открывают в брандмауэре или "
                                          "на роутере вручную").format(online.P2P_PORT))
        self.p2p_port_row.set_value(number(s["online_p2p_port"] or 0, 0, int, "settings.json",
                                           "online_p2p_port"))
        connection.add(self.p2p_port_row)
        # ufw and firewalld drop the peers' packets and, for UPnP, the router's answers: UPnP opens
        # the port on the router only.
        self.firewall_rows = []
        gateway = online.default_gateway()
        for firewall in online.active_firewalls():
            warning = Adw.ActionRow(title=tr("Включён брандмауэр: {}").format(firewall),
                                    subtitle_selectable=True)
            warning.add_prefix(Gtk.Image(icon_name="dialog-warning-symbolic"))
            self.firewall_rows.append((warning, firewall, gateway))
            connection.add(warning)
        self.p2p_port_row.connect("notify::value", lambda *_: self.show_firewall_rows())
        self.show_firewall_rows()
        self.connection_group = connection
        # In the order they are needed: which server, its address, the account on it, seamless
        # co-op, then the connection's details and the title's choice screen.
        for group in (coop, game, self.thd_group, account, seamless, connection, self.netchoice_group):
            page.add(group)
        self.server_kind_row.connect("notify::selected", lambda *_: self.show_server_kind())
        self.show_server_kind()
        self.last_login = getattr(self, "last_login", None)
        for row, signal in ((self.online_row, "notify::active"), (self.server_kind_row, "notify::selected"),
                            (self.npid_row, "changed"), (self.password_row, "changed"),
                            (self.server_row, "changed"), (self.thd_server_row, "changed")):
            row.connect(signal, lambda *_: self.show_online_status())
        self.online_page_built = True
        self.show_online_status()
        # Saved with shadPS4's public server, gone from the choice: said once, as the next save
        # stores Seamless Hunt.
        if s["online"] and online.stored_kind(s) == "public":
            self.toasts.add_toast(Adw.Toast(title=tr("Публичный сервер shadPS4 больше не принимает "
                                                     "bbport: выбран Seamless Hunt"), timeout=8))
        return page

    def show_online_switch(self):
        self.online_row.set_subtitle(tr("Включено: игра входит на сервер при запуске") if self.online_row.get_active()
                                     else tr("Выключено: игра только офлайн"))

    def show_online_status(self):
        """The Online tab's first row: off, no account, an account not checked yet, or the last
        connection test's sign-in with this account on this server."""
        thd = combo_value(self.server_kind_row) == "thd"
        npid = self.thd_id if thd else self.npid_row.get_text().strip()
        item = self.server_kind_row.get_selected_item()
        server = item.get_string() if item is not None else ""
        missing = self.own_server_missing()
        server_address = None if missing else online.addresses(self.online_settings())[0]
        checked = self.last_login if self.last_login and self.last_login[:4] == (
            npid, combo_value(self.server_kind_row), self.password_row.get_text(), server_address) else None
        if not online_module():
            icon, text = "network-offline-symbolic", tr("Эта сборка без модуля онлайна (libbbnet20.so): игра только офлайн")
        elif not self.online_row.get_active():
            icon, text = "network-offline-symbolic", tr("Игра по сети выключена")
        elif self.own_server_missing():
            icon, text = "dialog-warning-symbolic", tr("Введите адрес своего сервера или выберите Seamless Hunt")
        elif thd and not (self.thd_id and self.thd_token):
            icon, text = "dialog-warning-symbolic", tr("Вход не выполнен: войдите через Discord ниже")
        elif thd:
            icon, text = "object-select-symbolic", tr("Вы вошли как {}").format(npid)
        elif not npid:
            icon, text = "dialog-warning-symbolic", tr("Нет учётной записи: создайте её или введите свою ниже")
        elif checked and checked[4]:
            icon, text = "object-select-symbolic", tr("Вход выполнен: «{}» на {}").format(npid, server)
        elif checked:
            icon, text = "dialog-warning-symbolic", tr("Не удалось войти: {}").format(checked[5])
        else:
            icon, text = "network-idle-symbolic", tr("Учётная запись «{}» на {}: нажмите «Проверить», "
                                                     "чтобы войти").format(npid, server)
        self.online_status_icon.set_from_icon_name(icon)
        self.online_status_row.set_subtitle(GLib.markup_escape_text(text))
        self.test_button.set_sensitive(online_module() and "test" not in self.working and not missing)
        self.register_button.set_sensitive("register" not in self.working and not missing)

    def own_server_missing(self):
        return combo_value(self.server_kind_row) == "own" and not self.server_row.get_text().strip()

    def bbsc_options_changed(self):
        """BBSC's options that differ from their defaults (scripts/bbsc.py)."""
        changed = {}
        for key, (row, option) in self.bbsc_option_rows.items():
            if option["type"] == "bool":
                value = row.get_active()
            elif option["type"] == "int":
                value = int(row.get_value())
            else:
                value = row.get_text().strip()
            if value != option.get("default"):
                changed[key] = value
        return changed

    def online_settings(self):
        """The Online page's settings (the keys of DEFAULTS)."""
        return {
            "online_community": self.community_row.get_text().strip(),
            "online_server_kind": combo_value(self.server_kind_row),
            "online_server": self.server_row.get_text().strip(),
            "online_webapi": self.webapi_row.get_text().strip(),
            "online_npid": self.npid_row.get_text().strip(),
            "online_password": self.password_row.get_text(),
            "online_upnp": self.upnp_row.get_active(),
            "online_seamlesshunt_tombs": self.tombs_row.get_active(),
            "online_p2p_port": int(self.p2p_port_row.get_value()),
            "online_seamless": self.settings.get("online_seamless", False),
            "online_accounts": self.kept_accounts(),
            "bbsc": self.bbsc_row.get_active(),
            "bbsc_options": self.bbsc_options_changed(),
            "thd_server": self.thd_server_row.get_text().strip(),
            "thd_online_id": self.thd_id,
            "thd_token": self.thd_token,
        }

    def kept_accounts(self):
        self.keep_account()
        return {kind: dict(kept) for kind, kept in self.online_accounts.items()}

    def keep_account(self):
        """The account typed in, as the one of the server chosen in the page."""
        self.online_accounts[self.account_kind] = {"npid": self.npid_row.get_text().strip(),
                                                   "password": self.password_row.get_text()}

    def swap_account(self):
        """Another kind of server chosen: its own account in the fields, the other one kept."""
        kind = combo_value(self.server_kind_row)
        if kind == self.account_kind:
            return
        self.keep_account()
        self.account_kind = kind
        kept = self.online_accounts.get(kind, {})
        self.npid_row.set_text(kept.get("npid", ""))
        self.password_row.set_text(kept.get("password", ""))

    def show_server_kind(self):
        kind = combo_value(self.server_kind_row)
        for row in self.own_server_rows:
            row.set_visible(kind == "own")
        # Seamless Hunt: its game server comes with the choice, and accounts are made from here.
        # The Hunter's Dream's game server comes with it too: only an own server's is typed.
        self.community_row.set_visible(kind == "own")
        self.tombs_row.set_visible(kind == "seamlesshunt")
        self.game_group.set_visible(kind in ("own", "seamlesshunt"))
        self.bbsc_group.set_visible(kind != "thd")  # The Hunter's Dream has no BBSC
        self.play_group.set_description({
            "seamlesshunt": tr("Seamless Hunt даёт всё: сообщения, пятна крови, призраков, колокола и "
                               "призывы. С игроками на Windows: нужны версия игры 1.09 и тот же сервер"),
            "thd": tr("Всё идёт через The Hunter's Dream: сообщения, пятна крови, призраки и "
                      "кооператив с игроками bbhost"),
        }.get(kind, tr("Сообщения, пятна крови и призраки приходят с игрового сервера ниже; колокола "
                       "и призывы идут через ваш сервер shadNet. Нужны версия игры 1.09 и тот же сервер")))
        # Another server: the last test's results were for the one before.
        for row in self.test_rows:
            self.test_group.remove(row)
        self.test_rows = []
        self.test_group.set_visible(False)
        self.register_row.set_visible(kind in ("own", "seamlesshunt"))
        # The Hunter's Dream: its own account (the Discord sign-in), no shadNet one.
        thd = kind == "thd"
        self.thd_group.set_visible(thd)
        self.account_group.set_visible(not thd)

    def show_thd_account(self):
        link = getattr(self, "thd_link", None)
        if link is not None:
            self.thd_account_row.remove(link)
            self.thd_link = None
        if self.thd_id and self.thd_token:
            self.thd_account_row.set_title(tr("Вы вошли как {}").format(GLib.markup_escape_text(self.thd_id)))
            self.thd_account_row.set_subtitle("")
            self.thd_sign_button.set_label(tr("Выйти"))
        else:
            self.thd_account_row.set_title(tr("Вход не выполнен"))
            self.thd_account_row.set_subtitle(tr("Нужен аккаунт Discord, привязанный к The Hunter's Dream"))
            self.thd_sign_button.set_label(tr("Войти через Discord"))
        if self.thd_signing:
            self.thd_sign_button.set_label(tr("Отмена"))
        self.thd_sign_button.set_sensitive(True)
        if self.online_page_built:
            self.show_online_status()

    def on_thd_sign(self, _button):
        """online.thd_sign_in: a code to approve on The Hunter's Dream's page, then its account."""
        if self.thd_signing:
            self.thd_cancel = True  # the waiting thread stops; done() resets the row
            return
        self.thd_cancel = False
        if self.thd_id and self.thd_token:
            self.thd_id = self.thd_token = ""
            self.store()
            self.show_thd_account()
            return
        self.thd_signing = True
        self.working.add("discord")
        self.show_thd_account()
        server = self.thd_server_row.get_text().strip()

        def show_code(page, code):
            def show():
                self.thd_account_row.set_title(tr("Код входа: {}").format(code))
                self.thd_account_row.set_subtitle(GLib.markup_escape_text(tr(
                    "На странице {}: 1) нажмите «Sign in with Discord to link» и войдите; "
                    "2) вернувшись на страницу, введите код в поле кода (не в «Sign in with a code from the game»). "
                    "Код скопирован в буфер").format(page)))
                try:
                    self.thd_account_row.get_clipboard().set(code)
                except Exception:
                    pass
                link = Gtk.LinkButton(uri=page, label=tr("Открыть страницу"), valign=Gtk.Align.CENTER)
                self.thd_account_row.add_prefix(link)
                self.thd_link = link
                self.open_uri(page)
                return False
            GLib.idle_add(show)

        def done(name, token, error):
            self.thd_signing = False
            self.work_done("discord")
            if error:
                self.show_thd_account()
                if error != "cancelled":
                    self.thd_account_row.set_subtitle(GLib.markup_escape_text(error))
            else:
                self.thd_id, self.thd_token = name, token
                self.store()
                self.show_thd_account()
                self.toasts.add_toast(Adw.Toast(title=tr("Вход выполнен: {}").format(name)))
            return False

        def work():
            try:
                name, token = online.thd_sign_in(server, show_code, device="bbport on Linux",
                                                 cancelled=lambda: self.thd_cancel)
            except ValueError as error:
                GLib.idle_add(done, "", "", str(error))
                return
            GLib.idle_add(done, name, token, "")
        threading.Thread(target=work, daemon=True).start()

    def show_firewall_rows(self):
        port = int(self.p2p_port_row.get_value())
        for row, firewall, gateway in self.firewall_rows:
            port_rule, router_rule = online.firewall_commands(firewall, gateway, port or online.P2P_PORT)
            lines = [tr("UPnP открывает порт только на роутере; брандмауэр этого компьютера всё "
                        "равно блокирует кооператив. Откройте порт: {}").format(port_rule)]
            if router_rule:
                lines.append(tr("Для UPnP нужны ответы роутера: {}").format(router_rule))
            row.set_subtitle(GLib.markup_escape_text("\n".join(lines)))

    def on_test_connection(self, _button):
        if self.own_server_missing():
            self.toasts.add_toast(Adw.Toast(title=tr("Введите адрес своего сервера или выберите Seamless Hunt")))
            return
        server, webapi, community = online.addresses(self.online_settings())
        names = {"game": tr("Игровой сервер"), "shadnet": tr("Сервер shadNet"),
                 "service": tr("Сервис кооператива"),
                 "stun": tr("UDP сервера shadNet (призывы)"), "webapi": "WebAPI",
                 "login": tr("Вход в shadNet")}
        login_errors = {"wrong name or password": tr("неверное имя или пароль"),
                        "no such account": tr("такой учётной записи нет на этом сервере"),
                        "already signed in": tr("эта учётная запись уже в сети (игра запущена?)")}
        account = (self.npid_row.get_text().strip(), self.password_row.get_text())
        for row in self.test_rows:
            self.test_group.remove(row)
        self.test_rows = []
        self.test_button.set_sensitive(False)
        self.test_button.set_label(tr("Проверка…"))
        kind = combo_value(self.server_kind_row)
        thd_server = self.thd_server_row.get_text().strip()
        self.working.add("test")

        def show(results):
            for name, address, ok, detail in results:
                if name == "stun" and ok:
                    status = tr("отвечает; ваш публичный адрес: {}").format(detail)
                elif name == "stun" and detail == "timeout":
                    status = tr("не отвечает: призывы не соединятся")
                elif name == "login":
                    status = tr("вход выполнен") if ok else login_errors.get(
                        detail, tr("вход не удался ({})").format(detail))
                    self.last_login = (account[0], kind, account[1], server, ok, status)
                else:
                    status = tr("доступен") if ok else f'{tr("недоступен")} ({detail})'
                # Plain text: an error such as "<urlopen error ...>" is not Pango markup.
                row = Adw.ActionRow(title=GLib.markup_escape_text(f"{names[name]}: {address}"),
                                    subtitle=GLib.markup_escape_text(status))
                row.add_prefix(Gtk.Image(icon_name="object-select-symbolic" if ok else "dialog-error-symbolic"))
                self.test_group.add(row)
                self.test_rows.append(row)
            self.test_group.set_visible(bool(self.test_rows))
            self.work_done("test")
            self.test_button.set_label(tr("Проверить"))
            self.show_online_status()
            return False

        def work():
            # The Hunter's Dream: its game server and its co-op service (the sign-in is Discord's).
            results = (online.check_thd(thd_server)
                       if kind == "thd"
                       else online.check(server, webapi, community, account))
            GLib.idle_add(show, results)
        threading.Thread(target=work, daemon=True).start()

    def on_register(self, _button):
        if self.own_server_missing():
            self.toasts.add_toast(Adw.Toast(title=tr("Введите адрес своего сервера или выберите Seamless Hunt")))
            return
        server = online.addresses(self.online_settings())[0]
        npid, password = self.npid_row.get_text().strip(), self.password_row.get_text()
        if not npid or not password:
            self.toasts.add_toast(Adw.Toast(title=tr("Введите имя и пароль выше")))
            return
        host, _sep, port = server.rpartition(":")
        errors = {"the name is taken": tr("это имя уже занято"),
                  "the server needs its registration key": tr("серверу нужен ключ регистрации: "
                                                              "спросите его владельца"),
                  "invalid name, password or email": tr("недопустимое имя или пароль")}
        self.register_button.set_sensitive(False)
        self.working.add("register")

        def done(ok, detail):
            self.work_done("register")
            self.show_online_status()  # Create back on, unless the own server has no address
            message = (tr("Учётная запись «{}» создана на {}").format(npid, host) if ok else
                       tr("Не удалось создать учётную запись: {}").format(errors.get(detail, detail)))
            self.toasts.add_toast(Adw.Toast(title=GLib.markup_escape_text(message), timeout=6))
            if ok:
                self.store()
            return False

        def work():
            try:
                result = online.shadnet_register(host, int(port), npid, password)
            except (OSError, ValueError) as error:
                result = (False, str(error))
            GLib.idle_add(done, *result)
        threading.Thread(target=work, daemon=True).start()

    # --- about page ----------------------------------------------------------------------

    def build_about_page(self):
        page = Adw.PreferencesPage()
        about = Adw.PreferencesGroup()  # the section's title already says it
        app = Adw.ActionRow(title="bbport Linux",
                            subtitle=tr("Версия {}").format(bbport_update.VERSION_TEXT))
        app.add_prefix(Gtk.Image(file=str(PORT_DIR / "launcher" / "bloodborne.png"), pixel_size=48))
        about.add(app)
        def link_row(title, subtitle, url, icon):
            row = Adw.ActionRow(title=title, subtitle=subtitle, activatable=True)
            row.add_prefix(themed_icon(icon))
            row.add_suffix(Gtk.Image(icon_name="adw-external-link-symbolic"))
            row.connect("activated", lambda _row, link=url: self.open_uri(link))
            return row

        about.add(link_row(tr("Этот проект"), bbport_update.REPOSITORY_URL,
                           bbport_update.REPOSITORY_URL, "github-symbolic"))
        about.add(link_row(tr("Руководство для игроков"), bbport_update.GUIDE_URL,
                           bbport_update.GUIDE_URL, "help-browser-symbolic"))
        support = Adw.ActionRow(title=tr("Поддержать проект"), subtitle="ko-fi.com/ayozetr",
                                activatable=True)
        support.add_prefix(Gtk.Image(icon_name="emblem-favorite-symbolic"))
        support.add_suffix(Gtk.Image(icon_name="adw-external-link-symbolic"))
        support.connect("activated", lambda _row: self.open_uri(bbport_update.KOFI_URL))
        about.add(support)
        about.add(link_row(tr("Лицензия"), tr("GNU GPL v3 или новее · Файлы игры не входят."),
                           bbport_update.LICENSE_URL, "application-certificate-symbolic"))
        thanks = Adw.ActionRow(title=tr("Благодарности"), subtitle=tr("Без них ничего этого не было бы"),
                               activatable=True)
        thanks.add_prefix(Gtk.Image(icon_name="system-users-symbolic"))
        thanks.add_suffix(Gtk.Image(icon_name="go-next-symbolic"))
        thanks.connect("activated", lambda _row: self.show_thanks())
        about.add(thanks)
        projects = Adw.ExpanderRow(title=tr("Проекты, на которых он основан"))
        projects.add_prefix(themed_icon("github-symbolic"))
        projects.add_row(link_row(tr("Основано на bbport от deadinside28"), bbport_update.UPSTREAM_URL,
                                  bbport_update.UPSTREAM_URL, "github-symbolic"))
        projects.add_row(link_row(tr("Порт для Windows от Supermedo"), bbport_update.WINDOWS_URL,
                                  bbport_update.WINDOWS_URL, "github-symbolic"))
        # Its NOTICE asks for this attribution, as written, in the about screen.
        projects.add_row(link_row("Lantern Engine by Awaken", LANTERN_ENGINE_URL, LANTERN_ENGINE_URL,
                                  "github-symbolic"))
        about.add(projects)
        page.add(about)

        updates = Adw.PreferencesGroup(title=tr("Обновления"))
        self.check_updates_row = Adw.SwitchRow(
            title=tr("Проверять обновления при запуске"),
            subtitle=tr("Спрашивает GitHub о последнем выпуске; ничего не скачивается без вашего "
                        "согласия"),
            active=self.settings.get("check_updates", True))
        self.check_updates_row.add_prefix(Gtk.Image(icon_name="emblem-synchronizing-symbolic"))
        self.check_updates_row.connect("notify::active", lambda *_: self.store())
        updates.add(self.check_updates_row)
        self.update_row = Adw.ActionRow(title=tr("Последняя версия"))
        self.update_row.add_prefix(Gtk.Image(icon_name="software-update-available-symbolic"))
        self.update_button = Gtk.Button(valign=Gtk.Align.CENTER)
        self.update_button.connect("clicked", self.on_update_button)
        self.update_row.add_suffix(self.update_button)
        updates.add(self.update_row)
        # Another released version, an older one too (back to one that worked better).
        self.version_row = readable_choice(Adw.ComboRow(
            title=tr("Другая версия"),
            subtitle=tr("Например, предыдущая, если новая работает хуже. Настройки и сохранения не "
                        "затрагиваются"),
            model=Gtk.StringList.new([tr("Список появится после проверки обновлений")])))
        self.version_row.add_prefix(Gtk.Image(icon_name="document-open-recent-symbolic"))
        self.version_button = Gtk.Button(label=tr("Установить"), valign=Gtk.Align.CENTER)
        self.version_button.connect("clicked", self.on_install_version)
        self.version_row.add_suffix(self.version_button)
        self.version_row.connect("notify::selected", lambda *_: self.show_update_state())
        updates.add(self.version_row)
        # What changed in the version installed: its release notes on GitHub.
        notes_url = f"{bbport_update.REPOSITORY_URL}/releases/tag/{bbport_update.VERSION}"
        notes = Adw.ActionRow(title=tr("Что нового в этой версии"),
                              subtitle=tr("Изменения версии {} на GitHub").format(bbport_update.VERSION),
                              activatable=True)
        notes.add_prefix(Gtk.Image(icon_name="text-x-generic-symbolic"))
        notes.add_suffix(Gtk.Image(icon_name="adw-external-link-symbolic"))
        notes.connect("activated", lambda _row: self.open_uri(notes_url))
        updates.add(notes)
        page.add(updates)
        # The game's owners, under everything, as plain text.
        owners = Adw.PreferencesGroup()
        owners.add(Gtk.Label(label=tr("Bloodborne принадлежит Sony Interactive Entertainment и "
                                      "FromSoftware."),
                             wrap=True, justify=Gtk.Justification.CENTER,
                             css_classes=["dim-label", "caption"]))
        page.add(owners)
        return page

    def present_dialog(self, dialog):
        """Shows an Adw dialog. With the cairo renderer (kept: GTK's GPU renderers cut the top of
        capitals at fractional scales), each frame of a dialog's animation redraws the whole window
        on the CPU, some 50 ms: 20 frames a second, a stutter. So it opens and closes without
        it; animations come back once it is gone ("closed" comes as it starts closing, "unmap"
        once it is off the window)."""
        settings = Gtk.Settings.get_default()
        if os.environ.get("GSK_RENDERER") == "cairo" and settings.get_property("gtk-enable-animations"):
            settings.set_property("gtk-enable-animations", False)

            def gone(_dialog):
                dialog.disconnect(handler)
                GLib.timeout_add(300, lambda: settings.set_property("gtk-enable-animations", True) and False)
            handler = dialog.connect("unmap", gone)
        dialog.present(self)

    def show_thanks(self):
        """Everyone whose work is in this fork or who helped it: their GitHub profile on a click
        (the dialog is made once: thanks_dialog)."""
        self.present_dialog(self.thanks_dialog())

    def thanks_dialog(self):
        """The thanks dialog, made the first time it is needed or while the window is idle (some
        60 rows: 40 ms), and again after a language change (build)."""
        if getattr(self, "thanks", None) is not None:
            return self.thanks
        page = Adw.PreferencesPage()
        for title, people in THANKS:
            group = Adw.PreferencesGroup(title=tr(title))
            for name, what, url in people:
                row = Adw.ActionRow(title=GLib.markup_escape_text(name), subtitle=tr(what),
                                    activatable=True)
                row.add_suffix(Gtk.Image(icon_name="adw-external-link-symbolic"))
                row.connect("activated", lambda _row, link=url: self.open_uri(link))
                group.add(row)
            page.add(group)
        page.set_description(tr("Без них ничего этого не было бы"))
        self.thanks = Adw.PreferencesDialog(title=tr("Благодарности"))
        self.thanks.add(page)
        return self.thanks

    def open_uri(self, uri):
        Gtk.UriLauncher.new(uri).launch(self, None, None, None)

    def show_update_state(self, progress=None):
        """The update row and its button for the current state."""
        latest, state = self.latest, self.update_state
        newer = isinstance(latest, dict) and bbport_update.is_newer(latest["tag"])
        appimage = bbport_update.running_appimage()
        button, sensitive = tr("Проверить сейчас"), True
        if state == "checking":
            subtitle, sensitive = tr("Проверка…"), False
        elif state == "downloading":
            subtitle, button, sensitive = progress or tr("Загрузка…"), tr("Обновить"), False
        elif state == "installed":
            subtitle, button = tr("Версия {} установлена: перезапустите лаунчер").format(
                self.installing["tag"]), tr("Перезапустить")
        elif isinstance(latest, str):
            subtitle = tr("Не удалось проверить: {}").format(latest)
        elif latest is None:
            subtitle = tr("Установлена версия {}").format(bbport_update.VERSION)
        elif not newer:
            subtitle = tr("Установлена последняя версия ({})").format(bbport_update.VERSION)
        elif appimage and latest["appimage"]:
            subtitle, button = tr("Доступна версия {} (установлена {})").format(
                latest["tag"], bbport_update.VERSION), tr("Обновить")
        else:
            subtitle, button = tr("Доступна версия {} (установлена {})").format(
                latest["tag"], bbport_update.VERSION), tr("Открыть страницу")
        self.update_row.set_subtitle(subtitle)
        self.update_button.set_label(button)
        self.update_button.set_sensitive(sensitive)
        self.update_button.remove_css_class("suggested-action")
        if button in (tr("Обновить"), tr("Перезапустить")):
            self.update_button.add_css_class("suggested-action")
        chosen = self.chosen_version()
        self.version_row.set_sensitive(bool(self.releases))
        self.version_button.set_sensitive(
            chosen is not None and chosen["tag"] != bbport_update.VERSION and state == "idle")

    def show_versions(self):
        """The version selector's choices: every installable release, the running one marked."""
        labels = [tr("{} (установлена)").format(r["tag"]) if r["tag"] == bbport_update.VERSION
                  else f"{r['tag']} · {r['date']}" for r in self.releases]
        self.version_row.set_model(Gtk.StringList.new(
            labels or [tr("Список появится после проверки обновлений")]))
        current = next((i for i, r in enumerate(self.releases)
                        if r["tag"] == bbport_update.VERSION), 0)
        self.version_row.set_selected(current)
        self.show_update_state()

    def chosen_version(self):
        index = self.version_row.get_selected()
        return self.releases[index] if self.releases and 0 <= index < len(self.releases) else None

    def on_install_version(self, _button):
        release = self.chosen_version()
        if release is None or release["tag"] == bbport_update.VERSION:
            return
        if not bbport_update.running_appimage():
            self.open_uri(release["url"])  # a git checkout: the release page
            return
        older = not bbport_update.is_newer(release["tag"])
        dialog = Adw.AlertDialog(
            heading=tr("Установить версию {}?").format(release["tag"]),
            body=(tr("Это более старая версия, чем установленная ({}). Вернуться можно тем же "
                     "списком или кнопкой «Обновить». Настройки и сохранения не затрагиваются")
                  if older else tr("Установлена версия {}. Настройки и сохранения не затрагиваются"))
            .format(bbport_update.VERSION))
        dialog.add_response("cancel", tr("Отмена"))
        dialog.add_response("install", tr("Установить"))
        dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", lambda _d, response:
                       response == "install" and self.install_update(release))
        self.present_dialog(dialog)

    def on_update_button(self, _button):
        latest = self.latest
        if self.update_state == "installed":
            self.restart_launcher()
        elif isinstance(latest, dict) and bbport_update.is_newer(latest["tag"]):
            if bbport_update.running_appimage() and latest["appimage"]:
                self.install_update(latest)
            else:
                self.open_uri(latest["url"])
        else:
            self.on_check_update(None)

    def on_check_update(self, _button, quiet=False):
        self.update_state = "checking"
        self.show_update_state()

        def done(result, releases):
            self.latest, self.update_state = result, "idle"
            if releases is not None:
                self.releases = releases
            self.show_versions()
            if quiet and isinstance(result, dict) and bbport_update.is_newer(result["tag"]):
                toast = Adw.Toast(title=tr("Доступна версия {}").format(result["tag"]),
                                  button_label=tr("Подробнее"), timeout=8)
                toast.connect("button-clicked", lambda *_: self.show_section("about"))
                self.toasts.add_toast(toast)
            return False

        def work():
            # A connection that is not up yet when the launcher opens (the name does not resolve,
            # no route) gets a second try a few seconds later, and a plain message.
            for attempt in (1, 2):
                try:
                    result = bbport_update.latest_release()
                    break
                except (OSError, ValueError) as error:
                    reason = getattr(error, "reason", None) or error
                    if isinstance(reason, (socket.gaierror, ConnectionError, TimeoutError)):
                        result = tr("нет связи с GitHub, проверьте подключение к интернету")
                        if attempt == 1:
                            time.sleep(5)
                            continue
                    else:
                        result = str(reason)
                    break
            try:
                releases = bbport_update.releases()
            except (OSError, ValueError):
                releases = None  # the selector keeps what it had
            GLib.idle_add(done, result, releases)
        threading.Thread(target=work, daemon=True).start()

    def install_update(self, release):
        """Downloads release's AppImage over the running one (bbport_update.install)."""
        target = bbport_update.running_appimage()
        self.installing = release
        self.update_state = "downloading"
        self.show_update_state()

        def progress(done, total):
            text = tr("Загрузка… {} %").format(done * 100 // total) if total else \
                tr("Загрузка… {} МБ").format(done >> 20)
            GLib.idle_add(self.show_update_state, text)

        def finished(error):
            self.update_state = "idle" if error else "installed"
            self.show_update_state()
            if error:
                self.toasts.add_toast(Adw.Toast(title=tr("Не удалось обновить: {}").format(error)))
            return False

        def work():
            try:
                bbport_update.install(release["appimage"], target, progress)
                error = None
            except OSError as failure:
                error = str(getattr(failure, "reason", None) or failure)
            GLib.idle_add(finished, error)
        threading.Thread(target=work, daemon=True).start()

    def restart_launcher(self):
        if self.process is not None:
            self.toasts.add_toast(Adw.Toast(title=tr("Сначала закройте игру")))
            return
        target = bbport_update.running_appimage()
        env = {k: v for k, v in os.environ.items()
               if k not in ("APPDIR", "APPIMAGE", "ARGV0", "OWD", "LD_LIBRARY_PATH", "PYTHONHOME",
                            "PYTHONPATH")}
        # The new launcher starts once this one has exited: with the same application ID while
        # this one runs, it would only raise this window and quit.
        subprocess.Popen(["sh", "-c", 'while kill -0 "$1" 2>/dev/null; do sleep 0.2; done; exec "$2"',
                          "sh", str(os.getpid()), str(target)], env=env, start_new_session=True)
        self.close()  # on_close saves the settings

    # --- trophies page -------------------------------------------------------------------

    def build_trophies_page(self):
        page = Adw.PreferencesPage()
        key = Adw.PreferencesGroup(title=tr("Ключ трофеев"), description=tr(
            "Ключ трофеев PS4 (TrophyKey в shadPS4), 32 шестнадцатеричных символа: с ним названия и "
            "описания на языке игры. Хранится на этом компьютере. Без него они на английском"))
        self.trophy_key_row = Adw.PasswordEntryRow(title=tr("Ключ трофеев"),
                                                   text=self.settings.get("trophy_key", ""),
                                                   show_apply_button=True)
        self.trophy_key_row.connect("apply", lambda _row: (self.store(), self.refresh_trophies()))
        key.add(self.trophy_key_row)
        page.add(key)
        self.trophy_group = Adw.PreferencesGroup(title=tr("Трофеи"), description=tr(
            "Записываются, когда игра их открывает, и показываются в игре"))
        # The ⋮ menu marks trophies earned on a PS4 (a save carried over): a check per trophy,
        # written on Save.
        action = Gio.SimpleAction.new("trophy-edit", None)
        action.connect("activate", lambda *_: self.edit_trophies(True))
        self.add_action(action)
        menu = Gio.Menu()
        menu.append(tr("Отметить трофеи"), "win.trophy-edit")
        self.trophy_menu = Gtk.MenuButton(icon_name="view-more-symbolic", menu_model=menu,
                                          tooltip_text=tr("Действия с трофеями"),
                                          halign=Gtk.Align.END, valign=Gtk.Align.CENTER, css_classes=["flat"],
                                          sensitive=False)
        cancel = Gtk.Button(label=tr("Отмена"))
        cancel.connect("clicked", lambda _b: self.edit_trophies(False))
        save = Gtk.Button(label=tr("Сохранить"), css_classes=["suggested-action"])
        save.connect("clicked", self.on_trophies_save)
        editing = Gtk.Box(spacing=6, valign=Gtk.Align.CENTER)
        editing.append(cancel)
        editing.append(save)
        self.trophy_header = Gtk.Stack(hhomogeneous=False, vhomogeneous=False, halign=Gtk.Align.END,
                                       valign=Gtk.Align.CENTER)
        self.trophy_header.add_named(self.trophy_menu, "menu")
        self.trophy_header.add_named(editing, "editing")
        self.trophy_group.set_header_suffix(self.trophy_header)
        page.add(self.trophy_group)
        self.trophy_rows = []
        self.trophy_checks = {}
        self.trophy_editing = False
        self.trophy_shown = (None, None)
        self.trophy_seen = None  # a new page shows its list on the first visit
        return page

    def refresh_trophies(self):
        game = Path(self.settings.get("game_dir") or "").expanduser()
        user = self.user_dir()
        key = trophies.parse_key(self.trophy_key_row.get_text())
        language = number(self.settings.get("language") or system_game_language(),
                          system_game_language(), int, "settings.json", "language")

        # Each visit refreshes: only the latest one shows.
        self.trophy_generation = getattr(self, "trophy_generation", 0) + 1
        generation = self.trophy_generation

        def state(directory):
            # The list, the earned ones and the marks are in these files.
            if directory is None:
                return None
            return tuple((Path(directory) / name).stat().st_mtime_ns
                         if (Path(directory) / name).exists() else None
                         for name in ("trophies.tsv", "earned.tsv"))

        def show(directory, problem):
            # Not over trophies being marked: their checks would go. Nor again when nothing has
            # changed since the last visit (some 40 rows and icons).
            if generation == self.trophy_generation and not self.trophy_editing:
                seen = (directory, problem, state(directory))
                if seen != getattr(self, "trophy_seen", None):
                    self.trophy_seen = seen
                    self.trophy_shown = (directory, problem)
                    self.show_trophies()
            return False

        def work():
            problem = None
            try:
                try:
                    directory = trophies.prepare(game, user, key, language)
                except trophies.NotTrophyFile:  # the dump's file, not the key (issue #22)
                    directory = None
                    problem = tr("Файл трофеев дампа повреждён или зашифрован (sce_sys/trophy/trophy00.trp): "
                                 "сделайте дамп заново")
                except (ValueError, trophies.ET.ParseError):  # what a wrong key gives
                    problem = tr("Неверный ключ трофеев: названия недоступны")
                    try:
                        directory = trophies.prepare(game, user, None, language)
                    except (OSError, ValueError, trophies.ET.ParseError):
                        directory = None
            except Exception as error:  # the list still shows, with the error, not nothing
                directory, problem = None, str(error)
            if directory is None and problem is None:  # which file the dump lacks (issue #22)
                problem = tr("В дампе игры нет трофеев: не найден {}").format(
                    trophies.missing(game) or "sce_sys/trophy")
            GLib.idle_add(show, directory, problem)
        threading.Thread(target=work, daemon=True).start()

    def show_trophies(self):
        directory, problem = self.trophy_shown
        editing = self.trophy_editing and directory is not None
        for row in self.trophy_rows:
            self.trophy_group.remove(row)
        self.trophy_rows = []
        self.trophy_checks = {}
        self.trophy_header.set_visible_child_name("editing" if editing else "menu")
        self.trophy_menu.set_sensitive(directory is not None)
        rows = []
        if directory is None:
            self.trophy_group.set_description("")
            rows.append(Adw.ActionRow(title=GLib.markup_escape_text(
                problem or tr("В дампе игры нет трофеев: не найден {}").format("sce_sys/trophy"))))
        else:
            listed, earned = trophies.read_list(directory), trophies.read_earned(directory)
            marked = trophies.read_marked(directory)
            counted = [i for i, t in listed.items() if t["grade"] != "P"] or list(listed)
            done = sum(1 for i in counted if i in earned)
            self.trophy_group.set_description(
                tr("Отметьте трофеи, уже полученные на PS4 или в другой версии порта.")
                if editing else tr("Получено {} из {}").format(done, len(counted)))
            if problem:
                rows.append(Adw.ActionRow(title=problem))
            order = sorted(listed.items(), key=lambda item: item[0] if editing else (item[0] not in earned, item[0]))
            for i, t in order:
                got = i in earned
                name = t["name"] or f"#{i}"
                detail = t["detail"]
                if t["hidden"] and not got and not editing:
                    name, detail = tr("Скрытый трофей"), ""
                when = time.strftime("%Y-%m-%d %H:%M", time.localtime(earned[i])) if got else None
                note = (tr("Отмечен вручную {}") if i in marked else tr("Получен {}")).format(when) \
                    if when else None
                subtitle = "\n".join(x for x in (detail, note) if x)
                row = Adw.ActionRow(title=GLib.markup_escape_text(name),
                                    subtitle=GLib.markup_escape_text(subtitle))
                icon = Path(directory) / "icons" / f"TROP{i:03d}.PNG"
                image = Gtk.Image(file=str(icon), pixel_size=48) if icon.is_file() else \
                    Gtk.Image(icon_name="starred-symbolic", pixel_size=48)
                row.add_prefix(image)
                grade = TROPHY_GRADES.get(t["grade"])
                if grade:
                    row.add_suffix(Gtk.Label(label=tr(grade), css_classes=["dim-label"]))
                if not got:
                    image.set_opacity(0.35)
                if editing:
                    # The game's own unlocks stay, and the platinum follows the others.
                    check = Gtk.CheckButton(active=got, valign=Gtk.Align.CENTER,
                                            sensitive=t["grade"] != "P" and (not got or i in marked))
                    row.add_suffix(check)
                    row.set_activatable_widget(check)
                    self.trophy_checks[i] = check
                rows.append(row)
        for row in rows:
            self.trophy_group.add(row)
            self.trophy_rows.append(row)

    def edit_trophies(self, editing):
        if editing and (self.process is not None or save_import.game_running()):
            self.alert(tr("Трофеи"), tr("Сначала закройте игру"))
            return
        self.trophy_editing = editing
        self.show_trophies()

    def on_trophies_save(self, _button):
        """Writes the checks: the trophies earned on a PS4, and the marks taken back."""
        if self.process is not None or save_import.game_running():
            self.alert(tr("Трофеи"), tr("Сначала закройте игру"))
            return
        directory = self.trophy_shown[0]
        try:
            earned, marked = trophies.read_earned(directory), trophies.read_marked(directory)
            for i, check in self.trophy_checks.items():
                if not check.get_active() and i in marked:
                    trophies.unmark_earned(directory, i)
            trophies.mark_earned(directory, [i for i, check in self.trophy_checks.items()
                                             if check.get_active() and i not in earned])
        except OSError as error:
            self.alert(tr("Трофеи"), tr("Не удалось сохранить: {}").format(error))
        self.trophy_editing = False
        self.show_trophies()

    # --- cheats page ---------------------------------------------------------------------

    def build_cheats_page(self):
        """The cheats and gameplay tweaks, in the Mods section."""
        self.cheat_rows = {}
        for rank, title, description, items in (
                (40, tr("Читы"), tr("Патчи игры версии 1.09, применяются при запуске. Для обычного "
                                    "прохождения и игры по сети оставьте их выключенными"), CHEATS),
                (50, tr("Изменения игрового процесса"), None, TWEAKS)):
            group = Adw.PreferencesGroup(title=title, description=description)
            for key, name, subtitle in items:
                row = Adw.SwitchRow(title=tr(name), subtitle=tr(subtitle),
                                    active=self.ini.get(key, "0") == "1")
                self.cheat_rows[key] = row
                group.add(row)
            self.place("mods", rank, group)
        # Enemy control and the free camera use the same buttons: one at a time.
        control, camera = self.cheat_rows["cheat_enemy_control"], self.effect_rows["debug_camera"]
        control.connect("notify::active", lambda row, _p: row.get_active() and camera.set_active(False))
        camera.connect("notify::active", lambda row, _p: row.get_active() and control.set_active(False))

    # --- sections ------------------------------------------------------------------------

    def place(self, section, rank, group):
        """Puts a settings group in a section's page, in `rank` order."""
        self.section_groups.setdefault(section, []).append((rank, group))

    def sidebar_header(self, row, before):
        # The sections set up once (and the Journal, About) apart from the everyday ones.
        row.set_header(Gtk.Separator(margin_top=6, margin_bottom=6)
                       if before is not None and row.section == "setup" else None)

    def show_section(self, name, reveal=True):
        """Shows a section; "online" and "coop" are the Multiplayer page's tabs."""
        if name in ("online", "coop"):
            self.multiplayer_stack.set_visible_child_name(name)
            name = "multiplayer"
        self.stack.set_visible_child_name(name)
        if reveal:
            self.split.set_show_content(True)

    def on_section_changed(self):
        name = self.stack.get_visible_child_name()
        row = next((row for row in self.sidebar if getattr(row, "section", None) == name), None)
        if row is not None and self.sidebar.get_selected_row() is not row:
            self.sidebar.select_row(row)
        page = self.stack.get_page(self.stack.get_visible_child())
        self.section_title.set_title(page.get_title() if page else "Bloodborne")
        # Not while trophies are being marked: the checks not saved yet would go.
        if name == "trophies" and not self.build_errors and not getattr(self, "trophy_editing", False):
            self.refresh_trophies()

    def on_width_breakpoint(self, narrow):
        self.narrow = narrow
        if hasattr(self, "split"):
            self.split.set_collapsed(narrow)

    def build_multiplayer_page(self):
        """Online play and local co-op, as two tabs of one page."""
        self.multiplayer_stack = Adw.ViewStack()
        for build_page, name, title, icon in (
                (self.build_online_page, "online", tr("По сети"), "network-workgroup-symbolic"),
                (self.build_coop_page, "coop", tr("Локально"), "computer-symbolic")):
            self.multiplayer_stack.add_titled_with_icon(build_page(), name, title, icon)
        switcher_type = getattr(Adw, "InlineViewSwitcher", None)
        if switcher_type is not None:
            switcher = switcher_type(stack=self.multiplayer_stack, halign=Gtk.Align.CENTER,
                                     display_mode=Adw.InlineViewSwitcherDisplayMode.BOTH)
        else:
            switcher = Adw.ViewSwitcher(stack=self.multiplayer_stack, policy=Adw.ViewSwitcherPolicy.WIDE,
                                        halign=Gtk.Align.CENTER)
        switcher.set_margin_top(12)
        switcher.set_margin_bottom(6)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(switcher)
        self.multiplayer_stack.set_vexpand(True)
        box.append(self.multiplayer_stack)
        return box

    def build_error_page(self, error):
        """In place of a page that failed to build: the error, to copy into a report."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=24,
                      margin_bottom=24, margin_start=24, margin_end=24)
        box.append(Gtk.Label(label=tr("Эта страница не открылась из-за ошибки"), wrap=True,
                             css_classes=["title-2"]))
        box.append(Gtk.Label(label=tr(
            "Запуск игры отключён, а настройки не сохраняются, чтобы ничего не испортить. "
            "Скопируйте ошибку в отчёт об ошибке"), wrap=True))
        view = Gtk.TextView(editable=False, monospace=True, cursor_visible=False,
                            wrap_mode=Gtk.WrapMode.WORD_CHAR)
        view.get_buffer().set_text(error)
        box.append(Gtk.ScrolledWindow(vexpand=True, child=view))
        copy = Gtk.Button(label=tr("Копировать"), halign=Gtk.Align.CENTER)
        copy.connect("clicked", lambda _button: self.get_clipboard().set(error))
        box.append(copy)
        return box

    def build_log_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.log_view = Gtk.TextView(editable=False, monospace=True, cursor_visible=False,
                                     wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self.log_view.set_top_margin(8)
        self.log_view.set_left_margin(8)
        self.log_view.set_right_margin(8)
        scroller = Gtk.ScrolledWindow(vexpand=True, child=self.log_view)
        self.log_scroller = scroller
        box.append(scroller)
        bar = Gtk.ActionBar()
        self.export_log_button = Gtk.Button(label=tr("Экспорт журнала…"))
        self.export_log_button.connect("clicked", self.on_export_log)
        bar.pack_end(self.export_log_button)
        self.copy_log_button = Gtk.Button(label=tr("Копировать"))
        self.copy_log_button.connect("clicked", self.on_copy_log)
        bar.pack_end(self.copy_log_button)
        box.append(bar)
        buffer = self.log_view.get_buffer()
        buffer.connect("changed", self.on_log_changed)
        self.on_log_changed(buffer)
        return box

    def on_log_changed(self, buffer):
        has_text = buffer.get_char_count() > 0
        self.copy_log_button.set_sensitive(has_text)
        self.export_log_button.set_sensitive(has_text)

    def log_text(self):
        buffer = self.log_view.get_buffer()
        return buffer.get_text(*buffer.get_bounds(), False)

    def full_log_text(self):
        """The whole session: the Journal keeps only its last MAX_LOG_LINES lines (issue #17)."""
        if not self.log_spool:
            return self.log_text()
        try:
            self.log_spool.seek(0)
            text = self.log_spool.read()
            self.log_spool.seek(0, os.SEEK_END)
            return text
        except (OSError, ValueError):
            return self.log_text()

    def clear_log(self):
        self.log_view.get_buffer().set_text("")
        if self.log_spool:
            self.log_spool.close()
        self.log_spool = None

    def on_copy_log(self, _button):
        self.get_clipboard().set(self.full_log_text())
        self.toasts.add_toast(Adw.Toast(title=tr("Журнал скопирован")))

    def on_export_log(self, _button):
        text = self.full_log_text()
        dialog = Gtk.FileDialog(title=tr("Экспорт журнала"))
        dialog.set_initial_name(f"bbport-{time.strftime('%Y%m%d_%H%M%S')}.log")

        def finish(dialog, result):
            try:
                chosen = dialog.save_finish(result)
            except GLib.Error:
                return
            if not chosen or not chosen.get_path():
                return
            try:
                Path(chosen.get_path()).write_text(text, encoding="utf-8")
            except OSError as error:
                self.toasts.add_toast(Adw.Toast(
                    title=tr("Не удалось сохранить журнал: {}").format(error.strerror or error)))
                return
            self.toasts.add_toast(Adw.Toast(title=tr("Журнал сохранён: {}").format(chosen.get_path())))
        dialog.save(self, None, finish)

    def append_log(self, text):
        if self.log_spool is not False:
            try:
                if self.log_spool is None:
                    self.log_spool = tempfile.TemporaryFile("w+", encoding="utf-8",
                                                            errors="replace")
                self.log_spool.write(text)
            except OSError:
                # A spool with a gap would be worse: Copy and Export take what the Journal shows.
                if self.log_spool:
                    self.log_spool.close()
                self.log_spool = False
        buffer = self.log_view.get_buffer()
        buffer.insert(buffer.get_end_iter(), text)
        extra = buffer.get_line_count() - MAX_LOG_LINES
        if extra > 0:
            buffer.delete(buffer.get_start_iter(), buffer.get_iter_at_line(extra)[1])
        # To the end once per burst of lines, not once per line.
        if not getattr(self, "log_scroll_queued", False):
            self.log_scroll_queued = True

            def scroll():
                # The Journal of now: a rebuild (another language) before the idle replaces it.
                self.log_scroll_queued = False
                adj = self.log_scroller.get_vadjustment()
                adj.set_value(adj.get_upper())
                return False
            GLib.idle_add(scroll)

    # --- local co-op page ----------------------------------------------------------------

    def build_coop_page(self):
        s = self.settings
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(description=tr(
            "Несколько игр на этом ПК, по одной на игрока, каждая в своей части экрана и со своим "
            "контроллером. Игрок 1 играет с настройками лаунчера; у остальных свои сохранения и "
            "bbport.ini (копия настроек игрока 1), без онлайна и Discord. Окна размещаются через "
            "X11 (на Wayland — через XWayland)"))
        self.coop_players_row = Adw.SpinRow.new_with_range(2, bbport_coop.MAX_PLAYERS, 1)
        self.coop_players_row.set_title(tr("Игроки"))
        self.coop_players_row.set_value(number(s["coop_players"], 2, int, "settings.json", "coop_players"))
        self.coop_players_row.connect("notify::value", lambda *_: self.show_coop_players())
        group.add(self.coop_players_row)
        self.coop_layout_row = combo_row(tr("Расположение"), None, COOP_LAYOUTS, s["coop_layout"])
        group.add(self.coop_layout_row)
        # The players' windows on another monitor than the game's alone (a TV beside the desk).
        self.coop_display_row = readable_choice(Adw.ComboRow(title=tr("Монитор")))
        self.coop_display_row.add_suffix(flat_button("view-refresh-symbolic", tr("Обновить список"),
                                                     lambda _button: self.fill_coop_display()))
        self.fill_coop_display()
        group.add(self.coop_display_row)
        self.coop_sound_row = Adw.SwitchRow(title=tr("Звук только у игрока 1"),
                                            subtitle=tr("Иначе звучат все игры сразу"),
                                            active=s["coop_sound_first_only"])
        group.add(self.coop_sound_row)
        page.add(group)

        pads = Adw.PreferencesGroup(title=tr("Контроллеры"), description=tr(
            "Игрок с клавиатурой в меню: I, J, K, L — стрелки, пробел — подтвердить, левый Shift — назад"))
        pads.set_header_suffix(flat_button("view-refresh-symbolic", tr("Обновить список"),
                                           lambda _button: self.with_gamepads(self.fill_coop_controllers)))
        self.coop_pad_rows = []
        for player in range(1, bbport_coop.MAX_PLAYERS + 1):
            row = readable_choice(Adw.ComboRow(title=tr("Игрок {}").format(player)))
            pads.add(row)
            self.coop_pad_rows.append(row)
        self.fill_coop_controllers()
        page.add(pads)

        # Player 1's saves for another player (each has its own): the same character to play with.
        saves = Adw.PreferencesGroup()
        copy = Adw.ActionRow(title=tr("Скопировать сохранения игрока 1"),
                             subtitle=tr("Его персонажи другому игроку; сохранения того игрока сначала "
                                         "копируются в его savedata-backups"))
        menu = Gio.Menu()
        actions = Gio.SimpleActionGroup()
        for player in range(2, bbport_coop.MAX_PLAYERS + 1):
            menu.append(tr("Игроку {}").format(player), f"coopsaves.player{player}")
            action = Gio.SimpleAction(name=f"player{player}")
            action.connect("activate", lambda _a, _p, player=player: self.on_coop_copy_saves(player))
            actions.add_action(action)
        copy.insert_action_group("coopsaves", actions)
        copy.add_suffix(Gtk.MenuButton(label=tr("Скопировать"), menu_model=menu, valign=Gtk.Align.CENTER))
        saves.add(copy)
        page.add(saves)

        start = Adw.PreferencesGroup()
        self.coop_button = Gtk.Button(label=tr("Играть вместе"), halign=Gtk.Align.CENTER,
                                      css_classes=["suggested-action", "pill"])
        self.coop_button.connect("clicked", self.on_coop_start)
        start.add(self.coop_button)
        page.add(start)
        self.show_coop_players()
        return page

    def on_coop_copy_saves(self, player):
        """Player 1's saves (the launcher's) as player `player`'s, after a backup of theirs
        (save_import.import_saves), with no game running."""
        title = tr("Скопировать сохранения игрока 1")
        if self.process is not None or self.coop_processes or save_import.game_running():
            self.alert(title, tr("Сначала закройте игру"))
            return
        game = self.settings["game_dir"] or None
        source = save_import.saves_in_use(self.user_dir(), game)
        if source is None:
            self.alert(title, tr("У игрока 1 пока нет сохранений"))
            return
        target = bbport_coop.data_dir(DATA_DIR, player) / "user"

        def copy():
            try:
                _saves, backup = save_import.import_saves(source, target, game)
            except (OSError, save_import.SaveImportError) as error:
                self.alert(title, tr("Не удалось скопировать: {}").format(error))
                return
            done = tr("Сохранения игрока 1 скопированы игроку {}").format(player)
            self.toasts.add_toast(Adw.Toast(title=done + (tr("; его прежние в {}").format(backup)
                                                          if backup else "")))
        self.confirm(title, tr("Сохранения игрока {} заменятся сохранениями игрока 1 (его прежние "
                               "сначала копируются в savedata-backups)").format(player),
                     tr("Скопировать"), copy)

    def fill_coop_display(self):
        self.fill_displays(self.coop_display_row, "coop_display", tr("Как у игры (Графика → Монитор)"))

    def fill_coop_controllers(self):
        """Each player's controller choices: none, the keyboard and mouse, the connected
        controllers by device path (two of one model are told apart by it), and the saved choice
        while it is not connected. Without a saved choice the connected ones go in order, then
        the keyboard."""
        connected = [(path, name) for _guid, name, _type, path in connected_gamepads(paths=True, look=False)
                     if path]
        names = [name for _path, name in connected]
        choices = [(tr("Не выбран"), ""), (tr("Клавиатура и мышь"), bbport_coop.KEYBOARD)]
        choices += [(name if names.count(name) == 1 else f"{name} ({Path(path).name})", path)
                    for path, name in connected]
        # On Refresh, the rows' choices, saved or not.
        saved = [combo_value(row) for row in self.coop_pad_rows if hasattr(row, "values")] or \
            list(self.settings.get("coop_controllers") or [])
        if not any(saved):
            saved = [path for path, _name in connected] + [bbport_coop.KEYBOARD]
        for player, row in enumerate(self.coop_pad_rows):
            current = saved[player] if player < len(saved) else ""
            row_choices = list(choices)
            if current not in [value for _, value in row_choices]:
                row_choices.append((tr("{} (не подключён)").format(current), current))
            row.set_model(Gtk.StringList.new([label for label, _ in row_choices]))
            row.values = [value for _, value in row_choices]
            row.set_selected(row.values.index(current))

    def show_coop_players(self):
        players = int(self.coop_players_row.get_value())
        for player, row in enumerate(self.coop_pad_rows):
            row.set_visible(player < players)
        # Three and four players always take the quarters of the display.
        self.coop_layout_row.set_sensitive(players == 2)
        self.coop_layout_row.set_subtitle(
            "" if players == 2 else tr("С тремя и четырьмя игроками — четверти экрана"))

    def on_coop_start(self, _button, looked=False):
        if not looked:  # the players' controllers and prompts from a fresh look, in a thread
            if self.can_start():
                self.with_gamepads(lambda: self.on_coop_start(None, True))
            return
        if not self.can_start():
            return
        self.store()
        players = self.settings["coop_players"]
        controllers = self.settings["coop_controllers"]
        problem = bbport_coop.problems(players, controllers)
        if problem:
            self.alert(tr("Локальный кооп"), {
                "x11": tr("Окна игроков расставляются через X11, а X-сервера нет: включите XWayland "
                          "в настройках сеанса или запустите сеанс X11"),
                "controller": tr("Выберите контроллер для каждого игрока"),
                "same controller": tr("Один контроллер выбран у двух игроков"),
                "keyboard twice": tr("Клавиатура и мышь могут быть только у одного игрока"),
            }[problem[0]])
            return
        layout = self.settings["coop_layout"]
        sound = self.settings["coop_sound_first_only"]
        display = self.settings.get("coop_display", "")
        first = bbport_coop.player_environment(self.environment(), 1, players, controllers[0],
                                               layout, sound, display=display)
        self.start_game(first)
        if not self.process:
            return
        for player in range(2, players + 1):
            folder = bbport_coop.prepare_data_dir(DATA_DIR, player, ini_path())
            env = game_environment(bbport_coop.player_settings(self.settings, player))
            env = bbport_coop.player_environment(env, player, players, controllers[player - 1],
                                                 layout, sound, folder, display)
            GLib.timeout_add_seconds(COOP_START_DELAY * (player - 1), self.start_coop_player,
                                     player, env, self.process)

    def start_coop_player(self, player, env, first):
        """Starts player 2-4's game while player 1's (`first`) still runs, not beside a game
        started after it ended; its lines go to the Journal marked with the player."""
        if self.process is not first:
            return False
        launcher = Gio.SubprocessLauncher.new(
            Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_MERGE)
        launcher.set_environ([f"{k}={v}" for k, v in env.items()])
        launcher.set_cwd(str(PORT_DIR))
        try:
            process = launcher.spawnv(["setsid", "bash", str(PORT_DIR / "run.sh")])
        except GLib.Error as error:
            self.append_log(f"[P{player}] {tr('Не удалось запустить: {}').format(error.message)}\n")
            return False
        self.coop_processes[player] = process
        stream = Gio.DataInputStream.new(process.get_stdout_pipe())
        self.read_coop_line(player, stream)
        process.wait_async(None, self.on_coop_exit, player)
        return False

    def read_coop_line(self, player, stream):
        def on_line(stream, result):
            try:
                line, _length = stream.read_line_finish_utf8(result)
            except GLib.Error:
                return
            if line is None:
                return
            self.append_log(f"[P{player}] {line}\n")
            self.read_coop_line(player, stream)
        stream.read_line_async(GLib.PRIORITY_DEFAULT, None, on_line)

    def on_coop_exit(self, process, result, player):
        try:
            process.wait_finish(result)
        except GLib.Error:
            pass
        status = process.get_exit_status() if process.get_if_exited() else -1
        self.coop_processes.pop(player, None)
        self.append_log(tr("\n— игра игрока {} завершилась (код {}) —\n").format(player, status))

    # --- process -------------------------------------------------------------------------

    def on_launch(self, _button):
        if self.process:
            self.stop_game()
            return
        npid = self.npid_row.get_text().strip()
        if online_module() and not self.online_row.get_active() and npid and hasattr(Adw, "AlertDialog") \
                and self.settings.get("ask_online_off", True):
            dialog = Adw.AlertDialog(heading="Bloodborne", body=tr(
                "Учётная запись для игры онлайн указана, но «Играть онлайн» выключено"))
            # Someone who plays offline on purpose: asked again once "Play online" is turned on.
            again = Gtk.CheckButton(label=tr("Больше не спрашивать"), halign=Gtk.Align.CENTER)
            dialog.set_extra_child(again)
            dialog.add_response("cancel", tr("Отмена"))
            dialog.add_response("offline", tr("Играть офлайн"))
            dialog.add_response("online", tr("Играть онлайн"))
            dialog.set_response_appearance("online", Adw.ResponseAppearance.SUGGESTED)

            def on_response(_dialog, response):
                if response != "cancel":
                    if again.get_active():
                        self.settings["ask_online_off"] = False
                    self.online_row.set_active(response == "online")
                    self.with_gamepads(self.start_game)
            dialog.connect("response", on_response)
            self.present_dialog(dialog)
            return
        self.with_gamepads(self.start_game)

    def start_game(self, env=None):
        """Starts the game with the launcher's environment, or `env` (local co-op's player 1)."""
        if not self.can_start():
            return
        if self.online_row.get_active() and "@" in self.npid_row.get_text():
            self.alert("Bloodborne", tr("Online ID — это имя учётной записи (NPID), "
                                        "зарегистрированное на сервере, а не адрес email"))
            self.show_section("online")
            return
        if self.online_row.get_active() and self.own_server_missing():
            self.alert("Bloodborne", tr("Введите адрес своего сервера или выберите Seamless Hunt"))
            self.show_section("online")
            return
        self.store()
        self.clear_log()
        self.backup_saves()
        launcher = Gio.SubprocessLauncher.new(
            Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_MERGE)
        launcher.set_environ([f"{k}={v}" for k, v in (env or self.environment()).items()])
        launcher.set_cwd(str(PORT_DIR))
        try:
            # setsid: the game and its helpers form one process group, stopped together.
            self.process = launcher.spawnv(["setsid", "bash", str(PORT_DIR / "run.sh")])
        except GLib.Error as error:
            self.toasts.add_toast(Adw.Toast(title=tr("Не удалось запустить: {}").format(error.message)))
            return
        self.stream = Gio.DataInputStream.new(self.process.get_stdout_pipe())
        self.server_refused = False
        self.read_line()
        self.process.wait_async(None, self.on_exit)
        self.update_launch_button()
        self.show_section("log")

    def backup_saves(self):
        """The automatic copy of the saves (Setup → Saves) before the game opens them; a failed
        copy is told, and the game starts anyway."""
        if not self.settings["saves_auto_backup"]:
            return
        try:
            copy = save_import.auto_backup(self.user_dir(), self.settings["saves_auto_backup_keep"],
                                           self.settings["game_dir"] or None)
        except (OSError, save_import.SaveImportError) as error:
            self.toasts.add_toast(Adw.Toast(title=tr("Не удалось сделать копию сохранений: {}").format(error)))
            return
        if copy:
            self.append_log(f"Launcher: saves backed up in {copy}\n")

    def read_line(self):
        self.stream.read_line_async(GLib.PRIORITY_DEFAULT, None, self.on_line)

    def on_line(self, stream, result):
        try:
            line, _length = stream.read_line_finish_utf8(result)
        except GLib.Error:
            return
        if line is None:
            return
        self.append_log(line + "\n")
        # The shadNet server refused this build (the game itself only says it is signed out).
        if line.startswith("Online: the shadNet server ") and not self.server_refused:
            self.server_refused = True
            self.alert(tr("Игра по сети"), tr(
                "Сервер shadNet не принимает bbport, игра осталась офлайн. Выберите Seamless Hunt "
                "или свой сервер (Мультиплеер → По сети)."))
        self.read_line()

    def stop_game(self):
        if self.process:
            self.stop_process(self.process, lambda: self.process)
        self.stop_coop_players()

    def stop_coop_players(self):
        for player, process in list(self.coop_processes.items()):
            self.stop_process(process, lambda player=player: self.coop_processes.get(player))

    def stop_process(self, process, running):
        """SIGTERM to the game's process group, SIGKILL 3 s later if `running()` still has it."""
        pid = int(process.get_identifier())
        try:
            os.killpg(pid, signal.SIGTERM)
        except OSError:
            process.force_exit()
        GLib.timeout_add_seconds(3, self.kill_if_running, pid, running)

    def kill_if_running(self, pid, running):
        if running():
            try:
                os.killpg(pid, signal.SIGKILL)
            except OSError:
                pass
        return False

    def on_exit(self, process, result):
        try:
            process.wait_finish(result)
        except GLib.Error:
            pass
        status = process.get_exit_status() if process.get_if_exited() else -1
        self.process = None
        # Local co-op is one session: the other players' games end with player 1's.
        self.stop_coop_players()
        self.update_launch_button()
        self.update_game_status()
        self.append_log(tr("\n— игра завершилась (код {}) —\n").format(status))
        self.work_done()

    def on_close(self, _window):
        self.store()
        if self.process or self.coop_processes:
            self.stop_game()
        if self.fsr411_build:
            self.stop_fsr411_build()
        if self.atlas_job:
            self.stop_atlas_job()
        return False

    # --- Hunter's Atlas: its maps ----------------------------------------------------------

    def show_atlas(self):
        """The map group as things are: the maps' state, what can be done now."""
        state = bbport_atlas_maps.maps_state(DATA_DIR)
        folder = atlas_dir()
        working = self.atlas_job is not None
        game_running = self.process is not None
        if folder:
            self.atlas_row.set_subtitle(tr("Карта на весь экран в меню игры (Start): где вы, фонари и предметы"))
        else:
            self.atlas_row.set_subtitle(tr("Сначала подготовьте карты (ниже)"))
        self.atlas_row.set_sensitive(bool(folder))
        for row in (self.atlas_travel_row, self.atlas_items_row):
            row.set_sensitive(bool(folder) and self.atlas_row.get_active())
        if state["ready"]:
            language = ATLAS_LANGUAGE_NAMES.get(state["language"], state["language"] or "?")
            lines = [tr("Готовы: {}, {} МБ").format(language, state["bytes"] >> 20)]
            wanted = bbport_atlas_maps.language_folder(self.settings.get("language") or system_game_language())
            english = ("engus", "enggb")
            if state["language"] and wanted != state["language"] and \
                    not (wanted in english and state["language"] in english):
                lines.append(tr("Игра на другом языке: сделайте карты заново, чтобы названия были на нём"))
        elif folder:
            lines = [tr("Готовы (папка {})").format(folder)]
        else:
            lines = [tr("Не подготовлены. Их делают из ваших файлов игры: в первый раз скачивается около "
                        "200 МБ (около 600 МБ на диске), это занимает несколько минут")]
        self.atlas_maps_row.set_subtitle("\n".join(lines))
        self.atlas_prepare_button.set_label(tr("Сделать заново") if state["ready"] else tr("Подготовить"))
        if not state["ready"] and not folder:
            self.atlas_prepare_button.add_css_class("suggested-action")
        else:
            self.atlas_prepare_button.remove_css_class("suggested-action")
        self.atlas_prepare_button.set_sensitive(not working and not game_running)
        has_files = state["ready"] or (DATA_DIR / bbport_atlas_maps.TOOLS).exists()
        self.atlas_delete_button.set_sensitive(has_files and not working and not game_running)
        self.atlas_progress_row.set_visible(working)

    def confirm(self, heading, body, action, on_yes, destructive=False):
        """Asks before something that downloads or removes files."""
        dialog_type = getattr(Adw, "AlertDialog", None)
        if dialog_type is not None:
            dialog = dialog_type(heading=heading, body=body)
        else:
            dialog = Adw.MessageDialog(transient_for=self, heading=heading, body=body)
        dialog.add_response("cancel", tr("Отмена"))
        dialog.add_response("yes", action)
        dialog.set_response_appearance(
            "yes", Adw.ResponseAppearance.DESTRUCTIVE if destructive else Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("cancel")
        dialog.connect("response", lambda _d, response: response == "yes" and on_yes())
        if dialog_type is not None:
            self.present_dialog(dialog)
        else:
            dialog.present()

    def on_atlas_prepare(self, _button):
        if self.atlas_job or self.process:
            return
        game = Path(self.settings["game_dir"]).expanduser()
        if not (game / "eboot.bin").is_file():
            self.alert(tr("Карта (Hunter's Atlas)"), tr("Сначала выберите папку игры"))
            return
        if bbport_atlas_maps.maps_state(DATA_DIR)["ready"]:
            body = tr("Карты будут сделаны заново из файлов игры (несколько минут). Нынешние остаются, "
                      "пока новые не готовы")
        else:
            body = tr("Лаунчер скачает около 200 МБ (Python и библиотеки генератора карт) и сделает карты из "
                      "ваших файлов игры; всё вместе займёт около 600 МБ в папке данных. Это займёт несколько "
                      "минут; игру в это время запускать нельзя")
        self.confirm(tr("Подготовить карты?"), body, tr("Подготовить"), lambda: self.start_atlas_job(game))

    def start_atlas_job(self, game):
        self.store()
        language = self.settings.get("language") or str(system_game_language())
        launcher = Gio.SubprocessLauncher.new(
            Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_MERGE)
        launcher.set_cwd(str(PORT_DIR))
        try:
            # setsid: uv and the generator stop with it (Cancel).
            self.atlas_job = launcher.spawnv([
                "setsid", sys.executable, str(PORT_DIR / "launcher" / "bbport_atlas_maps.py"), "prepare",
                "--data-dir", str(DATA_DIR), "--game-dir", str(game), "--language", language])
        except GLib.Error as error:
            self.alert(tr("Карта (Hunter's Atlas)"), tr("Не удалось запустить: {}").format(error.message))
            return
        self.atlas_result = None
        self.atlas_progress.set_fraction(0)
        self.atlas_progress.set_text(tr(ATLAS_STEPS["uv"]))
        self.append_log(tr("\n— подготовка карт —\n"))
        self.update_launch_button()
        stream = Gio.DataInputStream.new(self.atlas_job.get_stdout_pipe())
        self.read_atlas_line(stream)
        self.atlas_job.wait_async(None, self.on_atlas_exit)

    def read_atlas_line(self, stream):
        def on_line(stream, result):
            try:
                line, _length = stream.read_line_finish_utf8(result)
            except GLib.Error:
                return
            if line is None:
                return
            self.append_log(f"[atlas] {line}\n")
            try:
                record = json.loads(line)
            except ValueError:
                record = None
            if isinstance(record, dict):
                if "progress" in record:
                    self.atlas_progress.set_fraction(min(max(record["progress"], 0), 100) / 100)
                    self.atlas_progress.set_text(f"{tr(ATLAS_STEPS.get(record.get('stage'), ''))} "
                                                 f"{record['progress']} %")
                elif "error" in record or "done" in record:
                    self.atlas_result = record
            self.read_atlas_line(stream)
        stream.read_line_async(GLib.PRIORITY_DEFAULT, None, on_line)

    def on_atlas_exit(self, process, result):
        try:
            process.wait_finish(result)
        except GLib.Error:
            pass
        self.atlas_job = None
        outcome = self.atlas_result or {"error": "unexpected", "detail": None}
        if outcome.get("done"):
            first = not self.atlas_row.get_active()
            self.show_atlas()
            if first:
                self.atlas_row.set_active(True)
            self.store()
            self.toasts.add_toast(Adw.Toast(title=tr("Карты готовы")))
        elif outcome.get("error") == "cancelled":
            self.toasts.add_toast(Adw.Toast(title=tr("Подготовка карт отменена; прежние карты не тронуты")))
        else:
            key = ATLAS_ERRORS.get(outcome.get("error"), "Не удалось подготовить карты ({}). Подробности в журнале")
            self.alert(tr("Карта (Hunter's Atlas)"), tr(key).format(outcome.get("detail") or outcome.get("error")))
        self.update_launch_button()
        self.work_done()

    def stop_atlas_job(self):
        if not self.atlas_job:
            return
        try:
            os.killpg(int(self.atlas_job.get_identifier()), signal.SIGTERM)
        except (OSError, TypeError, ValueError):
            self.atlas_job.force_exit()

    def on_atlas_delete(self):
        if self.atlas_job or self.process:
            return
        size = bbport_atlas_maps.maps_state(DATA_DIR)["bytes"] or \
            bbport_atlas_maps.folder_bytes(DATA_DIR / bbport_atlas_maps.TOOLS)

        def delete():
            bbport_atlas_maps.delete(DATA_DIR)
            self.atlas_row.set_active(False)
            self.store()
            self.show_atlas()
            # delete() goes on past what it cannot remove (a folder of another user, read-only).
            left = [DATA_DIR / name for name in (bbport_atlas_maps.MAPS, bbport_atlas_maps.TOOLS)
                    if (DATA_DIR / name).exists()]
            if left:
                self.alert(tr("Карта (Hunter's Atlas)"), tr("Не удалось удалить всё: осталась папка {}").format(left[0]))
            else:
                self.toasts.add_toast(Adw.Toast(title=tr("Карты удалены")))
        self.confirm(tr("Удалить карты?"),
                     tr("Карты и инструменты для них (около {} МБ) будут удалены. Их можно подготовить снова").format(
                         size >> 20), tr("Удалить"), delete, destructive=True)

    # --- FSR 4.1.1 from the user's DLL -----------------------------------------------------

    def update_fsr411_row(self, progress=None):
        building = self.fsr411_build is not None
        self.fsr411_button.set_label(tr("Отменить") if building else tr("Выбрать DLL…"))
        if hasattr(self, "fsr412_button"):
            self.fsr412_button.set_label(tr("Отменить") if building else tr("Выбрать файл…"))
        if progress:
            self.fsr411_row.set_subtitle(progress)
        elif not building:
            self.fsr411_row.set_subtitle(tr(
                "Собрать FSR 4.1.1 из amd_fidelityfx_upscaler_dx12.dll 4.1.x (OptiScaler: папка "
                "FSR4_LATEST, или из игры с FSR 4.1). Нужен GE-Proton 10+, Proton Experimental или "
                "Proton-CachyOS; 2–5 минут (RDNA4: вдвое дольше, ещё и вариант FP8)"))

    def alert(self, heading, body):
        if hasattr(Adw, "AlertDialog"):
            dialog = Adw.AlertDialog(heading=heading, body=body)
            dialog.add_response("ok", "OK")
            self.present_dialog(dialog)
        else:
            self.toasts.add_toast(Adw.Toast(title=f"{heading}: {body}", timeout=10))

    def update_dlss_row(self):
        own = ngx_libraries(self.user_dir() / "dlss")
        bundled = ngx_libraries(dlss_dir())
        own_fg = ngx_libraries(self.user_dir() / "dlss", NGX_FG_PREFIX)
        bundled_fg = ngx_libraries(dlss_dir(), NGX_FG_PREFIX)
        bridge = (dlss_dir() / "libbbport_dlss.so").is_file()
        if own:
            text = tr("Своя: {}").format(own[-1].name[len(NGX_PREFIX):])
        elif bundled:
            text = tr("Из сборки: {}").format(bundled[-1].name[len(NGX_PREFIX):])
        else:
            text = tr("Нет: выберите libnvidia-ngx-dlss.so.* из DLSS SDK NVIDIA ({})").format(DLSS_SDK_URL)
        # The Frame Generation library (the same SDK folder): the game searches both places.
        if own_fg:
            text += "\n" + tr("Генерация кадров: своя {}").format(own_fg[-1].name[len(NGX_FG_PREFIX):])
        elif bundled_fg:
            text += "\n" + tr("Генерация кадров: из сборки {}").format(bundled_fg[-1].name[len(NGX_FG_PREFIX):])
        else:
            text += "\n" + tr("Генерация кадров: нет libnvidia-ngx-dlssg.so.* (выберите её так же; DLSS SDK 310.7 или новее)")
        if not bridge:
            text += "\n" + tr("Эта сборка без моста DLSS (libbbport_dlss.so): DLSS работать не будет")
        self.dlss_row.set_subtitle(text)
        self.dlss_reset_button.set_sensitive(bool(own or own_fg))
        if hasattr(self, "sharpness_row"):  # built after this row
            self.update_upscaler_status()

    def choose_ngx(self):
        dialog = Gtk.FileDialog(title=tr("Библиотека DLSS NVIDIA (libnvidia-ngx-dlss.so.*, libnvidia-ngx-dlssg.so.*)"))
        files = Gtk.FileFilter()
        files.set_name("libnvidia-ngx-dlss*.so.*, nvngx_dlss*.dll")
        for pattern in ("libnvidia-ngx-dlss.so*", "libnvidia-ngx-dlssg.so*", "*.dll", "*.DLL"):
            files.add_pattern(pattern)
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(files)
        dialog.set_filters(filters)
        dialog.set_default_filter(files)

        def finish(dialog, result):
            try:
                chosen = dialog.open_finish(result)
            except GLib.Error:
                return
            if chosen and chosen.get_path():
                self.install_ngx(Path(chosen.get_path()))
        dialog.open(self, None, finish)

    def install_ngx(self, path):
        if path.suffix.lower() == ".dll":
            self.alert(tr("Нужна библиотека для Linux"), tr(
                "{} — библиотека DLSS для Windows; на Linux NVIDIA её не загружает. Нужна "
                "libnvidia-ngx-dlss.so.<версия> из DLSS SDK NVIDIA: {}").format(path.name, DLSS_SDK_URL))
            return
        try:
            with open(path, "rb") as f:
                elf = f.read(4) == b"\x7fELF"
        except OSError as error:
            self.alert(tr("Не удалось прочитать файл"), str(error))
            return
        prefix = ngx_prefix_of(path.name)
        if prefix is None or not elf:
            self.alert(tr("Это не библиотека DLSS"), tr(
                "Нужен файл libnvidia-ngx-dlss.so.<версия> (DLSS) или libnvidia-ngx-dlssg.so.<версия> "
                "(генерация кадров) из DLSS SDK NVIDIA: {}").format(DLSS_SDK_URL))
            return
        target = self.user_dir() / "dlss"
        try:
            target.mkdir(parents=True, exist_ok=True)
            for old in ngx_libraries(target, prefix):  # one of each kind
                old.unlink()
            shutil.copy2(path, target / path.name)
        except OSError as error:
            self.alert(tr("Не удалось скопировать библиотеку"), str(error))
            return
        version = path.name[len(prefix):]
        self.toasts.add_toast(Adw.Toast(title=(
            tr("DLSS Frame Generation {}: готово") if prefix == NGX_FG_PREFIX else tr("DLSS {}: готово")
        ).format(version)))
        self.update_dlss_row()

    def reset_ngx(self):
        for prefix in (NGX_PREFIX, NGX_FG_PREFIX):
            for old in ngx_libraries(self.user_dir() / "dlss", prefix):
                try:
                    old.unlink()
                except OSError:
                    pass
        self.update_dlss_row()

    def choose_dll(self, title, done):
        dialog = Gtk.FileDialog(title=title)
        dll = Gtk.FileFilter()
        dll.set_name("DLL")
        dll.add_pattern("*.dll")
        dll.add_pattern("*.DLL")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(dll)
        dialog.set_filters(filters)
        dialog.set_default_filter(dll)
        folder = self.settings.get("fsr411_dll_dir", "")
        if folder and Path(folder).is_dir():
            dialog.set_initial_folder(Gio.File.new_for_path(folder))

        def finish(dialog, result):
            try:
                chosen = dialog.open_finish(result)
            except GLib.Error:
                return
            if chosen and chosen.get_path():
                done(chosen.get_path())
        dialog.open(self, None, finish)

    def on_fsr411_button(self, _button):
        if self.fsr411_build:
            self.stop_fsr411_build()
            return
        self.choose_dll(tr("DLL апскейлера AMD (amd_fidelityfx_upscaler_dx12.dll)"),
                        self.on_fsr411_dll)

    def on_fsr412_button(self, _button):
        if self.fsr411_build:
            self.stop_fsr411_build()
            return
        dialog = Gtk.FileDialog(title=tr("Драйвер AMD: установщик Adrenalin (.exe) или amdxcffx64.dll"))
        files = Gtk.FileFilter()
        files.set_name("EXE, DLL")
        for pattern in ("*.exe", "*.EXE", "*.dll", "*.DLL"):
            files.add_pattern(pattern)
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(files)
        dialog.set_filters(filters)
        dialog.set_default_filter(files)

        def finish(dialog, result):
            try:
                chosen = dialog.open_finish(result)
            except GLib.Error:
                return
            if chosen and chosen.get_path():
                self.on_fsr412_driver(chosen.get_path())
        dialog.open(self, None, finish)

    def on_fsr412_driver(self, driver):
        """The driver's FSR 4 module answers through AMD's upscaler DLL: the one FSR 4.1.1 was
        built from, else chosen now."""
        upscaler = self.settings.get("fsr411_dll", "")
        if upscaler and Path(upscaler).is_file():
            self.start_fsr411_build(driver, upscaler)
            return
        self.toasts.add_toast(Adw.Toast(title=tr(
            "Ещё нужна DLL FSR 4.1.x: выберите amd_fidelityfx_upscaler_dx12.dll"), timeout=8))
        self.choose_dll(tr("DLL апскейлера AMD (amd_fidelityfx_upscaler_dx12.dll)"),
                        lambda path: self.start_fsr411_build(driver, path))

    def on_fsr411_dll(self, upscaler, loader=None):
        import dll_info
        self.settings["fsr411_dll_dir"] = str(Path(upscaler).parent)
        self.settings["fsr411_dll"] = str(upscaler)
        status, problem, details = dll_info.inspect(upscaler, loader)
        kind = details.get("kind")
        version = details.get("version", "?")
        if status == dll_info.UNSUPPORTED:
            if kind == "fsr4_0":
                body = tr(
                    "{}: FSR {}. Это официальная FSR 4.0.x от AMD: она включается только на "
                    "видеокартах RDNA4 (RX 9000), а под Proton на других видеокартах не "
                    "запускается, поэтому записать её нельзя.\n\nНужна FSR 4.1.x: например, "
                    "FSR4_LATEST из OptiScaler или DLL из игры с FSR 4.1.").format(
                        Path(upscaler).name, version)
            elif kind == "not_fsr4":
                body = tr("{}: в этой DLL нет FSR 4. Нужна amd_fidelityfx_upscaler_dx12.dll "
                          "версии 4.1.x.").format(Path(upscaler).name)
            else:
                models = ", ".join(details.get("models", [])) or tr("нет")
                body = tr(
                    "{}: версия {}, модели FSR 4: {}.\n\nbbport повторяет только официальную FSR 4.1.x "
                    "от AMD (модель v07_fp8_no_scale): например, FSR4_LATEST из OptiScaler или "
                    "amd_fidelityfx_upscaler_dx12.dll из игры с FSR 4.1. Сборки сообщества (4.0.2b и "
                    "подобные) устроены иначе и пока не поддерживаются.").format(
                        Path(upscaler).name, version, models)
            self.alert(tr("Эта DLL не подходит"), body)
            return
        if status == dll_info.NO_LOADER:
            if kind == "loader_is_upscaler":
                self.alert(tr("Это не загрузчик"), tr(
                    "{} — это DLL апскейлера. Загрузчик называется amd_fidelityfx_loader_dx12.dll "
                    "(у OptiScaler — amd_fidelityfx_dx12.dll) и лежит в той же папке игры, что и "
                    "DLL апскейлера.").format(Path(loader).name))
                return
            if loader:
                self.alert(tr("Загрузчик не подходит"), tr(
                    "{}: версия {}. Нужен загрузчик FidelityFX 2.x — из той же игры, что и DLL "
                    "апскейлера.").format(Path(loader).name, details.get("loader_version", "?")))
                return
            # A DLL without the FidelityFX API exports (AMD's own export it: no loader needed), and no
            # loader next to it or one folder up: ask for it.
            self.toasts.add_toast(Adw.Toast(title=tr(
                "Рядом с DLL нет загрузчика: выберите amd_fidelityfx_loader_dx12.dll из папки игры"),
                timeout=8))
            self.choose_dll(tr("Загрузчик FidelityFX (amd_fidelityfx_loader_dx12.dll или "
                               "amd_fidelityfx_dx12.dll)"),
                            lambda path: self.on_fsr411_dll(upscaler, path))
            return
        self.start_fsr411_build(upscaler, details.get("loader"))

    def start_fsr411_build(self, upscaler, loader):
        command, env = fsr411_build_command(upscaler, loader)
        launcher = Gio.SubprocessLauncher.new(
            Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_MERGE)
        launcher.set_environ([f"{k}={v}" for k, v in env.items()])
        launcher.set_cwd(str(PORT_DIR))
        try:
            # setsid: Proton and its helpers form one process group, cancelled together.
            self.fsr411_build = launcher.spawnv(["setsid", *command])
        except GLib.Error as error:
            self.toasts.add_toast(Adw.Toast(title=tr("Не удалось запустить: {}").format(error.message)))
            return
        self.append_log(tr("\n— сборка FSR 4.1.1 из {} —\n").format(upscaler))
        stream = Gio.DataInputStream.new(self.fsr411_build.get_stdout_pipe())
        stream.read_line_async(GLib.PRIORITY_DEFAULT, None, self.on_fsr411_line)
        self.fsr411_build.wait_async(None, self.on_fsr411_built)
        self.update_fsr411_row(tr("Подготовка…"))
        self.update_launch_button()

    def on_fsr411_line(self, stream, result):
        try:
            line, _length = stream.read_line_finish_utf8(result)
        except GLib.Error:
            return
        if line is None:
            return
        self.append_log(line + "\n")
        if self.fsr411_build:
            step = re.match(r"\[\s*(\d+)/(\d+)\]", line)
            if step:
                self.update_fsr411_row(tr("Запись проходов DLL под Proton: {} из {}").format(*step.groups()))
            elif line.startswith("Translating"):
                self.update_fsr411_row(tr("Перевод проходов в SPIR-V…"))
        stream.read_line_async(GLib.PRIORITY_DEFAULT, None, self.on_fsr411_line)

    def stop_fsr411_build(self):
        pid = int(self.fsr411_build.get_identifier())
        self.fsr411_cancelled = True
        try:
            os.killpg(pid, signal.SIGTERM)
        except OSError:
            self.fsr411_build.force_exit()

    def on_fsr411_built(self, process, result):
        try:
            process.wait_finish(result)
        except GLib.Error:
            pass
        status = process.get_exit_status() if process.get_if_exited() else -1
        cancelled = getattr(self, "fsr411_cancelled", False)
        self.fsr411_cancelled = False
        self.fsr411_build = None
        self.update_fsr411_row()
        self.update_launch_button()
        self.work_done()
        self.append_log(tr("— сборка FSR 4.1.1 завершилась (код {}) —\n").format(status))
        if status == 0:
            for index, (_label, value) in enumerate(UPSCALERS):
                if value == "fsr411":
                    self.upscaler_row.set_selected(index)
            self.update_upscaler_status()
            self.store()
            self.toasts.add_toast(Adw.Toast(title=tr("FSR 4.1.1 собран и выбран")))
        elif cancelled:
            self.toasts.add_toast(Adw.Toast(title=tr("Сборка FSR 4.1.1 отменена")))
        else:
            message = FSR411_BUILD_ERRORS.get(status, "Сборка не удалась (код {}): подробности в журнале")
            self.alert(tr("FSR 4.1.1 не собран"), tr(message).format(status))


class LauncherApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.github.bbport.Launcher",
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)

    def do_activate(self):
        # The launcher's own icons (launcher/icons: GitHub's mark), symbolic like the theme's.
        display = Gdk.Display.get_default()
        if display:
            Gtk.IconTheme.get_for_display(display).add_search_path(str(PORT_DIR / "launcher" / "icons"))
        window = self.get_active_window() or LauncherWindow(self)
        window.present()


def play():
    """--play: the game with the saved settings, no window (Steam Deck game mode)."""
    settings = load_settings()
    # No window sets the launcher's language here, and the in-game menu takes it (BB_MENU_LANGUAGE).
    set_language(settings.get("ui_language", ""))
    if not (Path(settings["game_dir"]).expanduser() / "eboot.bin").is_file():
        print("bbport: choose the game folder in the launcher first", file=sys.stderr)
        return 1
    migrate_ini(settings, *load_ini())
    os.chdir(PORT_DIR)
    env = game_environment(settings)
    # Started by Steam: its runtime's libraries are first in LD_LIBRARY_PATH; the port is built
    # against the system's. Steam keeps the original in SYSTEM_LD_LIBRARY_PATH.
    if "SYSTEM_LD_LIBRARY_PATH" in env:
        env["LD_LIBRARY_PATH"] = env["SYSTEM_LD_LIBRARY_PATH"]
    os.execvpe("bash", ["bash", str(PORT_DIR / "run.sh")], env)


def build_fsr411(arguments):
    """--build-fsr411 <upscaler DLL> [loader DLL]: the launcher's FSR 4.1.1 build, without a window."""
    if not 1 <= len(arguments) <= 2:
        print("usage: --build-fsr411 <amd_fidelityfx_upscaler_dx12.dll> [loader DLL]", file=sys.stderr)
        return 1
    command, env = fsr411_build_command(*arguments)
    return subprocess.call(command, env=env, cwd=PORT_DIR)


if __name__ == "__main__":
    if "--play" in sys.argv[1:]:
        sys.exit(play())
    if "--build-fsr411" in sys.argv[1:]:
        sys.exit(build_fsr411(sys.argv[sys.argv.index("--build-fsr411") + 1:]))
    sys.exit(LauncherApp().run(sys.argv))
