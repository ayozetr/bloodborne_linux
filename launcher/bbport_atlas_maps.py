# SPDX-License-Identifier: GPL-2.0-or-later
"""Hunter's Atlas's maps, made on the player's computer (the launcher's "Prepare maps").

The maps come from the player's own game files: Atlas's generator (tools/hunters-atlas) reads them
with soulstruct and needs CPython 3.12 and pinned packages. Nothing of that is in the package; the
first preparation fetches it into the data folder (atlas-tools/):

1. uv, a single static program (a pinned release, checked against its SHA-256);
2. CPython 3.12 (uv's own builds) and the generator's packages (requirements.lock: exact versions
   with their hashes, checked by uv);
3. the maps (generate_atlas.py), the names in the game's language (localize_names.py) and Atlas's
   own art, converted for the game (art/*.png -> .bbra).

The maps are made in navigation-map.new and replace navigation-map only once complete, keeping the
map's own settings (settings.ini); a failed or cancelled run leaves the previous maps as they were.
Run as a program it prints one JSON line per step ({"progress": 0-100, "stage": ...}) and exits 0
when done: the launcher shows its progress and can stop it (the whole process group).
"""
import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools" / "hunters-atlas"
UV_VERSION = "0.12.22"
UV_URL = (f"https://github.com/astral-sh/uv/releases/download/{UV_VERSION}/"
          "uv-x86_64-unknown-linux-musl.tar.gz")
UV_SHA256 = "a50fd68c653b0cfb1c85e0a7db62cb78cf5c22b6f3dcf3ae173e5f222d084470"
PYTHON_VERSION = "3.12.15"
MAPS, NEW, OLD, TOOLS = "navigation-map", "navigation-map.new", "navigation-map.old", "atlas-tools"
STAGING = "navigation-map.staging"  # the generator's work files (~160 MB), removed after it
# Atlas's art (tools/hunters-atlas/art: its source/art at 4ee4a0ed, the PNGs recompressed without
# loss by optipng, the same pixels).
ART = {
    "background.png": "0de51b2c99cf84b462ea003de3eec5ec528aba511393238ec3f3786b0c953f7a",
    "icons.png": "a7c6476f011f0581f990f1c36e1fa059b9be37bb32e542ea49485fa800b762f5",
    "menu.png": "9a8c1c767a35139ef5bb5873025d797e3f975765e67f0bc26455217e72e09b75",
    "parchment.png": "f2be127be052de9f80e4c0b6ef0f9d97298014fc2c3048e8f73f8993a5d429ee",
    "fallback.ttf": "58568c88a01b80dfc056daca3eeafd434a0380df1a48dda53f0de0d716109bbd",
}
# The game's language (BB_LANGUAGE) -> its text folder (msg/<folder>).
LANGUAGE_FOLDERS = {0: "jpnjp", 1: "engus", 2: "frafr", 3: "spaes", 4: "deude", 5: "itait",
                    6: "nldnl", 7: "porpt", 8: "rusru", 9: "korkr", 10: "zhotw", 11: "zhocn",
                    12: "finfi", 13: "swese", 14: "dandk", 15: "norno", 16: "polpl", 17: "porbr",
                    18: "enggb", 19: "turtr", 20: "spaar"}
NEEDED_FREE = 900 * 1024 * 1024  # tools (~350 MB), the new maps (~120 MB) and the old ones
# The steps and their share of the progress bar (start, end).
STEPS = {"uv": (0, 4), "python": (4, 12), "packages": (12, 26), "maps": (26, 90), "names": (90, 95),
         "art": (95, 99), "install": (99, 100)}


class Failure(Exception):
    """A step that failed; its message is the stage's key and a detail."""
    def __init__(self, stage, detail):
        super().__init__(f"{stage}: {detail}")
        self.stage, self.detail = stage, detail


def language_folder(language):
    """The text folder of a BB_LANGUAGE id (English for an unknown one)."""
    try:
        return LANGUAGE_FOLDERS.get(int(language), "engus")
    except (TypeError, ValueError):
        return "engus"


def maps_state(data_dir):
    """{"ready", "language", "bytes"} of the prepared maps in the data folder."""
    folder = Path(data_dir) / MAPS
    info = {"ready": False, "language": None, "bytes": 0}
    if not (folder / "maps" / "atlas.json").is_file() or not (folder / "art" / "icons.bbra").is_file():
        return info
    info["ready"] = True
    # bbport.json is written by the preparation; maps made by hand have the names' language only
    # in the generator's manifest (localize_names.py adds it; none: English).
    for record, default in (("bbport.json", None), ("maps/generated-assets.json", "engus")):
        try:
            info["language"] = json.loads((folder / record).read_text(encoding="utf-8")).get("language", default)
            break
        except (OSError, ValueError, AttributeError):
            continue
    info["bytes"] = folder_bytes(folder, Path(data_dir) / TOOLS)
    return info


def folder_bytes(*folders):
    """The space the folders take: a file hard-linked twice (uv links its cache into the
    environment) counts once."""
    total, seen = 0, set()
    for folder in folders:
        for root, _dirs, files in os.walk(folder):
            for name in files:
                try:
                    st = os.lstat(os.path.join(root, name))
                except OSError:
                    continue
                if (st.st_dev, st.st_ino) not in seen:
                    seen.add((st.st_dev, st.st_ino))
                    total += st.st_size
    return total


def delete(data_dir):
    """Removes the maps and the tools made for them (and any half-made maps)."""
    for name in (NEW, OLD, STAGING, MAPS, TOOLS):
        shutil.rmtree(Path(data_dir) / name, ignore_errors=True)


def child_environment(tools):
    """The environment of uv and the generator: none of the package's Python or libraries, and
    uv's files kept in the tools folder."""
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("PYTHON", "LD_", "UV_", "VIRTUAL_ENV", "CONDA"))}
    env.update(UV_CACHE_DIR=str(tools / "cache"), UV_PYTHON_INSTALL_DIR=str(tools / "python"),
               UV_NO_CONFIG="1", UV_PYTHON_PREFERENCE="only-managed", UV_NO_PROGRESS="1",
               PYTHONDONTWRITEBYTECODE="1")
    return env


class Preparation:
    def __init__(self, data_dir, game_dir, language, report=None):
        self.data = Path(data_dir)
        self.game = Path(game_dir)
        self.language = language
        self.tools = self.data / TOOLS
        self.new = self.data / NEW
        self.report = report or (lambda progress, stage, detail=None: None)
        self.log = []
        self.language_done = None

    def step(self, stage, fraction=0.0, detail=None):
        start, end = STEPS[stage]
        self.report(int(start + (end - start) * min(max(fraction, 0.0), 1.0)), stage, detail)

    def run(self, command, stage, cwd=None, on_line=None):
        """Runs a tool; its output goes to the log (and to on_line); a failure stops here."""
        process = subprocess.Popen(command, cwd=cwd, env=child_environment(self.tools), text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
        for line in process.stdout:
            line = line.rstrip("\n")
            self.log.append(line)
            del self.log[:-200]
            if on_line:
                on_line(line)
        if process.wait() != 0:
            tail = " | ".join(line for line in self.log[-4:] if line.strip())
            raise Failure(stage, f"exit {process.returncode}: {tail}")

    # -- tools -----------------------------------------------------------------------------
    def marker(self):
        lock = (TOOLS_DIR / "requirements.lock").read_bytes()
        return {"uv": UV_VERSION, "python": PYTHON_VERSION, "lock": hashlib.sha256(lock).hexdigest()}

    def tools_ready(self):
        try:
            ready = json.loads((self.tools / "ready.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False
        return ready == self.marker() and self.uv().is_file() and self.python().is_file()

    def uv(self):
        return self.tools / "bin" / "uv"

    def python(self):
        return self.tools / "venv" / "bin" / "python"

    def fetch_uv(self):
        self.step("uv")
        (self.tools / "bin").mkdir(parents=True, exist_ok=True)
        handle, temp = tempfile.mkstemp(dir=self.tools, suffix=".tar.gz")
        try:
            digest = hashlib.sha256()
            request = urllib.request.Request(UV_URL, headers={"User-Agent": "bbport-launcher"})
            with os.fdopen(handle, "wb") as out, urllib.request.urlopen(request, timeout=30) as reply:
                size = int(reply.headers.get("Content-Length") or 0)
                done = 0
                while chunk := reply.read(1 << 16):
                    out.write(chunk)
                    digest.update(chunk)
                    done += len(chunk)
                    if size:
                        self.step("uv", done / size)
            if digest.hexdigest() != UV_SHA256:
                raise Failure("uv", "the download does not match its SHA-256")
            with tarfile.open(temp) as archive:
                member = next((m for m in archive.getmembers()
                               if m.isfile() and m.name.endswith("/uv") and m.name.count("/") == 1), None)
                if member is None:
                    raise Failure("uv", "no uv in the archive")
                source = archive.extractfile(member)
                target = self.uv().with_suffix(".part")
                with open(target, "wb") as out:
                    shutil.copyfileobj(source, out)
                target.chmod(0o755)
                target.replace(self.uv())
        except OSError as error:
            raise Failure("uv", str(error)) from error
        finally:
            Path(temp).unlink(missing_ok=True)

    def install_tools(self):
        if self.tools_ready():
            self.step("packages", 1.0)
            return
        shutil.rmtree(self.tools / "venv", ignore_errors=True)
        (self.tools / "ready.json").unlink(missing_ok=True)
        self.fetch_uv()
        self.step("python")
        self.run([str(self.uv()), "python", "install", PYTHON_VERSION], "python")
        self.step("packages")
        self.run([str(self.uv()), "venv", "--python", PYTHON_VERSION, str(self.tools / "venv")], "packages")
        self.step("packages", 0.2)
        self.run([str(self.uv()), "pip", "install", "--python", str(self.python()), "--require-hashes",
                  "-r", str(TOOLS_DIR / "requirements.lock")], "packages")
        (self.tools / "ready.json").write_text(json.dumps(self.marker()), encoding="utf-8")
        self.step("packages", 1.0)

    # -- maps ------------------------------------------------------------------------------
    def generate(self):
        self.step("maps")

        def on_line(line):
            if line.startswith("{"):
                try:
                    record = json.loads(line)
                except ValueError:
                    return
                if isinstance(record.get("progress"), int):
                    self.step("maps", record["progress"] / 100, record.get("stage"))
        staging = self.data / STAGING
        shutil.rmtree(staging, ignore_errors=True)
        try:
            self.run([str(self.python()), "-B", "-E", "-s", "generate_atlas.py", "--game-dir", str(self.game),
                      "--output-dir", str(self.new), "--staging-dir", str(staging)], "maps", cwd=TOOLS_DIR,
                     on_line=on_line)
        finally:
            shutil.rmtree(staging, ignore_errors=True)
        shutil.rmtree(self.new / ".generation-staging", ignore_errors=True)
        if not (self.new / "maps" / "atlas.json").is_file():
            raise Failure("maps", "the generator made no atlas.json")

    def localize(self):
        self.step("names")
        folder = language_folder(self.language)
        if folder in ("engus", "enggb") or not (self.game / "dvdroot_ps4" / "msg" / folder).is_dir():
            return "engus"
        self.run([str(self.python()), "-B", "-E", "-s", "localize_names.py", "--game-dir", str(self.game),
                  "--output-dir", str(self.new), "--language", folder], "names", cwd=TOOLS_DIR)
        return folder

    def convert_art(self):
        self.step("art")
        art = TOOLS_DIR / "art"
        for name, digest in ART.items():
            if hashlib.sha256((art / name).read_bytes()).hexdigest() != digest:
                raise Failure("art", f"{name} does not match Atlas's art")
        target = self.new / "art"
        target.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(art / "fallback.ttf", target / "fallback.ttf")
        # Pillow is the generator's: the art's pixels as BBRA ("BBRA", width, height, RGBA rows).
        convert = ("import struct,sys\nfrom pathlib import Path\nfrom PIL import Image\n"
                   "source,target=Path(sys.argv[1]),Path(sys.argv[2])\n"
                   "for name in ('background','icons','menu','parchment'):\n"
                   "    im=Image.open(source/(name+'.png')).convert('RGBA')\n"
                   "    (target/(name+'.bbra')).write_bytes(b'BBRA'+struct.pack('<II',*im.size)+im.tobytes())\n")
        self.run([str(self.python()), "-B", "-E", "-s", "-c", convert, str(art), str(target)], "art")
        if not (target / "icons.bbra").is_file() or not (target / "native-font.ttf").is_file():
            raise Failure("art", "the map art is incomplete")

    def install(self, language):
        self.step("install")
        (self.new / "bbport.json").write_text(json.dumps({
            "language": language, "uv": UV_VERSION, "python": PYTHON_VERSION}), encoding="utf-8")
        current, old = self.data / MAPS, self.data / OLD
        if (current / "settings.ini").is_file():  # the map's own settings (zoom keys, toggles)
            shutil.copyfile(current / "settings.ini", self.new / "settings.ini")
        shutil.rmtree(old, ignore_errors=True)
        if current.exists():
            current.rename(old)
        self.new.rename(current)
        shutil.rmtree(old, ignore_errors=True)
        self.step("install", 1.0)

    def prepare(self):
        if not (self.game / "eboot.bin").is_file():
            raise Failure("game", f"no eboot.bin in {self.game}")
        self.data.mkdir(parents=True, exist_ok=True)
        if shutil.disk_usage(self.data).free < NEEDED_FREE:
            raise Failure("space", f"{NEEDED_FREE >> 20} MiB free are needed in {self.data}")
        shutil.rmtree(self.new, ignore_errors=True)
        try:
            self.install_tools()
            self.generate()
            language = self.localize()
            self.convert_art()
            self.install(language)
            self.language_done = language
        except BaseException:
            shutil.rmtree(self.new, ignore_errors=True)  # the previous maps stay as they were
            raise


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="action", required=True)
    prepare = sub.add_parser("prepare", help="make (or remake) the maps")
    prepare.add_argument("--data-dir", type=Path, required=True)
    prepare.add_argument("--game-dir", type=Path, required=True)
    prepare.add_argument("--language", default="1", help="BB_LANGUAGE id of the game")
    remove = sub.add_parser("delete", help="remove the maps and their tools")
    remove.add_argument("--data-dir", type=Path, required=True)
    a = p.parse_args(argv)
    if a.action == "delete":
        delete(a.data_dir)
        return 0

    def report(progress, stage, detail=None):
        print(json.dumps({"progress": progress, "stage": stage, "detail": detail}), flush=True)

    def stopped(_signum, _frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stopped)
    preparation = Preparation(a.data_dir, a.game_dir, a.language, report)
    try:
        preparation.prepare()
    except Failure as failure:
        print(json.dumps({"error": failure.stage, "detail": failure.detail}), flush=True)
        return 1
    except KeyboardInterrupt:
        print(json.dumps({"error": "cancelled", "detail": None}), flush=True)
        return 2
    except Exception as error:  # noqa: BLE001  (shown in the launcher, not a traceback)
        print(json.dumps({"error": "unexpected", "detail": f"{type(error).__name__}: {error}"}), flush=True)
        return 1
    print(json.dumps({"done": True, "language": preparation.language_done}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
