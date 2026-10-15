#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Seamless co-op (BBSC, bbsc/): its options and the game's variables for them.

BBSC's own list of options is bbsc/emulator/mod/mod.json (the Windows mod's "Mods" tab reads it):
each has an id, a type (bool, int, text), a default and the environment variable BBSC reads. The
launcher keeps only what the player changed (settings "bbsc_options": {id: value}) and the switch
itself ("bbsc"); environment() turns them into variables for run.sh, which loads libbbsc.so.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# The repository's copy, and the AppImage's (next to libbbsc.so).
MOD_JSON = (ROOT / 'bbsc/emulator/mod/mod.json', ROOT / 'bbsc/mod.json')
# Not in bbport's build of BBSC: its own Discord status (bbport has one).
LEFT_OUT = {'discord'}


def mod_info(paths=MOD_JSON):
    """mod.json as a dict, or None when this build has no BBSC."""
    for path in paths:
        try:
            return json.loads(Path(path).read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
    return None


def options(info=None):
    """BBSC's options this build offers, in mod.json's order."""
    info = mod_info() if info is None else info
    if not info:
        return []
    return [o for o in info.get('settings', [])
            if o.get('id') not in LEFT_OUT and o.get('env') and o.get('type') in ('bool', 'int', 'text')]


def value_of(option, chosen):
    """The value to use: the player's (checked against the option's type and range), else the
    default."""
    value = chosen.get(option['id'], option.get('default'))
    kind = option['type']
    if kind == 'bool':
        return bool(value) if isinstance(value, (bool, int)) else bool(option.get('default'))
    if kind == 'int':
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = int(option.get('default', 0))
        return max(int(option.get('min', value)), min(int(option.get('max', value)), value))
    return str(value or '').strip()


def environment(settings, info=None):
    """BB_BBSC and BBSC's option variables when seamless co-op is on, else nothing."""
    if not settings.get('bbsc'):
        return {}
    chosen = settings.get('bbsc_options') or {}
    env = {'BB_BBSC': '1'}
    for option in options(info):
        value = value_of(option, chosen)
        if option['type'] == 'bool':
            env[option['env']] = '1' if value else '0'
        elif option['type'] == 'int':
            env[option['env']] = str(value)
        elif value:
            env[option['env']] = value
    return env
