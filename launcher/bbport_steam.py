# SPDX-License-Identifier: GPL-2.0-or-later
"""Adds the game to Steam as a non-Steam shortcut (Steam's userdata/<id>/config/shortcuts.vdf).
From the Windows launcher of Supermedo/bloodborne_pc; finding, closing and starting Steam are
Linux's here.

shortcuts.vdf is Valve's binary KeyValues: a type byte (0 = map, 1 = string, 2 = int32,
7 = uint64), a NUL-terminated key, then the value; 8 ends a map. The file holds one map,
"shortcuts", whose entries are maps named "0", "1", ...
"""
import os
from pathlib import Path
import shutil
import struct
import subprocess
import zlib

MAP, STRING, INT32, UINT64, END = 0, 1, 2, 7, 8


def _cstring(data, at):
    end = data.index(b'\0', at)
    return data[at:end].decode('utf-8', errors='replace'), end + 1


def parse(data, at=0):
    """A map as a list of (type, key, value); nested maps are lists too. Returns (items, next)."""
    items = []
    while at < len(data):
        kind = data[at]
        at += 1
        if kind == END:
            return items, at
        key, at = _cstring(data, at)
        if kind == MAP:
            value, at = parse(data, at)
        elif kind == STRING:
            value, at = _cstring(data, at)
        elif kind == INT32:
            value, at = struct.unpack_from('<i', data, at)[0], at + 4
        elif kind == UINT64:
            value, at = struct.unpack_from('<Q', data, at)[0], at + 8
        else:
            raise ValueError(f'unknown field type {kind} in shortcuts.vdf')
        items.append((kind, key, value))
    return items, at


def dump(items):
    out = bytearray()
    for kind, key, value in items:
        out += bytes([kind]) + key.encode('utf-8') + b'\0'
        if kind == MAP:
            out += dump(value) + bytes([END])
        elif kind == STRING:
            out += str(value).encode('utf-8') + b'\0'
        elif kind == INT32:
            out += struct.pack('<i', value)
        elif kind == UINT64:
            out += struct.pack('<Q', value)
    return bytes(out)


def shortcut_id(exe, name):
    """The id Steam gives a non-Steam game: CRC32 of the quoted exe and the name, top bit set."""
    return (zlib.crc32((exe + name).encode('utf-8')) & 0xffffffff) | 0x80000000


def entry(name, exe, start_dir, icon, options=''):
    quoted = f'"{exe}"'
    appid = shortcut_id(quoted, name)
    return [
        (INT32, 'appid', struct.unpack('<i', struct.pack('<I', appid))[0]),
        (STRING, 'AppName', name), (STRING, 'Exe', quoted), (STRING, 'StartDir', f'"{start_dir}"'),
        (STRING, 'icon', icon), (STRING, 'ShortcutPath', ''), (STRING, 'LaunchOptions', options),
        (INT32, 'IsHidden', 0), (INT32, 'AllowDesktopConfig', 1), (INT32, 'AllowOverlay', 1),
        (INT32, 'OpenVR', 0), (INT32, 'Devkit', 0), (STRING, 'DevkitGameID', ''),
        (INT32, 'DevkitOverrideAppID', 0), (INT32, 'LastPlayTime', 0), (STRING, 'FlatpakAppID', ''),
        (MAP, 'tags', []),
    ]


def add_shortcut(vdf_path, name, exe, start_dir, icon, options=''):
    """Adds the shortcut to one shortcuts.vdf, or updates the entry that starts the same exe or
    has the same name and options (this port from another place: a checkout, then the AppImage).
    Returns 'added' or 'updated'. A copy of the old file is kept as shortcuts.vdf.bak."""
    vdf_path = Path(vdf_path)
    data = vdf_path.read_bytes() if vdf_path.exists() else b''
    root = parse(data)[0] if data else []
    shortcuts = next((value for kind, key, value in root if kind == MAP and key.lower() == 'shortcuts'), None)
    if shortcuts is None:
        shortcuts = []
        root.append((MAP, 'shortcuts', shortcuts))
    new = entry(name, exe, start_dir, icon, options)
    target = f'"{exe}"'.lower()
    for index, (kind, key, value) in enumerate(shortcuts):
        fields = {k.lower(): v for _t, k, v in value} if kind == MAP else {}
        same_port = fields.get('appname') == name and fields.get('launchoptions') == options and options
        if str(fields.get('exe', '')).lower() == target or same_port:
            # Keep what Steam or the player added (play time, tags).
            kept = {k.lower() for k in ('LastPlayTime', 'tags')}
            old = {k.lower(): (t, k, v) for t, k, v in value}
            shortcuts[index] = (MAP, key, [old[k.lower()] if k.lower() in kept and k.lower() in old else (t, k, v)
                                            for t, k, v in new])
            result = 'updated'
            break
    else:
        shortcuts.append((MAP, str(len(shortcuts)), new))
        result = 'added'
    if data:
        vdf_path.with_name(vdf_path.name + '.bak').write_bytes(data)
    vdf_path.parent.mkdir(parents=True, exist_ok=True)
    vdf_path.write_bytes(dump(root) + bytes([END]))
    return result


def steam_folder():
    """Steam's data folder (the native package's; ~/.steam/steam links to it), or None."""
    home = Path.home()
    for path in (Path(os.environ.get('XDG_DATA_HOME', home / '.local/share')) / 'Steam',
                 home / '.steam/steam', home / '.steam/root'):
        if (path / 'userdata').is_dir():
            return path.resolve()
    return None


def user_configs(steam):
    """userdata/<account>/config folders of the accounts that used Steam on this PC."""
    users = Path(steam) / 'userdata'
    return [d / 'config' for d in sorted(users.iterdir()) if d.is_dir() and d.name.isdigit() and d.name != '0'] \
        if users.is_dir() else []


def steam_running():
    return subprocess.run(['pgrep', '-x', 'steam'], capture_output=True).returncode == 0


def steam_command():
    """The command that starts Steam, or None."""
    return shutil.which('steam')


def shutdown_steam():
    """Asks Steam to exit (it writes shortcuts.vdf as it goes, so it must be closed first)."""
    subprocess.Popen([steam_command(), '-shutdown'], stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)


def start_steam():
    """Starts Steam on its library, detached from the launcher."""
    subprocess.Popen([steam_command(), 'steam://open/games'], stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)


if __name__ == '__main__':  # self-test on a temporary file
    import tempfile
    with tempfile.TemporaryDirectory() as folder:
        vdf = Path(folder) / 'shortcuts.vdf'
        print(add_shortcut(vdf, 'Bloodborne', '/games/bb/launcher/bb-launcher.sh', '/games/bb', 'x.png', '--play'))
        print(add_shortcut(vdf, 'Other', '/other/o', '/other', ''))
        print(add_shortcut(vdf, 'Bloodborne', '/games/bb/launcher/bb-launcher.sh', '/games/bb', 'y.png', '--play'))
        print(add_shortcut(vdf, 'Bloodborne', '/apps/Bloodborne.AppImage', '/apps', 'y.png', '--play'))
        print(add_shortcut(vdf, 'Bloodborne', '/shadps4/shadps4', '/shadps4', '', 'CUSA03173'))
        root = parse(vdf.read_bytes())[0]
        print([[f for f in e[2] if f[1] in ('AppName', 'Exe')] for e in root[0][2]])
        assert len(root[0][2]) == 3
        assert dump(root) + bytes([END]) == vdf.read_bytes()
    print(os.path.basename(__file__), 'ok')
