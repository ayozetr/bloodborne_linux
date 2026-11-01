#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Co-op addresses (BB_ONLINE=1): the game's own server, the shadNet server and its WebAPI.

From run.py and the launcher of the Windows port of bbport. Messages,
bloodstains and ghosts come from the community game server; bells and summons go through a shadNet
server. By default both are Seamless Hunt's (play.seamlesshunt.com, BBSC's server): shadPS4's public
shadNet (srv.shadps4.net) accepts only shadPS4's own builds since 2026-10-12.

`online.py bbsc-local` (BB_BBSC=1): prints the shadNet host when BBSC's game server should run on
this PC (scripts/bbsc_gameserver, started by run.sh): BB_BBSC_LOCAL_SERVER=1, or =auto (default)
when the server's own game server does not answer (its ss.info on port 20443 timed out for players
while the rest worked; the local one serves ss.info and sends summons to the shadNet server, as
BBSC's players do). Nothing printed: the server's game server is used.

`online.py overrides --user DIR` writes DIR/host_overrides.json for this launch (the game's
server -> the community server; summon signs -> the shadNet WebAPI when it has the Bloodborne
summon service) and prints its path for SHADPS4_HTTP_HOST_OVERRIDES_JSON. A player who needs
other addresses puts them in DIR/host_overrides.custom.json, which is then used as it is.

The launcher's Online tab (launcher/bbport_launcher.py) takes its settings from here too: the kind
of server (Seamless Hunt, an own one or The Hunter's Dream), one account for each, the game's
online variables (environment), the connection test with the sign-in, shadNet's account
registration and the firewall's advice; by way of the Linux fork.
"""
import argparse
import bbsc
import json
from pathlib import Path
import os
import re
import socket
import ssl
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request

COMMUNITY_SERVER = 'http://play.seamlesshunt.com'
SHADNET_SERVER = 'play.seamlesshunt.com:31313'
WEBAPI_SERVER = 'http://play.seamlesshunt.com:31315'
# The defaults before 2026-10-15 (the launcher replaces them in saved settings).
OLD_DEFAULTS = {
    'online_server': ('srv.shadps4.net:31313',),
    'online_community': ('https://thehuntersdream.com', ''),
    'online_webapi': ('',),
}
# Bloodborne's own game server, answered by the community server on the same port.
GAME_SERVER = 'https://ss4.scej-network.jp:20443'
# The server's ss.info sends the game to this port for its API (summons among them).
COMMUNITY_API_PORT = 18671
# Seamless Hunt's game server (its ss.info sends the game to the address). Its bloodstains and
# death visions (tomb_messenger/message_area) crash the game with "Transaction failed" on Windows and
# Linux alike (the Linux fork's issue #10): its own BBSC package sends those two requests nowhere by
# default, so they fail and the game goes on without them. BB_SEAMLESSHUNT_TOMBS=1 (the launcher)
# keeps them.
SEAMLESSHUNT_HOSTS = ('play.seamlesshunt.com', '199.195.193.131')
# Its servers, for the launcher's "Seamless Hunt" choice (online_server_kind "seamlesshunt"), as its
# guide sets them up (install.seamlesshunt.com/bbport.html): shadNet, the WebAPI, the game server.
SEAMLESSHUNT_SERVER = SHADNET_SERVER
SEAMLESSHUNT_WEBAPI = WEBAPI_SERVER
SEAMLESSHUNT_GAME = COMMUNITY_SERVER
SEAMLESSHUNT_TOMBS = '/tomb_messenger/message_area'
NOWHERE = 'http://127.0.0.1:9'


# The shadNet server's UDP port (shadnet.cfg MatchingUdpPort): the game pings it to learn its public
# address, which the server hands to the other player of a summon.
STUN_PORT = 31314
# The online ID of the connection test's ping: the server keeps one address per online ID, and the
# player's own would replace the address of a game running meanwhile.
STUN_TEST_ID = b'bbport-udp-test'
# The shadPS4 team's server frames UDP as a PS4 P2P datagram (p2p_sockets.cpp).
SERVER_SIGNALING_HEADER = bytes([0xFF, 0x83, 0xFF, 0xFF, 0xFF, 0xFF])


def community_address(value, probe=False):
    """The game server as scheme://host (the game picks the ports), Seamless Hunt by default.
    Without a scheme: https, but http for the default server's host (it serves plain http), or
    with probe whatever the host's port 20443 speaks: some servers answer the game in plain http."""
    value = str(value or '').strip() or COMMUNITY_SERVER
    scheme, _sep, rest = value.rpartition('://')
    host = rest.split('/')[0].split(':')[0]
    default_scheme, _sep, default_host = COMMUNITY_SERVER.partition('://')
    if not scheme and host == default_host:
        scheme = default_scheme
    if not scheme and probe:
        scheme = community_scheme(host)
    return f'{scheme or "https"}://{host}'


def community_scheme(host):
    """'http' when the host's port 20443 refuses a TLS handshake, else 'https' (unreachable too)."""
    try:
        with socket.create_connection((host, 20443), timeout=4) as sock:
            ssl.create_default_context().wrap_socket(sock, server_hostname=host).close()
    except ssl.SSLCertVerificationError:
        return 'https'
    except ssl.SSLError:
        return 'http'
    except OSError:
        pass
    return 'https'


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


def stored_kind(settings):
    """The kind of server the settings name: 'public' (shadPS4's server), 'own', 'seamlesshunt' or
    'thd'; settings from before the choice existed are 'own' when they name another server."""
    kind = settings.get('online_server_kind')
    if kind in ('public', 'own', 'seamlesshunt', 'thd'):
        return kind
    server = str(settings.get('online_server') or '').strip()
    return 'own' if server and server not in (SHADNET_SERVER, *OLD_DEFAULTS['online_server']) else 'public'


def server_kind(settings):
    """The kind of server the game uses: 'own', 'seamlesshunt' or 'thd'. shadPS4's public server
    signs this port's builds out since 2026-10-12 (upstream docs/BBSC.md), so settings that chose
    it, or chose nothing yet, get Seamless Hunt."""
    kind = stored_kind(settings)
    return 'seamlesshunt' if kind == 'public' else kind


def account(settings, kind):
    """(online ID, password) kept for one kind of server: each has its own accounts, so the
    launcher keeps one for each (online_accounts). Settings from before that know only the one of
    the server chosen then: the public server's is not Seamless Hunt's."""
    kept = (settings.get('online_accounts') or {}).get(kind)
    if isinstance(kept, dict):
        return str(kept.get('npid') or ''), str(kept.get('password') or '')
    if kind == stored_kind(settings):
        return str(settings.get('online_npid') or ''), str(settings.get('online_password') or '')
    return '', ''


def addresses(settings):
    """(shadNet server, WebAPI, game server) for the launcher's settings. A server without a port
    gets shadNet's 31313; an own server without an address is Seamless Hunt (the launcher does not
    start the game with one)."""
    server = str(settings.get('online_server') or '').strip()
    if server_kind(settings) == 'seamlesshunt' or not server:
        return SEAMLESSHUNT_SERVER, SEAMLESSHUNT_WEBAPI, SEAMLESSHUNT_GAME
    community = community_address(settings.get('online_community'), probe=True)
    if ':' not in server:
        server += ':31313'
    return server, webapi_setting(settings.get('online_webapi'), server, community), community


def environment(settings):
    """The game's online variables (run.sh and the online module) for the launcher's settings."""
    if server_kind(settings) == 'thd':
        # The online module talks to The Hunter's Dream itself (BB_NET_BACKEND=thd, bbhost's
        # protocol); the account is the Discord sign-in's token. No BBSC there.
        return {
            'BB_ONLINE': '1',
            'BB_NET_BACKEND': 'thd',
            'BB_COMMUNITY_SERVER': thd_base(settings.get('thd_server')),
            'BB_THD_ONLINE_ID': str(settings.get('thd_online_id') or ''),
            'BB_THD_TOKEN': str(settings.get('thd_token') or ''),
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
        'BB_SEAMLESSHUNT_TOMBS': '1' if settings.get('online_seamlesshunt_tombs') else '0',
    }
    port = int(settings.get('online_p2p_port') or 0)
    if 0 < port < 65536:
        env['BB_P2P_PORT'] = str(port)
    # Summons through the server's WebAPI (http.cpp); the server needs BloodborneSeamlessCoop=true.
    if server_kind(settings) == 'own' and settings.get('online_seamless'):
        env['SHADPS4_BLOODBORNE_SEAMLESS_COOP'] = '1'
    # Seamless co-op (BBSC, gpu/bbnet20/bbsc), on Seamless Hunt or an own server.
    if settings.get('bbsc', True):
        env['BB_BBSC'] = '1'
        env.update(bbsc.environment(settings))  # the options the player changed
    return env


def stun_ping(host, port=STUN_PORT, timeout=2.0, attempts=3):
    """The public (address, port) the shadNet server sees for this computer, from the ping the
    game sends it (np_signaling_helpers.cpp: command 1, the online ID and the local address);
    OSError, TimeoutError when nothing answers. Sent in both framings, as the game does
    (p2p_sockets.cpp): the 0xffff vport header for shadp2p servers (our own), and the PS4 P2P
    datagram header the shadPS4 team's server (srv.shadps4.net) takes; each drops the other."""
    body = b'\x01' + STUN_TEST_ID.ljust(16, b'\0') + bytes(4)
    headers = (b'\xff\xff\xff\xff', SERVER_SIGNALING_HEADER)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        address = socket.gethostbyname(host)
        for _ in range(attempts):
            for header in headers:
                sock.sendto(header + body, (address, port))
            try:
                reply, sender = sock.recvfrom(64)
            except TimeoutError:
                continue
            for header in headers:
                if sender[0] == address and len(reply) == len(header) + 6 and reply.startswith(header):
                    found = reply[len(header):]
                    return socket.inet_ntoa(found[:4]), struct.unpack('!H', found[4:6])[0]
        raise TimeoutError(f'no answer from {host}:{port} (UDP)')


def summon_service(webapi):
    """True when a shadNet WebAPI answers Bloodborne's summon calls: the route exists there
    (an empty request is refused with 400), where other servers answer 404."""
    if not webapi:
        return False
    request = urllib.request.Request(webapi.rstrip('/') + '/summon_messenger/create', data=b'',
                                     headers={'User-Agent': 'Bloodborne/01.09'}, method='POST')
    try:
        urllib.request.urlopen(request, timeout=4).close()
        return True
    except urllib.error.HTTPError as error:
        return error.code != 404
    except (OSError, ValueError):
        return False


def write_overrides(user_dir, community, webapi, plain=False, tombs=False):
    """The host overrides file for this launch; returns its path. tombs: Seamless Hunt's
    bloodstains and death visions too (SEAMLESSHUNT_TOMBS)."""
    user_dir = Path(user_dir)
    user_dir.mkdir(parents=True, exist_ok=True)
    custom = user_dir / 'host_overrides.custom.json'
    if custom.exists():
        print(f'Co-op: addresses from {custom}', file=sys.stderr)
        return custom
    community = community_address(community)
    host = community.split('://', 1)[1]
    overrides = {GAME_SERVER: community}
    if plain:
        # The shadPS4 0.20 module: the game server only; summons stay on shadNet.
        print(f'Co-op: game server {community}', file=sys.stderr)
    elif summon_service(webapi):
        overrides.update({f'{scheme}://{host}:{COMMUNITY_API_PORT}/summon_messenger': webapi
                          for scheme in ('https', 'http')})
        print(f'Co-op: summon signs through {webapi}', file=sys.stderr)
    else:
        print(f'Co-op: {webapi} has no summon service; summon signs through {community}',
              file=sys.stderr)
    if host in SEAMLESSHUNT_HOSTS and not tombs:
        overrides.update({f'http://{name}:20443{SEAMLESSHUNT_TOMBS}': NOWHERE
                          for name in SEAMLESSHUNT_HOSTS})
        print('Co-op: Seamless Hunt\'s bloodstains and death visions are off (they crash the game)',
              file=sys.stderr)
    path = user_dir / 'host_overrides.json'
    path.write_text(json.dumps(overrides, indent=2) + '\n', encoding='utf-8')
    return path


# The co-op port the launcher suggests pinning (BB_P2P_PORT, the online module's default) and opening.
P2P_PORT = 3658

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


# shadNet's TCP protocol (gpu/bbnet20/vendor/shadps4/shadnet/client.h): a 15-byte header (packet type u8,
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


def shadnet_request(host, port, command, request, timeout=6.0):
    """Sends one request to a shadNet server as the game does and leaves at once: its error byte
    (0: done), or None when the server speaks another protocol version (then ConnectionError
    for one that is no shadNet server, OSError for the socket)."""
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
            raise ConnectionError(f'protocol v{version}')
        body = struct.pack('<I', len(request)) + request
        sock.sendall(SHADNET_HEADER.pack(0, command, SHADNET_HEADER.size + len(body), 1) + body)
        while True:  # notifications may come first
            kind, reply, payload = packet(sock)
            if kind == 1 and reply == command:
                return payload[0] if payload else 1


def shadnet_login(host, port, npid, password, timeout=6.0):
    """Signs in to a shadNet server as the game does and leaves at once: (ok, detail), detail an
    entry of LOGIN_ERRORS, 'protocol vN' or the socket error."""
    request = (proto_string(1, npid) + proto_string(2, password) +
               proto_string(4, 'CUSA00900') + proto_string(5, 'Bloodborne'))
    try:
        error = shadnet_request(host, port, 0, request, timeout)
    except ConnectionError as failure:
        if str(failure).startswith('protocol v'):
            return False, str(failure)
        raise
    return error == 0, LOGIN_ERRORS.get(error, f'code {error}') if error else ''


# The server's answers to RegistrationRequest (client.h, ErrorType).
REGISTER_ERRORS = {3: 'invalid name, password or email', 10: 'error',
                   11: 'the name is taken', 12: 'email provider not allowed',
                   13: 'the email is taken', 23: 'the server needs its registration key'}


def shadnet_register(host, port, npid, password, email='', key='', timeout=6.0):
    """Makes an account on a shadNet server (shadnet-sample's register): (ok, detail), detail an
    entry of REGISTER_ERRORS. Servers want one email per account; none given, one is made from
    the name, as Seamless Hunt's account tool does (the address is not checked)."""
    request = (proto_string(1, npid) + proto_string(2, password) +
               proto_string(4, email or f'{npid}@bbsc.local') + (proto_string(5, key) if key else b''))
    error = shadnet_request(host, port, 2, request, timeout)
    return error == 0, REGISTER_ERRORS.get(error, f'code {error}') if error else ''


def check(server, webapi, community, account=None):
    """(name, address, ok, detail) for the game server, the shadNet server, its UDP port (detail:
    the public address it sees, or 'timeout'), its WebAPI, and with account (npid, password) the
    sign-in (detail: an entry of LOGIN_ERRORS, or why it could not be tried)."""
    results = []
    try:
        game_url = community if (':20443' in community) else f"{community.rstrip('/')}:20443"
        req = urllib.request.Request(f'{game_url}/bb-eu/ss.info',
                                     headers={'User-Agent': 'Bloodborne/01.09'})
        with urllib.request.urlopen(req, timeout=6) as reply:
            reply.read(64)
        results.append(('game', community, True, ''))
    except urllib.error.HTTPError:
        results.append(('game', community, True, ''))  # the server answered
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
        req = urllib.request.Request(webapi.rstrip('/') + '/status',
                                     headers={'User-Agent': 'Bloodborne/01.09'})
        with urllib.request.urlopen(req, timeout=4) as reply:
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


# ---- The Hunter's Dream pool (BB_NET_BACKEND=thd, gpu/bbnet20/thd; bbhost's protocol) ------------

HUNTERS_DREAM_SERVER = 'https://thehuntersdream.com'
# The play logs the game sends to FromSoftware's old storage buckets go to the game server's API.
PLAY_LOG_HOSTS = ('bb-playlog-prod.s3.amazonaws.com', 'bb-playlog-test.s3.amazonaws.com')


def thd_base(value):
    """The Hunter's Dream's address as scheme://host (https unless a scheme is given)."""
    value = str(value or '').strip().rstrip('/') or HUNTERS_DREAM_SERVER
    if '://' not in value:
        value = 'https://' + value
    scheme, rest = value.split('://', 1)
    host_part = rest.split('/')[0]
    return f'{scheme}://{host_part}'


def thd_call(url, body):
    """A call to The Hunter's Dream's account service (bbhost's): its reply, or ValueError with the
    server's reason."""
    request = urllib.request.Request(url, data=json.dumps(body).encode(), method='POST',
                                     headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            text = response.read()
    except urllib.error.HTTPError as error:
        text = error.read()
    except (OSError, ValueError) as error:
        raise ValueError(f'{url}: {error}') from error
    try:
        reply = json.loads(text)
    except ValueError:
        reply = None
    if not isinstance(reply, dict) or 'ResKind' not in reply:
        raise ValueError(f'{url} has no account service')
    if reply['ResKind'] != 0:
        raise ValueError(reply.get('Message') or 'refused')
    return reply


def thd_sign_in(server, on_code, device='bbport', cancelled=lambda: False):
    """Discord sign-in the way bbhost does it: a code to approve on the website. on_code(page, code)
    shows it. Returns (online id, token); raises ValueError."""
    auth = thd_base(server)
    start = thd_call(auth + '/auth/device/start', {'DeviceName': device})
    code, user_code = start.get('DeviceCode', ''), start.get('UserCode', '')
    if not code or not user_code:
        raise ValueError('no code in the reply')
    interval = max(1, int(start.get('Interval') or 5))
    deadline = time.monotonic() + int(start.get('ExpiresIn') or 600)
    on_code(start.get('VerificationUri') or auth + '/link', user_code)
    while time.monotonic() < deadline:
        for _ in range(interval * 4):  # a cancel is noticed within a quarter of a second
            if cancelled():
                raise ValueError('cancelled')
            time.sleep(0.25)
        poll = thd_call(auth + '/auth/device/poll', {'DeviceCode': code})
        status = poll.get('Status')
        if status == 'approved':
            if not poll.get('OnlineId') or not poll.get('Token'):
                raise ValueError('no token in the reply')
            return poll['OnlineId'], poll['Token']
        if status == 'slow_down':
            interval += 5
        elif status == 'denied':
            raise ValueError('the sign-in was denied')
        elif status == 'expired':
            break
    raise ValueError('the code expired; try again')


def write_thd_overrides(user_dir, community):
    """The host overrides file for this launch (the game's servers and play logs -> The Hunter's
    Dream); returns (path, base address). host_overrides.custom.json is used as it is."""
    user_dir = Path(user_dir)
    user_dir.mkdir(parents=True, exist_ok=True)
    base = thd_base(community)
    custom = user_dir / 'host_overrides.custom.json'
    if custom.exists():
        print(f'Co-op: addresses from {custom}', file=sys.stderr)
        return custom, base
    overrides = {'*.scej-network.jp': base}
    overrides.update({host: f'{base}:{COMMUNITY_API_PORT}' for host in PLAY_LOG_HOSTS})
    path = user_dir / 'host_overrides.json'
    path.write_text(json.dumps(overrides, indent=2) + '\n', encoding='utf-8')
    print(f"Co-op: The Hunter's Dream {base}", file=sys.stderr)
    return path, base


def check_thd(community):
    """(name, address, ok, detail) for The Hunter's Dream's game server and co-op service."""
    base = thd_base(community)
    results = []
    for name, url in (('game', base + ':20443/bb-eu/ss.info'), ('service', base + f':{COMMUNITY_API_PORT}/')):
        try:
            urllib.request.urlopen(url, timeout=6).close()
            results.append((name, url.split('/')[2], True, ''))
        except urllib.error.HTTPError:
            results.append((name, url.split('/')[2], True, ''))  # it answered
        except (OSError, ValueError) as error:
            results.append((name, url.split('/')[2], False, str(error)))
    return results


def bbsc_local_server():
    """The shadNet host for a local BBSC game server, or '' (see the module's description)."""
    mode = os.environ.get('BB_BBSC_LOCAL_SERVER', 'auto').strip().lower()
    server = os.environ.get('BB_SHADNET_SERVER') or SHADNET_SERVER
    host = server.rsplit(':', 1)[0] if server.count(':') == 1 else server
    if mode in ('0', 'off', 'no'):
        return ''
    if mode in ('1', 'on', 'yes'):
        return host
    community = community_address(os.environ.get('BB_COMMUNITY_SERVER'))
    comm_host = community.split('://', 1)[1].split(':')[0]
    if comm_host in ('127.0.0.1', 'localhost'):
        return ''  # pointed at a local one already
    try:
        game_url = community if (':20443' in community) else f"{community.rstrip('/')}:20443"
        req = urllib.request.Request(f'{game_url}/bb-eu/ss.info',
                                     headers={'User-Agent': 'Bloodborne/01.09'})
        with urllib.request.urlopen(req, timeout=5) as reply:
            reply.read(64)
        return ''
    except urllib.error.HTTPError:
        # An HTTP status reply (even 403 or 401) confirms the server is reachable and running.
        return ''
    except (OSError, ValueError) as error:
        try:
            # Fallback: check if port 20443 is accepting TCP connections
            socket.create_connection((comm_host, 20443), timeout=3).close()
            return ''
        except (OSError, ValueError):
            pass
        print(f'Co-op: {community}:20443 does not answer ({error}): BBSC game server on this PC',
              file=sys.stderr)
        return host


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = parser.add_subparsers(dest='command', required=True)
    overrides = sub.add_parser('overrides')
    overrides.add_argument('--user', required=True)
    overrides.add_argument('--plain', action='store_true')
    sub.add_parser('check')
    thd = sub.add_parser('thd-overrides')
    thd.add_argument('--user', required=True)
    sub.add_parser('thd-check')
    sub.add_parser('thd-signin')
    sub.add_parser('bbsc-local')
    a = parser.parse_args()
    server = os.environ.get('BB_SHADNET_SERVER') or SHADNET_SERVER
    community = community_address(os.environ.get('BB_COMMUNITY_SERVER'))
    webapi = webapi_setting(os.environ.get('BB_SHADNET_WEBAPI'), server, community)
    if a.command == 'thd-overrides':
        path, base = write_thd_overrides(a.user, os.environ.get('BB_COMMUNITY_SERVER'))
        print(path)
        print(base)
        return
    if a.command == 'thd-check':
        for name, address, ok, detail in check_thd(os.environ.get('BB_COMMUNITY_SERVER')):
            print(f'{name}: {address}: {"reachable" if ok else "not reachable"} {detail}'.rstrip())
        return
    if a.command == 'thd-signin':
        try:
            name, token = thd_sign_in(os.environ.get('BB_COMMUNITY_SERVER'),
                                      lambda page, code: print(f'Open {page} and enter {code}',
                                                               file=sys.stderr, flush=True))
        except ValueError as error:
            sys.exit(f'The Hunter\'s Dream sign-in: {error}')
        print(name)
        print(token)
        return
    if a.command == 'bbsc-local':
        print(bbsc_local_server())
        return
    if a.command == 'overrides':
        print(write_overrides(a.user, community, webapi, a.plain,
                              os.environ.get('BB_SEAMLESSHUNT_TOMBS') == '1'))
    else:
        for name, address, ok, detail in check(server, webapi, community):
            print(f'{name}: {address}: {"reachable" if ok else "not reachable"} {detail}'.rstrip())


if __name__ == '__main__':
    main()
