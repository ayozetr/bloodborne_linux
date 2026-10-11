# SPDX-License-Identifier: GPL-2.0-or-later
"""The launcher's version, and updates of the AppImage from this fork's GitHub releases.

Releases are tagged <upstream version>-linux.<n> (0.4-linux.1, 0.5-linux.1) and carry the
AppImage as an asset. An update downloads it next to the running AppImage ($APPIMAGE) and
renames it over that file: the running copy keeps its own mount, and the next start is the new
version. Without an AppImage (a git checkout) the launcher only links the release.
"""
import json
import os
from pathlib import Path
import re
import tempfile
import urllib.request

VERSION = "0.51-linux.1"
REPOSITORY = "ayozetr/bloodborne_linux"
REPOSITORY_URL = f"https://github.com/{REPOSITORY}"
UPSTREAM_URL = "https://github.com/deadinside28/bloodborne_pc"
WINDOWS_URL = "https://github.com/Supermedo/bloodborne_pc"
LICENSE_URL = f"{REPOSITORY_URL}/blob/main/LICENSE"
RELEASES_URL = f"{REPOSITORY_URL}/releases"
LATEST_API = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"


def version_key(tag):
    """Comparable key of a tag (0.5-linux.1 -> (0, 5, 1)); None for another scheme."""
    match = re.fullmatch(r"v?(\d+)\.(\d+)(?:\.(\d+))?-linux\.(\d+)", tag.strip())
    if not match:
        return None
    major, minor, patch, build = match.groups()
    return int(major), int(minor), int(patch or 0), int(build)


def is_newer(tag, current=VERSION):
    new, old = version_key(tag), version_key(current)
    return new is not None and old is not None and new > old


def latest_release(url=LATEST_API, timeout=10):
    """{"tag", "url", "appimage", "size"} of the latest release ("appimage" None without one)."""
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json", "User-Agent": f"bbport-launcher/{VERSION}"})
    with urllib.request.urlopen(request, timeout=timeout) as reply:
        data = json.load(reply)
    asset = next((a for a in data.get("assets", []) if a.get("name", "").endswith(".AppImage")), None)
    return {"tag": data.get("tag_name", ""), "url": data.get("html_url", RELEASES_URL),
            "appimage": asset and asset.get("browser_download_url"),
            "size": asset and asset.get("size")}


def running_appimage():
    """The AppImage this launcher runs from, when it is one and can be replaced."""
    path = os.environ.get("APPIMAGE")
    if not path:
        return None
    path = Path(path)
    return path if path.is_file() and os.access(path.parent, os.W_OK) else None


def install(url, target, progress=None, chunk=1 << 20):
    """Downloads `url` next to `target` and renames it over `target`, executable.
    progress(done, total) after every chunk; total is 0 when the server does not say."""
    request = urllib.request.Request(url, headers={"User-Agent": f"bbport-launcher/{VERSION}"})
    handle, partial = tempfile.mkstemp(prefix=".bbport-update-", dir=target.parent)
    try:
        with os.fdopen(handle, "wb") as out, urllib.request.urlopen(request, timeout=30) as reply:
            total = int(reply.headers.get("Content-Length") or 0)
            done = 0
            while block := reply.read(chunk):
                out.write(block)
                done += len(block)
                if progress:
                    progress(done, total)
        if total and done != total:
            raise OSError(f"download ended at {done} of {total} bytes")
        os.chmod(partial, 0o755)
        os.replace(partial, target)
    except BaseException:
        Path(partial).unlink(missing_ok=True)
        raise
