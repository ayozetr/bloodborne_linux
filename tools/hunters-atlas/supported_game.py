"""bbport: whether a game folder holds the supported Bloodborne 1.09 executable.

The generator compared eboot.bin's SHA-256 with one dump's: another tool's dump of the same 1.09
executable (another SELF header around it), or another edition's, was refused (issue #24). The
port's own check, the hash of the executable's loaded image (scripts/game_check.py), takes every
dump and edition the port runs.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import game_check  # noqa: E402


def supported(game):
    """True when `game` (the folder holding eboot.bin) has the supported 1.09 executable."""
    try:
        return game_check.image_sha256(game) == game_check.SUPPORTED_IMAGE
    except (OSError, ValueError, KeyError, IndexError):
        return False
