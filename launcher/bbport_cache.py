# SPDX-License-Identifier: GPL-2.0-or-later
"""The port's shader cache: <user directory>/cache, one folder (or .zip) per game serial, with the
shaders the GPU library translated (cache_storage.cpp). The launcher shows its size and clears it;
the next start translates the shaders again. The drivers' own caches (NVIDIA's, Mesa's) belong to
the system and other games, and stay.
"""
import shutil
from pathlib import Path


def cache_dir(user_dir):
    return Path(user_dir) / 'cache'


def size(user_dir):
    """Bytes the shader cache takes (its files' sizes); 0 when there is none."""
    total = 0
    for path in cache_dir(user_dir).rglob('*'):
        try:
            if path.is_file() and not path.is_symlink():
                total += path.stat().st_size
        except OSError:
            continue
    return total


def clear(user_dir):
    """Removes everything in the shader cache, not the folder itself. Returns the bytes freed."""
    freed = size(user_dir)
    directory = cache_dir(user_dir)
    if directory.is_dir():
        for entry in directory.iterdir():
            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry, ignore_errors=True)
            else:
                entry.unlink(missing_ok=True)
    return freed - size(user_dir)
