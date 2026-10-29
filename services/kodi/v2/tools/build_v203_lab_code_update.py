#!/usr/bin/env python3
"""Build the credential-free v2.0.3 lab code update from the pinned v2.0.2 archive."""

import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from youtube_lab_navigation_fix import transform


KODI = Path(__file__).resolve().parents[2]
BASE = KODI / 'dist/astertv-v2.0.2-code-only-lab.tar.gz'
BASE_SHA256 = '9c89d3e95a6deb35377bf5b3a042e80e73c3657b0ed6c80eb46396046f8debb1'
OUTPUT = Path(os.environ.get('ASTER_V203_OUTPUT',
                             str(KODI / 'dist/astertv-v2.0.3-code-only-lab.tar.gz')))
SRC = KODI


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build():
    if sha(BASE.read_bytes()) != BASE_SHA256 or OUTPUT.exists():
        raise ValueError('base archive drift or output exists')
    members = {}
    with tarfile.open(BASE, 'r:gz') as archive:
        for member in archive:
            name = member.name
            path = PurePosixPath(name)
            if (name in members or path.is_absolute() or '..' in path.parts
                    or (name != '.' and not name.startswith('./'))
                    or not (member.isfile() or member.isdir())):
                raise ValueError('unsafe base archive member')
            members[name] = (member, archive.extractfile(member).read() if member.isfile() else None)

    replacement = {
        './plugin.video.asterhome/default.py': (SRC / 'plugin.video.asterhome/default.py').read_bytes(),
        './plugin.video.asterhome/library.py': (SRC / 'plugin.video.asterhome/library.py').read_bytes(),
        './skin.asterhome/tools/youtube_root_focus.py': (SRC / 'skin.asterhome/tools/youtube_root_focus.py').read_bytes(),
    }
    nav_name = './skin.asterhome/1080i/MyVideoNav.xml'
    nav = transform(members[nav_name][1])
    if sha(nav) != 'f1ccd560d5bfd1458d4f60a42ffcdf9eb1ee889e4e1c84c8faf9ec422c90878f':
        raise ValueError('navigation transform drift')
    replacement[nav_name] = nav
    route_name = './skin.asterhome/tools/youtube_route_focus.py'
    if route_name in members:
        raise ValueError('route focus already in base')
    route = (SRC / 'skin.asterhome/tools/youtube_route_focus.py').read_bytes()
    replacement[route_name] = route

    family_name = './script.asterruntime/family-manifest.json'
    family = json.loads(members[family_name][1])
    for name in (nav_name, route_name, './skin.asterhome/tools/youtube_root_focus.py'):
        family['skin'][name[len('./skin.asterhome/'):]] = sha(replacement[name])
    replacement[family_name] = (json.dumps(family, indent=2, sort_keys=True) + '\n').encode()
    for name in replacement:
        if name not in members and name != route_name:
            raise ValueError('unexpected added member')

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w') as archive:
            for name in sorted(set(members) | {route_name}):
                previous = members.get(name)
                data = replacement.get(name, previous[1] if previous else None)
                info = tarfile.TarInfo(name)
                info.uid = info.gid = info.mtime = 0
                info.uname = info.gname = ''
                info.mode = previous[0].mode if previous else 0o644
                if data is None:
                    info.type = tarfile.DIRTYPE
                    archive.addfile(info)
                else:
                    info.size = len(data)
                    archive.addfile(info, io.BytesIO(data))
    return {'path': str(OUTPUT), 'sha256': sha(OUTPUT.read_bytes()),
            'bytes': OUTPUT.stat().st_size, 'members': len(members) + 1,
            'family_sha256': sha(replacement[family_name])}


if __name__ == '__main__':
    print(json.dumps(build(), indent=2))
