"""bbport: the names of a generated Atlas pack in the game's language.

The generator writes the names of areas, lamps and pickups in English: it reads msg/engus and
matches names by their English text. This step runs after it and changes nothing of that: every
name it finds among the game's own English texts (menu.msgbnd and item.msgbnd) is replaced by the
text with the same id in the chosen language folder (msg/spaes, msg/rusru, ...), so the names are
the game's own. Names it cannot find stay in English; one made of several names joined by " / "
(an area with three places) is translated part by part.

    python localize_names.py --game-dir <game> --output-dir <generated pack> --language spaes

The game is only read. maps/generated-assets.json gets the language and the new file hashes.
"""
import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

BINDERS = ('menu.msgbnd.dcx', 'item.msgbnd.dcx')


def texts(folder):
    """{(binder, text file, text id): text} of one msg language folder."""
    import tempfile
    import pipeline_context as ctx
    if ctx.STAGE is None:  # the local soulstruct config places its unused paths there
        ctx.STAGE = Path(tempfile.gettempdir()) / 'atlas-localize'
    import soulstruct_local_config
    sys.modules['soulstruct.config'] = soulstruct_local_config  # as generate_atlas.py does
    from soulstruct.containers import Binder
    from soulstruct.base.text.fmg import FMG
    result = {}
    for binder in BINDERS:
        for entry in Binder.from_path(folder / binder).entries:
            name = entry.name.replace('\\', '/').rsplit('/', 1)[-1]
            if not name.endswith('.fmg'):
                continue
            for text_id, value in FMG.from_bytes(entry.get_uncompressed_data()).entries.items():
                if value and value.strip():
                    result[(binder, name, text_id)] = value.strip()
    return result


def dictionary(english, local):
    """English text -> the language's text for the same ids (the most common one when the ids of
    one English text differ in the language)."""
    candidates = defaultdict(Counter)
    for key, text in english.items():
        if key in local and '\n' not in text:
            candidates[text][local[key]] += 1
    return {text: counts.most_common(1)[0][0] for text, counts in candidates.items()}


def translate(words, name):
    if name in words:
        return words[name]
    if ' / ' in name:
        return ' / '.join(translate(words, part) for part in name.split(' / '))
    return name


def localize(output, words):
    """Translates the display names of the pack in place; returns (translated, unchanged)."""
    done, kept = Counter(), Counter()

    def name(holder):
        if isinstance(holder, dict) and isinstance(holder.get('name'), str):
            new = translate(words, holder['name'])
            (done if new != holder['name'] else kept)[holder['name']] += 1
            holder['name'] = new

    maps = output / 'maps'
    atlas = json.loads((maps / 'atlas.json').read_text(encoding='utf-8'))
    for area in atlas.get('maps', []):
        name(area)
    catalog = json.loads((maps / 'catalog.json').read_text(encoding='utf-8'))
    for area in catalog.values():
        if isinstance(area, dict):
            for key in ('landmarks', 'regions'):
                for item in area.get(key, []):
                    name(item)
    features = json.loads((maps / 'features.json').read_text(encoding='utf-8'))
    for area in features.get('areas', {}).values():
        for key in ('lamps', 'reveal_regions'):
            for item in area.get(key, []):
                name(item)
        for pickup in area.get('pickups', []):
            for item in pickup.get('contents', []):
                name(item)
    areas = {}
    for path in sorted(maps.glob('m??_??_??_??.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        name(data)
        for lamp in data.get('lamps', []):
            name(lamp)
        areas[path] = data
    files = {maps / 'atlas.json': atlas, maps / 'catalog.json': catalog, maps / 'features.json': features}
    files.update(areas)
    for path, data in files.items():
        path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    return done, kept


def update_manifest(output, language):
    path = output / 'maps' / 'generated-assets.json'
    if not path.exists():
        return
    manifest = json.loads(path.read_text(encoding='utf-8'))
    manifest['language'] = language
    files = manifest.get('files')  # {"maps/atlas.json": sha256, ...}
    if isinstance(files, dict):
        for relative in files:
            target = output / relative
            if target.is_file():
                files[relative] = hashlib.sha256(target.read_bytes()).hexdigest()
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--game-dir', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--language', required=True, help='msg folder of the language: spaes, frafr, rusru, ...')
    a = p.parse_args(argv)
    msg = a.game_dir / 'dvdroot_ps4' / 'msg'
    if a.language == 'engus':
        print(json.dumps({'stage': 'localize', 'language': 'engus', 'translated': 0}))
        return 0
    if not (msg / a.language).is_dir():
        raise SystemExit(f'No msg/{a.language} in the game: the names stay in English')
    words = dictionary(texts(msg / 'engus'), texts(msg / a.language))
    done, kept = localize(a.output_dir, words)
    update_manifest(a.output_dir, a.language)
    print(json.dumps({'stage': 'localize', 'language': a.language, 'translated': sum(done.values()),
                      'unchanged': sorted(kept)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
