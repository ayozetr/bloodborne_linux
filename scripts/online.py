#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Co-op addresses (BB_ONLINE=1): the game's own server, the shadNet server and its WebAPI.

From run.py and the launcher of the Windows port (Supermedo/bloodborne_pc). Messages,
bloodstains and ghosts come from the community game server (The Hunter's Dream by default);
bells and summons go through a shadNet server (shadPS4's public one by default).

`online.py overrides --user DIR` writes DIR/host_overrides.json for this launch (the game's
server -> the community server; summon signs -> the shadNet WebAPI when it has the Bloodborne
summon service) and prints its path for SHADPS4_HTTP_HOST_OVERRIDES_JSON. A player who needs
other addresses puts them in DIR/host_overrides.custom.json, which is then used as it is.
`online.py check` tests the servers, the shadNet server's UDP port included (docs/SERVER.md).

The Hunter's Dream's co-op pool (online_server_kind "thd"), with bbhost's players: bbbridge
(bbbridge/, by MaskZeus) stands in for the shadNet server on this PC and talks to The Hunter's
Dream as bbhost does; its account is a Discord sign-in. `online.py bridge --user DIR` writes the
bridge's config and the game's overrides for it into DIR/bbbridge and prints both paths.
"""
import argparse
import json
import os
from pathlib import Path
import re
import socket
import struct
import subprocess
import sys
import urllib.error
import urllib.request

COMMUNITY_SERVER = 'https://thehuntersdream.com'
SHADNET_SERVER = 'srv.shadps4.net:31313'
# Bloodborne's own game server, answered by the community server on the same port.
GAME_SERVER = 'https://ss4.scej-network.jp:20443'
# The server's ss.info sends the game to this port for its API (summons among them).
COMMUNITY_API_PORT = 18671


# The shadNet server's UDP port (shadnet.cfg MatchingUdpPort): the game pings it to learn its public
# address, which the server hands to the other player of a summon.
STUN_PORT = 31314
# The online ID of the connection test's ping: the server keeps one address per online ID, and the
# player's own would replace the address of a game running meanwhile.
STUN_TEST_ID = b'bbport-udp-test'


def community_address(value):
    """The game server as https://host (the game picks the ports), The Hunter's Dream by default."""
    value = str(value or '').strip() or COMMUNITY_SERVER
    scheme, _sep, rest = value.rpartition('://')
    host = rest.split('/')[0].split(':')[0]
    return f'{scheme or "https"}://{host}'


def webapi_address(server):
    """The shadNet WebAPI of a server address host:port (the server's default port 31315)."""
    server = str(server or '').strip() or SHADNET_SERVER
    host = server.rsplit(':', 1)[0] if server.count(':') == 1 else server
    return f'http://{host}:31315'


def webapi_setting(webapi, server, community):
    """The WebAPI field, unless it holds the game server's address (a common mix-up): then the
    shadNet server's own WebAPI."""
    webapi = str(webapi or '').strip()
    community_host = community_address(community).split('://', 1)[1]
    if webapi and community_host in webapi:
        webapi = ''
    return webapi or webapi_address(server)


def server_kind(settings):
    """'public' (shadPS4's server) or 'own'; settings from before the choice existed are 'own'
    when they name another server."""
    kind = settings.get('online_server_kind')
    if kind in ('public', 'own', 'thd'):
        return kind
    server = str(settings.get('online_server') or '').strip()
    return 'own' if server and server != SHADNET_SERVER else 'public'


def account(settings, kind):
    """(online ID, password) kept for one kind of server: each has its own accounts, so the
    launcher keeps one for each (online_accounts). Settings from before that know only the one of
    the server chosen then."""
    kept = (settings.get('online_accounts') or {}).get(kind)
    if isinstance(kept, dict):
        return str(kept.get('npid') or ''), str(kept.get('password') or '')
    if kind == server_kind(settings):
        return str(settings.get('online_npid') or ''), str(settings.get('online_password') or '')
    return '', ''


def addresses(settings):
    """(shadNet server, WebAPI, game server) for the launcher's settings. A server without a port
    gets shadNet's 31313; shadPS4's public server ignores the WebAPI field."""
    community = community_address(settings.get('online_community'))
    server = str(settings.get('online_server') or '').strip()
    if server_kind(settings) == 'public' or not server:
        return SHADNET_SERVER, webapi_address(SHADNET_SERVER), community
    if ':' not in server:
        server += ':31313'
    return server, webapi_setting(settings.get('online_webapi'), server, community), community


def environment(settings):
    """The game's online variables (run.sh and the online module) for the launcher's settings."""
    if server_kind(settings) == 'thd':
        # bbbridge on this PC (run.sh starts it): the online ID is the Discord sign-in's.
        return {
            'BB_ONLINE': '1',
            'BB_BRIDGE': '1',
            'BB_SHADNET_SERVER': BRIDGE_SERVER,
            'BB_SHADNET_WEBAPI': BRIDGE_WEBAPI,
            'BB_SHADNET_NPID': str(settings.get('online_npid') or '').strip(),
            'BB_SHADNET_PASSWORD': BRIDGE_PASSWORD,
            'BB_UPNP': '0',   # the bridge's gateway talks to the internet, not the game
            'BB_COMMUNITY_SERVER': COMMUNITY_SERVER,
            'SHADPS4_P2P_PORT': str(BRIDGE_P2P_PORT),
        }
    server, webapi, community = addresses(settings)
    env = {
        'BB_ONLINE': '1',
        'BB_SHADNET_SERVER': server,
        'BB_SHADNET_WEBAPI': webapi,
        'BB_SHADNET_NPID': str(settings.get('online_npid') or '').strip(),
        'BB_SHADNET_PASSWORD': settings.get('online_password') or '',
        'BB_UPNP': '1' if settings.get('online_upnp', True) else '0',
        'BB_COMMUNITY_SERVER': community,
    }
    port = int(settings.get('online_p2p_port') or 0)
    if 0 < port < 65536:
        env['SHADPS4_P2P_PORT'] = str(port)
    # Summons through the server's WebAPI (http.cpp); the server needs BloodborneSeamlessCoop=true.
    if server_kind(settings) == 'own' and settings.get('online_seamless'):
        env['SHADPS4_BLOODBORNE_SEAMLESS_COOP'] = '1'
    return env


def stun_ping(host, port=STUN_PORT, timeout=2.0, attempts=3):
    """The public (address, port) the shadNet server sees for this computer, from the ping the
    game sends it (np_signaling_helpers.cpp: a 0xffff signaling header, command 1, the online ID
    and the local address); OSError, TimeoutError when nothing answers."""
    ping = b'\xff\xff\xff\xff' + b'\x01' + STUN_TEST_ID.ljust(16, b'\0') + bytes(4)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        address = socket.gethostbyname(host)
        for _ in range(attempts):
            sock.sendto(ping, (address, port))
            try:
                reply, sender = sock.recvfrom(64)
            except TimeoutError:
                continue
            if sender[0] == address and len(reply) == 10 and reply[:4] == b'\xff' * 4:
                return socket.inet_ntoa(reply[4:8]), struct.unpack('!H', reply[8:10])[0]
        raise TimeoutError(f'no answer from {host}:{port} (UDP)')


def summon_service(webapi):
    """True when a shadNet WebAPI answers Bloodborne's summon calls: the route exists there
    (an empty request is refused with 400), where other servers answer 404."""
    request = urllib.request.Request(webapi.rstrip('/') + '/summon_messenger/create', data=b'',
                                     method='POST')
    try:
        urllib.request.urlopen(request, timeout=4).close()
        return True
    except urllib.error.HTTPError as error:
        return error.code != 404
    except (OSError, ValueError):
        return False


def write_overrides(user_dir, community, webapi):
    """The host overrides file for this launch; returns its path."""
    user_dir = Path(user_dir)
    user_dir.mkdir(parents=True, exist_ok=True)
    custom = user_dir / 'host_overrides.custom.json'
    if custom.exists():
        print(f'Co-op: addresses from {custom}', file=sys.stderr)
        return custom
    community = community_address(community)
    host = community.split('://', 1)[1]
    overrides = {GAME_SERVER: community}
    if summon_service(webapi):
        overrides.update({f'{scheme}://{host}:{COMMUNITY_API_PORT}/summon_messenger': webapi
                          for scheme in ('https', 'http')})
        print(f'Co-op: summon signs through {webapi}', file=sys.stderr)
    else:
        print(f'Co-op: {webapi} has no summon service; summon signs through {community}',
              file=sys.stderr)
    path = user_dir / 'host_overrides.json'
    path.write_text(json.dumps(overrides, indent=2) + '\n', encoding='utf-8')
    return path


# The co-op port the launcher suggests pinning (SHADPS4_P2P_PORT) and opening.
P2P_PORT = 3658

# bbbridge on this PC: its shadNet port, its WebAPI and its two game-server proxies (bbbridge's
# setup.cpp, overrides()). The game's play log (FromSoftware's telemetry, which feeds The Hunter's
# Dream's live map through the bridge) stays blocked (gpu/bbnet net_util.cpp), so it is not here.
BRIDGE_SERVER = '127.0.0.1:31313'
BRIDGE_WEBAPI = 'http://127.0.0.1:31315'
BRIDGE_P2P_PORT = 3658   # the game's P2P port, as the bridge's gateway expects it
BRIDGE_OVERRIDES = {
    GAME_SERVER: 'http://127.0.0.1:31316',
    f'https://thehuntersdream.com:20443': 'http://127.0.0.1:31316',
    f'https://thehuntersdream.com:{COMMUNITY_API_PORT}': 'http://127.0.0.1:31317',
    f'http://thehuntersdream.com:{COMMUNITY_API_PORT}': 'http://127.0.0.1:31317',
    f'https://thehuntersdream.com:{COMMUNITY_API_PORT}/summon_messenger': BRIDGE_WEBAPI,
    f'http://thehuntersdream.com:{COMMUNITY_API_PORT}/summon_messenger': BRIDGE_WEBAPI,
}
# The game signs in to the bridge with a password, which the bridge never reads.
BRIDGE_PASSWORD = 'bbbridge'


def bridge_dir(user_dir):
    return Path(user_dir) / 'bbbridge'


def bridge_accounts(user_dir):
    """The Hunter's Dream online IDs signed in on this PC (bbbridge's account file)."""
    try:
        state = json.loads((bridge_dir(user_dir) / 'bbbridge_state.json').read_text(encoding='utf-8'))
        return [name for name in state.get('accounts', {}) if isinstance(name, str)]
    except (OSError, ValueError, AttributeError):
        return []


def bridge_recovery_code(user_dir, name):
    """The recovery code of an account created on this PC (none for a Discord sign-in)."""
    try:
        state = json.loads((bridge_dir(user_dir) / 'bbbridge_state.json').read_text(encoding='utf-8'))
        return str(state['accounts'][name].get('recovery_code') or '')
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return ''


def write_bridge_files(user_dir):
    """DIR/bbbridge/bbbridge_config.json (the account file next to it; other keys a player added
    stay) and the game's host overrides for the bridge. Returns (config, overrides)."""
    folder = bridge_dir(user_dir)
    folder.mkdir(parents=True, exist_ok=True)
    config = folder / 'bbbridge_config.json'
    try:
        current = json.loads(config.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        current = {}
    if not isinstance(current, dict):
        current = {}
    wanted = {**current, 'state_file': str(folder / 'bbbridge_state.json')}
    if wanted != current:
        config.write_text(json.dumps(wanted, indent=2) + '\n', encoding='utf-8')
    overrides = folder / 'host_overrides.json'
    overrides.write_text(json.dumps(BRIDGE_OVERRIDES, indent=2) + '\n', encoding='utf-8')
    return config, overrides


def active_firewalls(ufw_conf=Path('/etc/ufw/ufw.conf'), systemctl='/usr/bin/systemctl'):
    """Firewalls that drop unrequested incoming UDP by default, read without root: ufw when its
    configuration enables it, firewalld when its service runs. The host's systemctl runs without
    the AppImage's library paths."""
    found = []
    try:
        if re.search(r'^\s*ENABLED\s*=\s*yes', ufw_conf.read_text(errors='replace'), re.M):
            found.append('ufw')
    except OSError:
        pass
    try:
        env = {k: v for k, v in os.environ.items() if k not in ('LD_LIBRARY_PATH', 'LD_PRELOAD')}
        if subprocess.run([systemctl, 'is-active', '--quiet', 'firewalld'], env=env,
                          timeout=3).returncode == 0:
            found.append('firewalld')
    except (OSError, subprocess.SubprocessError):
        pass
    return found


def default_gateway(route=Path('/proc/net/route')):
    """The IPv4 default gateway (the router, which answers UPnP), or None."""
    try:
        for line in route.read_text().splitlines()[1:]:
            fields = line.split()
            if len(fields) > 2 and fields[1] == '00000000' and fields[2] != '00000000':
                return socket.inet_ntoa(int(fields[2], 16).to_bytes(4, 'little'))
    except (OSError, ValueError):
        pass
    return None


def firewall_commands(firewall, gateway=None, port=P2P_PORT):
    """(open the co-op port, let the router's UPnP replies in or None) for a firewall."""
    if firewall == 'ufw':
        return (f'sudo ufw allow {port}/udp',
                f'sudo ufw allow from {gateway} proto udp' if gateway else None)
    return (f'sudo firewall-cmd --permanent --add-port={port}/udp && sudo firewall-cmd --reload',
            None)


# shadNet's TCP protocol (gpu/bbnet/shadps4/shadnet/client.h): a 15-byte header (packet type u8,
# command u16, total size u32, packet id u64, little endian); the server greets with ServerInfo
# (its protocol version, u32) and answers Login with an error byte. srv.shadps4.net answers 8 for
# an unknown name as well as for a wrong password.
SHADNET_HEADER = struct.Struct('<BHIQ')
SHADNET_PROTOCOL = 1
LOGIN_ERRORS = {5: 'error', 6: 'already signed in', 7: 'no such account',
                8: 'wrong name or password', 9: 'wrong token'}


def proto_string(field, text):
    data = text.encode()
    length, varint = len(data), bytearray()
    while True:
        varint.append(length & 0x7f | (0x80 if length > 0x7f else 0))
        length >>= 7
        if not length:
            return bytes([field << 3 | 2]) + bytes(varint) + data


def shadnet_login(host, port, npid, password, timeout=6.0):
    """Signs in to a shadNet server as the game does and leaves at once: (ok, detail), detail an
    entry of LOGIN_ERRORS, 'protocol vN' or the socket error."""
    def receive(sock, size):
        data = b''
        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                raise ConnectionError('the server closed the connection')
            data += chunk
        return data

    def packet(sock):
        kind, command, total, _id = SHADNET_HEADER.unpack(receive(sock, SHADNET_HEADER.size))
        if not SHADNET_HEADER.size <= total <= 0x800000:
            raise ConnectionError('not a shadNet server')
        return kind, command, receive(sock, total - SHADNET_HEADER.size)

    with socket.create_connection((host, port), timeout=timeout) as sock:
        kind, _command, payload = packet(sock)
        if kind != 3:
            raise ConnectionError('not a shadNet server')
        version = struct.unpack_from('<I', payload)[0] if len(payload) >= 4 else SHADNET_PROTOCOL
        if version != SHADNET_PROTOCOL:
            return False, f'protocol v{version}'
        request = (proto_string(1, npid) + proto_string(2, password) +
                   proto_string(4, 'CUSA00900') + proto_string(5, 'Bloodborne'))
        body = struct.pack('<I', len(request)) + request
        sock.sendall(SHADNET_HEADER.pack(0, 0, SHADNET_HEADER.size + len(body), 1) + body)
        while True:  # notifications may come first
            kind, command, payload = packet(sock)
            if kind == 1 and command == 0:
                error = payload[0] if payload else 1
                return error == 0, LOGIN_ERRORS.get(error, f'code {error}') if error else ''


def check(server, webapi, community, account=None):
    """(name, address, ok, detail) for the game server, the shadNet server, its UDP port (detail:
    the public address it sees, or 'timeout'), its WebAPI, and with account (npid, password) the
    sign-in (detail: an entry of LOGIN_ERRORS, or why it could not be tried)."""
    results = []
    try:
        with urllib.request.urlopen(community + ':20443/bb-eu/ss.info', timeout=6) as reply:
            reply.read(64)
        results.append(('game', community, True, ''))
    except (OSError, ValueError) as error:
        results.append(('game', community, False, str(error)))
    host, _sep, port = server.rpartition(':')
    try:
        socket.create_connection((host or server, int(port or 31313)), timeout=4).close()
        results.append(('shadnet', server, True, ''))
    except (OSError, ValueError) as error:
        results.append(('shadnet', server, False, str(error)))
    try:
        public, public_port = stun_ping(host or server)
        results.append(('stun', f'{host or server}:{STUN_PORT}', True, f'{public}:{public_port}'))
    except TimeoutError:
        results.append(('stun', f'{host or server}:{STUN_PORT}', False, 'timeout'))
    except OSError as error:
        results.append(('stun', f'{host or server}:{STUN_PORT}', False, str(error)))
    try:
        with urllib.request.urlopen(webapi.rstrip('/') + '/status', timeout=4) as reply:
            ok = b'"ok":true' in reply.read(512).replace(b' ', b'')
        results.append(('webapi', webapi, ok, '' if ok else 'not a shadNet server'))
    except (OSError, ValueError) as error:
        results.append(('webapi', webapi, False, str(error)))
    npid, password = account or ('', '')
    if npid and password and results[1][2]:
        try:
            ok, detail = shadnet_login(host or server, int(port or 31313), npid, password)
            results.append(('login', npid, ok, detail))
        except (OSError, ValueError) as error:
            results.append(('login', npid, False, str(error)))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = parser.add_subparsers(dest='command', required=True)
    overrides = sub.add_parser('overrides')
    overrides.add_argument('--user', required=True)
    bridge = sub.add_parser('bridge')
    bridge.add_argument('--user', required=True)
    sub.add_parser('check')
    a = parser.parse_args()
    server = os.environ.get('BB_SHADNET_SERVER') or SHADNET_SERVER
    community = community_address(os.environ.get('BB_COMMUNITY_SERVER'))
    webapi = webapi_setting(os.environ.get('BB_SHADNET_WEBAPI'), server, community)
    if a.command == 'bridge':
        config, overrides = write_bridge_files(a.user)
        print(config)
        print(overrides)
    elif a.command == 'overrides':
        print(write_overrides(a.user, community, webapi))
    else:
        for name, address, ok, detail in check(server, webapi, community):
            print(f'{name}: {address}: {"reachable" if ok else "not reachable"} {detail}'.rstrip())


if __name__ == '__main__':
    main()
