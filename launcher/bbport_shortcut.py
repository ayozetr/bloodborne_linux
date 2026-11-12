# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""A desktop entry for the launcher: in the applications menu and on the desktop.

The AppImage has no menu entry of its own unless an AppImage manager (Gear Lever, AppImageLauncher)
makes one, and a checkout has launcher/install-desktop.sh. The launcher's "Create shortcut" writes
one for whichever it is: the AppImage itself, or the checkout's bb-launcher.sh.
"""
import os
import subprocess
from pathlib import Path

ENTRY_NAME = "io.github.ayozetr.bloodborne_linux.desktop"


def exec_quote(path):
    """`path` as one Exec argument (Desktop Entry Specification: double quotes, with ", `, $ and \\
    escaped)."""
    escaped = "".join("\\" + c if c in '"`$\\' else c for c in str(path))
    return f'"{escaped}"'


def entry_text(target, icon):
    """The desktop entry that starts `target` (the AppImage or bb-launcher.sh) with `icon`."""
    return ("[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Bloodborne (bbport)\n"
            "Comment=Native Linux port launcher for your own copy of Bloodborne\n"
            f"Exec={exec_quote(target)}\n"
            f"Icon={icon}\n"
            "Terminal=false\n"
            "Categories=Game;\n"
            "StartupWMClass=io.github.bbport.Launcher\n")


def applications_dir(env=os.environ):
    """Where the user's own menu entries go ($XDG_DATA_HOME/applications)."""
    data = env.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(data) / "applications"


def desktop_dir():
    """The desktop folder (xdg-user-dir DESKTOP: "Escritorio", "Bureau"...), else ~/Desktop."""
    try:
        out = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True,
                             timeout=5).stdout.strip()
        if out and Path(out).is_dir() and Path(out) != Path.home():
            return Path(out)
    except (OSError, subprocess.SubprocessError):
        pass
    return Path.home() / "Desktop"


def write_entry(folder, target, icon, trusted=False):
    """Writes the entry into `folder` and returns its path. On the desktop (`trusted`) it is made
    executable and marked trusted for GNOME's file manager, which otherwise will not start it."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / ENTRY_NAME
    path.write_text(entry_text(target, icon), encoding="utf-8")
    path.chmod(0o755 if trusted else 0o644)
    if trusted:
        try:
            subprocess.run(["gio", "set", str(path), "metadata::trusted", "true"],
                           capture_output=True, timeout=5)
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        try:
            subprocess.run(["update-desktop-database", str(folder)], capture_output=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            pass
    return path
