#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Discord Rich Presence while the game runs: "Playing Bloodborne", the area the player is in,
online or offline or the co-op partners, and the time played. run.sh starts it next to the game
(BB_DISCORD=0 turns it off); it ends with the game.

The game writes what the helper shows into BB_PRESENCE_DIR (--presence-dir): `area`, the map of
the player's area (src/runtime_file.c), and `coop`, the online IDs of the players connected with
this one, one per line (the online module, np_signaling_state.cpp).

Discord's local IPC: a Unix socket discord-ipc-N in the runtime directory (also inside the
Flatpak, Snap and Vesktop sandboxes' directories). Frames are a little-endian op code and length,
then JSON: a handshake (op 0) with the application id, then SET_ACTIVITY commands (op 1).
Without Discord running the helper keeps looking for it and does nothing else.
"""
import argparse
import json
import os
from pathlib import Path
import socket
import struct
import time
import uuid

# The "Bloodborne" application on Discord's developer portal (its icon is the art asset
# "bloodborne").
CLIENT_ID = '1558176258121269389'
HANDSHAKE, FRAME, CLOSE = 0, 1, 2
# The areas by map (map/mapstudio/mXX_YY_...): the names of Smithbox's Bloodborne map aliases
# (github.com/vawser/Smithbox, MIT). The Chalice Dungeons (m29) are one name.
AREAS = {
    'm21_00': "Hunter's Dream",
    'm21_01': 'Abandoned Old Workshop',
    'm22_00': 'Hemwick Charnel Lane',
    'm23_00': 'Old Yharnam',
    'm24_00': 'Cathedral Ward',
    'm24_01': 'Central Yharnam',
    'm24_02': 'Upper Cathedral Ward',
    'm25_00': 'Forsaken Castle Cainhurst',
    'm26_00': 'Nightmare of Mensis',
    'm27_00': 'Forbidden Woods',
    'm28_00': "Yahar'gul, Unseen Village",
    'm32_00': 'Byrgenwerth',
    'm33_00': 'Nightmare Frontier',
    'm34_00': "Hunter's Nightmare",
    'm35_00': 'Research Hall',
    'm36_00': 'Fishing Hamlet',
}
CHALICE_DUNGEON = 'Chalice Dungeon'
# Where Discord clients put their socket, relative to the runtime/temporary directory.
SUBDIRS = ('', 'app/com.discordapp.Discord', 'app/com.discordapp.DiscordCanary',
           'app/dev.vencord.Vesktop', '.flatpak/com.discordapp.Discord/xdg-run',
           '.flatpak/dev.vencord.Vesktop/xdg-run', 'snap.discord', 'snap.discord-canary')


def socket_paths(env=os.environ):
    bases = [env.get(name) for name in ('XDG_RUNTIME_DIR', 'TMPDIR', 'TMP', 'TEMP')] + ['/tmp']
    for base in dict.fromkeys(b for b in bases if b):
        for sub in SUBDIRS:
            for n in range(10):
                yield Path(base) / sub / f'discord-ipc-{n}'


def frame(op, payload):
    data = json.dumps(payload).encode()
    return struct.pack('<II', op, len(data)) + data


def read_frame(sock):
    header = b''
    while len(header) < 8:
        chunk = sock.recv(8 - len(header))
        if not chunk:
            raise ConnectionError('Discord closed the connection')
        header += chunk
    op, length = struct.unpack('<II', header)
    body = b''
    while len(body) < length:
        chunk = sock.recv(length - len(body))
        if not chunk:
            raise ConnectionError('Discord closed the connection')
        body += chunk
    return op, json.loads(body or b'{}')


def connect(client_id, env=os.environ):
    """A connected, handshaken socket to the first Discord client found, or None."""
    for path in socket_paths(env):
        if not path.is_socket():
            continue
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            sock.connect(str(path))
            sock.sendall(frame(HANDSHAKE, {'v': 1, 'client_id': client_id}))
            op, reply = read_frame(sock)
            if op == FRAME and reply.get('evt') == 'READY':
                return sock
        except (OSError, ValueError, ConnectionError):
            pass
        sock.close()
    return None


def area_name(map_id):
    """The area of a map ("m24_01"), or None for an unknown one."""
    map_id = (map_id or '').strip().lower()
    if map_id.startswith('m29_'):
        return CHALICE_DUNGEON
    return AREAS.get(map_id)


def read_state(directory):
    """(map, co-op partners) from the game's presence directory; (None, []) without it."""
    if directory is None:
        return None, []
    directory = Path(directory)
    try:
        area = (directory / 'area').read_text(encoding='utf-8').strip() or None
    except OSError:
        area = None
    try:
        lines = (directory / 'coop').read_text(encoding='utf-8', errors='replace').splitlines()
    except OSError:
        lines = []
    return area, [line.strip() for line in lines if line.strip()]


def activity(online, start, area=None, partners=()):
    """The area on the first line and the session on the second: "Co-op with <partners>",
    "Online" or "Offline". Before the game is in an area, the session alone."""
    session = (f'Co-op with {", ".join(partners)}' if partners
               else 'Online' if online else 'Offline')
    value = {
        'details': area_name(area) or session,
        'timestamps': {'start': start},
        'assets': {'large_image': 'bloodborne', 'large_text': 'Bloodborne · native Linux port'},
    }
    if area_name(area):
        value['state'] = session
    return value


def set_activity(sock, pid, value):
    sock.sendall(frame(FRAME, {'cmd': 'SET_ACTIVITY', 'args': {'pid': pid, 'activity': value},
                               'nonce': str(uuid.uuid4())}))
    op, reply = read_frame(sock)
    if reply.get('evt') == 'ERROR':
        raise ConnectionError(reply.get('data', {}).get('message', 'SET_ACTIVITY failed'))


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--pid', type=int, required=True, help='the game process: ends with it')
    parser.add_argument('--online', action='store_true')
    parser.add_argument('--presence-dir', help="the game's area and co-op partners")
    parser.add_argument('--retry', type=float, default=15.0, help='seconds between attempts')
    a = parser.parse_args()
    start = int(time.time())
    sock = None
    shown = None
    while alive(a.pid):
        value = activity(a.online, start, *read_state(a.presence_dir))
        if sock is None:
            sock = connect(CLIENT_ID)
            shown = None
        if sock is not None and value != shown:
            # Discord takes a few updates a minute; the area changes at loading screens only.
            try:
                set_activity(sock, a.pid, value)
                if shown is None:
                    print('Discord: Rich Presence on', flush=True)
                shown = value
            except (OSError, ConnectionError, ValueError) as error:
                print(f'Discord: {error}', flush=True)
                sock.close()
                sock = None
        elif sock is not None:
            # Discord closed or restarted: connect again on the next round.
            try:
                sock.settimeout(0)
                if sock.recv(1, socket.MSG_PEEK) == b'':
                    raise ConnectionError
            except BlockingIOError:
                pass
            except (OSError, ConnectionError):
                sock.close()
                sock = None
            if sock is not None:
                sock.settimeout(5)
        time.sleep(a.retry if sock is None else 2.0)
    if sock is not None:
        sock.close()


if __name__ == '__main__':
    main()
