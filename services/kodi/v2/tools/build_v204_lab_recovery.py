#!/usr/bin/env python3
"""Build the credential-free v2.0.4 lab repair overlay from v2.0.3."""

import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile


KODI = Path(__file__).resolve().parents[2]
V2 = KODI / 'v2'
BASE = KODI / 'dist/astertv-v2.0.3-code-only-lab.tar.gz'
BASE_SHA = 'bedee92f711fe62b3e18921cf7b9fa8e2421117030cd678886461da8bc1c90af'
OUT = KODI / 'dist/astertv-v2.0.4-code-only-lab.tar.gz'
KEYMAP = KODI / 'dist/astertv-v2.0.4-lab-keymap.xml'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def update_row(manifest, path, raw):
    row, = [row for row in manifest['files'] if row['path'] == path]
    row.update(bytes=len(raw), sha256=sha(raw))


def transform_movie(raw):
    text = raw.decode()
    source = (V2 / 'movie_native/default.py').read_text()
    helper = source[source.index('def admitted_source(movie_id):'):source.index('def main():')]
    old = "require(xbmcgui.getCurrentWindowId()==11127 and xbmcgui.getCurrentWindowDialogId() in (0,9999) and idle(rpc),'idle-search-source-required')"
    if text.count('def main():') != 1 or text.count(old) != 1:
        raise ValueError('movie-predecessor')
    text = text.replace('def main():', helper + 'def main():')
    text = text.replace(old, "require(admitted_source(int(sys.argv[1])) and idle(rpc),'idle-movie-source-required')")
    compile(text, 'movie.py', 'exec')
    return text.encode()


def transform_select(raw):
    text = raw.decode()
    source = (KODI / 'skin.asterhome/tools/select_dispatch.py').read_text()
    begin = '    if (window_id, focus_id) in ((10025, 50), (10000, 100), (10000, 110)):'
    block = source[source.index(begin):source.index('    if window_id == 10502', source.index(begin))]
    old = '    if (window_id, focus_id) in ((10025, 50), (10000, 110)):'
    if text.count(old) != 1 or begin in text:
        raise ValueError('select-predecessor')
    text = text.replace(old, block + old)
    compile(text, 'select_dispatch.py', 'exec')
    return text.encode()


def build():
    if OUT.exists() or sha(BASE.read_bytes()) != BASE_SHA:
        raise ValueError('base-drift-or-output-exists')
    members = {}
    with tarfile.open(BASE, 'r:gz') as archive:
        for entry in archive:
            name = entry.name
            path = PurePosixPath(name)
            if (name in members or path.is_absolute() or '..' in path.parts
                    or (name != '.' and not name.startswith('./'))
                    or not (entry.isfile() or entry.isdir())):
                raise ValueError('unsafe-member')
            members[name] = (entry, archive.extractfile(entry).read() if entry.isfile() else None)
    data = {name: value for name, (_, value) in members.items()}
    prefix = './script.asterruntime/aster-global-search-ui22/'
    movie = transform_movie(data[prefix + 'movie.py'])
    select = transform_select(data['./skin.asterhome/tools/select_dispatch.py'])
    movie_xml = (V2 / 'movie_native/custom_1130_movie.xml').read_bytes()
    settings_xml = (KODI / 'skin.asterhome/1080i/SettingsCategory.xml').read_bytes()
    music = (V2 / 'music_catalogue.py').read_bytes()
    data[prefix + 'movie.py'] = movie
    data[prefix + 'overlay/select_dispatch.py'] = select
    data[prefix + 'overlay/custom_1130_movie.xml'] = movie_xml
    data['./skin.asterhome/tools/select_dispatch.py'] = select
    data['./skin.asterhome/1080i/custom_1130_movie.xml'] = movie_xml
    data['./skin.asterhome/1080i/SettingsCategory.xml'] = settings_xml
    data['./script.astermusic.v2lab/resources/lib/music_catalogue.py'] = music

    component_name = prefix + 'manifest.json'
    component = json.loads(data[component_name])
    for path, raw in [('movie.py', movie), ('overlay/select_dispatch.py', select),
                      ('overlay/custom_1130_movie.xml', movie_xml)]:
        update_row(component, path, raw)
    data[component_name] = (json.dumps(component, indent=2) + '\n').encode()

    music_manifest_name = './script.asterruntime/music72-manifest.json'
    music_manifest = json.loads(data[music_manifest_name])
    update_row(music_manifest, 'script.astermusic.v2lab/resources/lib/music_catalogue.py', music)
    data[music_manifest_name] = (json.dumps(music_manifest, indent=2) + '\n').encode()

    family_name = './script.asterruntime/family-manifest.json'
    family = json.loads(data[family_name])
    family['components']['aster-global-search-ui22']['manifest_sha256'] = sha(data[component_name])
    family['music_manifest_sha256'] = sha(data[music_manifest_name])
    family['skin']['tools/select_dispatch.py'] = sha(select)
    data[family_name] = (json.dumps(family, indent=2, sort_keys=True) + '\n').encode()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w') as archive:
            for name in sorted(members):
                previous = members[name][0]
                value = data[name]
                entry = tarfile.TarInfo(name)
                entry.uid = entry.gid = entry.mtime = 0
                entry.uname = entry.gname = ''
                entry.mode = previous.mode
                if value is None:
                    entry.type = tarfile.DIRTYPE
                    archive.addfile(entry)
                else:
                    entry.size = len(value)
                    archive.addfile(entry, io.BytesIO(value))
    KEYMAP.write_bytes((KODI / 'remote/g20s-pro-plus.xml').read_bytes())
    return {'archive_sha256': sha(OUT.read_bytes()), 'archive_bytes': OUT.stat().st_size,
            'archive_members': len(members), 'family_sha256': sha(data[family_name]),
            'keymap_sha256': sha(KEYMAP.read_bytes())}


if __name__ == '__main__':
    print(json.dumps(build(), indent=2))
