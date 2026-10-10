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
"""
import argparse
import json
import os
from pathlib import Path
import re
import socket
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


def firewall_commands(firewall, gateway=None):
    """(open the co-op port, let the router's UPnP replies in or None) for a firewall."""
    if firewall == 'ufw':
        return (f'sudo ufw allow {P2P_PORT}/udp',
                f'sudo ufw allow from {gateway} proto udp' if gateway else None)
    return (f'sudo firewall-cmd --permanent --add-port={P2P_PORT}/udp && sudo firewall-cmd --reload',
            None)


def check(server, webapi, community):
    """(name, address, ok, detail) for the game server, the shadNet server and its WebAPI."""
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
        with urllib.request.urlopen(webapi.rstrip('/') + '/status', timeout=4) as reply:
            ok = b'"ok":true' in reply.read(512).replace(b' ', b'')
        results.append(('webapi', webapi, ok, '' if ok else 'not a shadNet server'))
    except (OSError, ValueError) as error:
        results.append(('webapi', webapi, False, str(error)))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = parser.add_subparsers(dest='command', required=True)
    overrides = sub.add_parser('overrides')
    overrides.add_argument('--user', required=True)
    sub.add_parser('check')
    a = parser.parse_args()
    server = os.environ.get('BB_SHADNET_SERVER') or SHADNET_SERVER
    community = community_address(os.environ.get('BB_COMMUNITY_SERVER'))
    webapi = webapi_setting(os.environ.get('BB_SHADNET_WEBAPI'), server, community)
    if a.command == 'overrides':
        print(write_overrides(a.user, community, webapi))
    else:
        for name, address, ok, detail in check(server, webapi, community):
            print(f'{name}: {address}: {"reachable" if ok else "not reachable"} {detail}'.rstrip())


if __name__ == '__main__':
    main()
