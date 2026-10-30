#!/usr/bin/env python3
"""Build the credential-free v2.0.5 Books-search lab overlay from v2.0.4."""

import gzip
import io
import json
from pathlib import Path, PurePosixPath
import tarfile

from build_v204_lab_recovery import KODI, V2, sha, update_row


BASE = KODI / 'dist/astertv-v2.0.4-code-only-lab.tar.gz'
BASE_SHA = '7a0d45665978b28179b0ba6d73a7e6150d97c8c441f1f8541e4fa0e0dd25b416'
OUT = KODI / 'dist/astertv-v2.0.5-code-only-lab.tar.gz'


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('unexpected-predecessor:' + old[:60])
    return text.replace(old, new)


def search_default(raw):
    text = raw.decode()
    source = (V2 / 'search_native/default.py').read_text()
    text = once(text,
        'from global_search import SOURCES,READS,SearchUnavailable,search_group,normalize_query\n',
        'from global_search import SOURCES,READS,SearchUnavailable,search_group,normalize_query\n'
        "sys.path.insert(0,'/storage/.kodi/addons/skin.asterhome/tools')\n"
        'from search_books import KINDS as BOOK_KINDS, local_groups, permitted_id\n')
    text = once(text,
        "home.setProperty(PREFIX+'Status','Search this box’s synced TV, film and music index.')",
        "home.setProperty(PREFIX+'Status','Search synced TV, film, music and your local Books feed.')")
    begin = source.index('            for group in local_groups(query):')
    end = source.index("            categories.selectItem(0);display(0);home.setProperty(PREFIX+'Ready','true')", begin)
    book_loop = source[begin:end]
    marker = "            categories.selectItem(0);display(0);home.setProperty(PREFIX+'Ready','true')"
    if text.count(marker) != 2:
        raise ValueError('search-loop-predecessor')
    text = text.replace(marker, book_loop + marker, 1)
    begin = source.index('        def open_book_hit(hit):')
    end = source.index("        run_query('')", begin)
    text = once(text, "        run_query('')", source[begin:end] + "        run_query('')")
    old = "                        if linked and (hit.kind in LABELS or (artist_enabled and hit.kind=='artist') or (movie_enabled and hit.kind=='movie')):"
    new = ("                        if hit.kind in dict(BOOK_KINDS):\n"
           "                            try:open_book_hit(hit)\n"
           "                            except SearchUnavailable:\n"
           "                                home.setProperty(PREFIX+'Status','This Books page could not be verified. Search again.')\n"
           "                            active_detail=None\n"
           "                        elif linked and (hit.kind in LABELS or (artist_enabled and hit.kind=='artist') or (movie_enabled and hit.kind=='movie')):")
    text = once(text, old, new)
    compile(text, 'search-default.py', 'exec')
    return text.encode()


def books_data(raw):
    text = raw.decode()
    text = once(text, "def main(page, action='load'):",
                "def main(page, action='load', identity=None):")
    text = once(text,
        "    elif action == 'clear' and page != 'home':\n        window.clearProperty('AsterBooks.Search')",
        "    elif action == 'clear' and page != 'home':\n        window.clearProperty('AsterBooks.Search')\n"
        "    elif action == 'focus' and page != 'home':\n        window.clearProperty('AsterBooks.Search')")
    text = once(text,
        "        if action == 'load' and rows:\n            xbmc.executebuiltin('Control.SetFocus(500,0,absolute)')",
        "        if action == 'focus' and identity is not None:\n"
        "            match = next((index for index, row in enumerate(rows)\n"
        "                          if row['id'] == identity and row['kind'] == KINDS[page]), None)\n"
        "            if match is not None:\n"
        "                listing.selectItem(match)\n"
        "                xbmc.executebuiltin('Control.SetFocus(500)')\n"
        "        elif action == 'load' and rows:\n"
        "            xbmc.executebuiltin('Control.SetFocus(500,0,absolute)')")
    text = once(text, "         sys.argv[2] if len(sys.argv) > 2 else 'load')",
                "         sys.argv[2] if len(sys.argv) > 2 else 'load',\n"
                "         sys.argv[3] if len(sys.argv) > 3 else None)")
    compile(text, 'books_data.py', 'exec')
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
    component = './script.asterruntime/aster-global-search-ui22/'
    default = search_default(data[component + 'default.py'])
    books = books_data(data['./skin.asterhome/tools/books_data.py'])
    old = 'Books and podcasts[CR]Not connected to search yet[CR][CR]HP preview · no autoplay'
    new = 'TV · Film · Music[CR]Ebooks · Audiobooks · Podcasts[CR][CR]Local feed · no autoplay'
    xml = once(data['./skin.asterhome/1080i/custom_1127_search.xml'].decode(), old, new).encode()
    module = (V2 / 'search_books.py').read_bytes()
    compile(module, 'search_books.py', 'exec')
    name = component + 'resources/lib/search_books.py'
    if name in members:
        raise ValueError('search-books-already-present')
    data.update({component + 'default.py': default,
                 component + 'overlay/custom_1127_search.xml': xml,
                 name: module,
                 './skin.asterhome/1080i/custom_1127_search.xml': xml,
                 './skin.asterhome/tools/books_data.py': books})
    manifest_name = component + 'manifest.json'
    manifest = json.loads(data[manifest_name])
    update_row(manifest, 'default.py', default)
    update_row(manifest, 'overlay/custom_1127_search.xml', xml)
    manifest['files'].append({'path': 'resources/lib/search_books.py',
                              'bytes': len(module), 'sha256': sha(module)})
    manifest['files'].sort(key=lambda row: row['path'])
    data[manifest_name] = (json.dumps(manifest, indent=2) + '\n').encode()
    family_name = './script.asterruntime/family-manifest.json'
    family = json.loads(data[family_name])
    family['components']['aster-global-search-ui22'].update(
        files=len(manifest['files']), manifest_sha256=sha(data[manifest_name]))
    family['skin']['1080i/custom_1127_search.xml'] = sha(xml)
    data[family_name] = (json.dumps(family, indent=2, sort_keys=True) + '\n').encode()
    with OUT.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w') as archive:
            for path in sorted(data):
                previous = members.get(path)
                value = data[path]
                entry = tarfile.TarInfo(path)
                entry.uid = entry.gid = entry.mtime = 0
                entry.uname = entry.gname = ''
                entry.mode = previous[0].mode if previous else 0o644
                if value is None:
                    entry.type = tarfile.DIRTYPE
                    archive.addfile(entry)
                else:
                    entry.size = len(value)
                    archive.addfile(entry, io.BytesIO(value))
    return {'archive_sha256': sha(OUT.read_bytes()), 'archive_bytes': OUT.stat().st_size,
            'archive_members': len(data), 'family_sha256': sha(data[family_name])}


if __name__ == '__main__':
    print(json.dumps(build(), indent=2))
