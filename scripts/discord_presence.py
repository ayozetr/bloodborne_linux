#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Discord Rich Presence while the game runs: "Playing Bloodborne", online or offline, with the
time played. run.sh starts it next to the game (BB_DISCORD=0 turns it off); it ends with the game.

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


def activity(online, start):
    return {
        'details': 'Online' if online else 'Offline',
        'timestamps': {'start': start},
        'assets': {'large_image': 'bloodborne', 'large_text': 'Bloodborne · native Linux port'},
    }


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
    parser.add_argument('--retry', type=float, default=15.0, help='seconds between attempts')
    a = parser.parse_args()
    start = int(time.time())
    sock = None
    while alive(a.pid):
        if sock is None:
            sock = connect(CLIENT_ID)
            if sock is not None:
                try:
                    set_activity(sock, a.pid, activity(a.online, start))
                    print('Discord: Rich Presence on', flush=True)
                except (OSError, ConnectionError, ValueError) as error:
                    print(f'Discord: {error}', flush=True)
                    sock.close()
                    sock = None
        else:
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
