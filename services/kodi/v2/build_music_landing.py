"""Build the exact-successor HP Music landing overlay from a live snapshot."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from music_hero_ui import extend_home, extend_includes, extend_music_data


HERE = Path(__file__).resolve().parent
EXPECTED = {
    'music_data.py': '302480b923f8372437cc4e7c7b77e66e4dd3350cb9edc1d4a27d0682bda8406b',
    'IncludesMusic.xml': 'fb9f085bf586f43216c4d8429c09e42ff8861efd8b19ff2240a2e6f1eaa30c83',
    'custom_1113_music.xml': 'b56670d6e121e3204c30b4bf408149fc6e34a17c07f9740898607a6d523b7fb6',
}
ACTIVE = '83a5107425e65475af369391d4e8ccf47de0bd17499bad3ab8d5a66f67bb696a'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def raw(value):
    return (json.dumps(value, indent=2) + '\n').encode()


def build(snapshot, active_manifest, output):
    snapshot, active_manifest, output = map(Path, (snapshot, active_manifest, output))
    if output.exists():
        raise ValueError('immutable-music-landing-output')
    if sha(active_manifest.read_bytes()) != ACTIVE:
        raise ValueError('music-landing-active-manifest')
    sources = {}
    for name, expected in EXPECTED.items():
        data = (snapshot / name).read_bytes()
        if sha(data) != expected:
            raise ValueError('music-landing-predecessor:' + name)
        sources[name] = data
    files = {
        'tools/music_data.py': extend_music_data(sources['music_data.py']),
        '1080i/IncludesMusic.xml': extend_includes(sources['IncludesMusic.xml']),
        '1080i/custom_1113_music.xml': extend_home(sources['custom_1113_music.xml']),
        'tools/music_landing.py': (HERE / 'music_landing.py').read_bytes(),
        'tools/owned_landing.py': (HERE / 'owned_landing.py').read_bytes(),
        'tools/music_policy.py': (HERE / 'music_policy.py').read_bytes(),
    }
    for name, data in files.items():
        if name.endswith('.py'):
            ast.parse(data)
        else:
            ET.fromstring(data)
    parent = json.loads(active_manifest.read_text())
    prior = {row['path']: row['sha256'] for row in parent['files']}
    records = []
    output.mkdir(parents=True)
    for name, data in sorted(files.items()):
        target = output / 'payload' / '.kodi/addons/skin.asterhome' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        records.append(dict(path='.kodi/addons/skin.asterhome/' + name,
                            sha256=sha(data), before_sha256=prior.get(name)))
    successor_rows = []
    for row in parent['files']:
        name = row['path']
        changed = files.get(name)
        successor_rows.append(dict(row, **({'sha256': sha(changed), 'bytes': len(changed)}
                                           if changed is not None else {})))
    for name in ('tools/music_landing.py', 'tools/owned_landing.py', 'tools/music_policy.py'):
        successor_rows.append(dict(path=name, sha256=sha(files[name]),
                                   bytes=len(files[name]), before_sha256=None))
    integration = dict(parent, kind='hp-owned-music-landing', files=successor_rows,
                       previous_manifest_sha256=ACTIVE)
    manifest_path = ('.aster-checkpoints/aster-music-integration-20261024/'
                     'active-manifest.json')
    data = raw(integration)
    target = output / 'payload' / manifest_path
    target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
    records.append(dict(path=manifest_path, sha256=sha(data), before_sha256=ACTIVE))
    manifest = dict(schema=1, kind='hp-owned-music-landing',
                    previous_manifest_sha256=ACTIVE, files=records,
                    music_integration_sha256=sha(data))
    helpers = {
        'music_landing_install.py': HERE / 'music_landing_install.py',
        'deploy_music_landing.py': HERE / 'tools/deploy_music_landing.py',
        'digest_news_install.py': HERE / 'digest_news_install.py',
    }
    manifest['helpers'] = {}
    for name, source in helpers.items():
        helper = source.read_bytes()
        (output / name).write_bytes(helper)
        manifest['helpers'][name] = sha(helper)
    (output / 'manifest.json').write_bytes(raw(manifest))
    return sha(raw(manifest))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot', required=True)
    parser.add_argument('--active-manifest', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(build(args.snapshot, args.active_manifest, args.output))
