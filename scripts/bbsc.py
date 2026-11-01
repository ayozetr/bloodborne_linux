#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Seamless co-op (BBSC, gpu/bbnet20/bbsc): its options and the game's variables for them.

BBSC's options (scripts/bbsc_options.json, from BBSC 0.0.2's mod.json) each have an id, a type
(bool, int, text), a default and the environment variable BBSC reads. The launcher keeps only what
the player changed (settings "bbsc_options": {id: value}); environment() turns them into variables
for the game. Left out of the list: BBSC's two master switches (the launcher's BBSC switch is the
one), its own Discord status (bbport has one) and its P2P channel, which 0.7's BBSC does not read.
"""
import json
from pathlib import Path

OPTIONS_JSON = Path(__file__).resolve().with_name('bbsc_options.json')


def options(path=OPTIONS_JSON):
    """BBSC's options, in their list's order; [] without the list."""
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    return [o for o in data.get('settings', [])
            if o.get('env') and o.get('type') in ('bool', 'int', 'text')]


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


def environment(settings, listed=None):
    """BBSC's option variables, for the options the player changed; nothing with BBSC off."""
    if not settings.get('bbsc', True):
        return {}
    chosen = settings.get('bbsc_options') or {}
    env = {}
    for option in options() if listed is None else listed:
        if option['id'] not in chosen:
            continue  # BBSC's own default
        value = value_of(option, chosen)
        if option['type'] == 'bool':
            env[option['env']] = '1' if value else '0'
        elif option['type'] == 'int':
            env[option['env']] = str(value)
        elif value:
            env[option['env']] = value
    return env
