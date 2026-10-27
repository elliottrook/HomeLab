"""Build an exact family-runtime successor containing EPUB Doctor reporting."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build_family_runtime import encoded, rewrite_component
from family_runtime import component_manifest, exact_members


OLD = 'aster-network-preview5'
NEW = 'aster-network-preview6'
SETTINGS = '1080i/Settings.xml'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def replace_one(raw, old, new, code):
    if raw.count(old) != 1:
        raise ValueError(code)
    return raw.replace(old, new)


def build(addon, skin, source, output):
    addon, skin, source, output = map(Path, (addon, skin, source, output))
    if output.exists():
        raise ValueError('epub-doctor-output-exists')
    family_raw = (addon / 'family-manifest.json').read_bytes()
    family = json.loads(family_raw)
    if (family.get('kind') != 'aster-family-runtime.v1'
            or OLD not in family.get('components', {}) or NEW in family['components']):
        raise ValueError('epub-doctor-family-predecessor')
    old_root = addon / OLD
    old_manifest_raw = (old_root / 'manifest.json').read_bytes()
    old_members = exact_members(old_root)
    if sha(old_manifest_raw) != family['components'][OLD]['manifest_sha256']:
        raise ValueError('epub-doctor-old-component-drift')

    source_manifest_raw = (source / 'manifest.json').read_bytes()
    source_manifest = json.loads(source_manifest_raw)
    if (source_manifest.get('kind') != 'hp-network-preview.v6'
            or source_manifest.get('books_doctor') is not True
            or source_manifest.get('repairs') is not False):
        raise ValueError('epub-doctor-source-contract')
    files = rewrite_component(NEW, exact_members(source), {})
    new_manifest_raw = encoded(component_manifest(
        NEW, files, sha(source_manifest_raw), source_manifest))
    new_pin = sha(new_manifest_raw)

    dispatcher = (addon / 'default.py').read_bytes()
    dispatcher_after = replace_one(dispatcher, OLD.encode(), NEW.encode(),
                                   'epub-doctor-dispatcher-anchor')
    settings = (skin / SETTINGS).read_bytes()
    settings_after = replace_one(settings, OLD.encode(), NEW.encode(),
                                 'epub-doctor-settings-component-anchor')
    settings_after = replace_one(
        settings_after, family['components'][OLD]['manifest_sha256'].encode(),
        new_pin.encode(), 'epub-doctor-settings-pin-anchor')

    successor = json.loads(family_raw)
    successor['components'].pop(OLD)
    successor['components'][NEW] = {'manifest_sha256': new_pin,
                                    'files': len(files)}
    successor['skin'][SETTINGS] = sha(settings_after)
    family_after = encoded(successor)

    write(output / 'payload/runtime/default.py', dispatcher_after)
    write(output / 'payload/runtime/family-manifest.json', family_after)
    write(output / 'payload/skin' / SETTINGS, settings_after)
    write(output / 'payload/runtime' / NEW / 'manifest.json', new_manifest_raw)
    for relative, raw in files.items():
        write(output / 'payload/runtime' / NEW / relative, raw)

    old_rows = [dict(path=path, bytes=len(raw), sha256=sha(raw))
                for path, raw in sorted(old_members.items())]
    new_rows = [dict(path=path, bytes=len(raw), sha256=sha(raw))
                for path, raw in sorted(files.items())]
    manifest = {
        'schema': 1, 'kind': 'aster-epub-doctor-family.v1',
        'old_component': OLD, 'new_component': NEW,
        'before': {
            'runtime_default': sha(dispatcher),
            'family_manifest': sha(family_raw),
            'settings': sha(settings),
            'component_manifest': sha(old_manifest_raw),
            'component_files': old_rows,
        },
        'after': {
            'runtime_default': sha(dispatcher_after),
            'family_manifest': sha(family_after),
            'settings': sha(settings_after),
            'component_manifest': new_pin,
            'component_files': new_rows,
        },
        'source_manifest_sha256': sha(source_manifest_raw),
        'read_only': True, 'repairs': False,
    }
    here = Path(__file__).resolve().parent
    helpers = (here / 'epub_doctor_family_install.py',
               here / 'tools/deploy_epub_doctor_family.py')
    manifest['helpers'] = {}
    for helper in helpers:
        write(output / helper.name, helper.read_bytes())
        manifest['helpers'][helper.name] = sha(helper.read_bytes())
    write(output / 'manifest.json', encoded(manifest))
    return sha((output / 'manifest.json').read_bytes())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--addon', required=True)
    parser.add_argument('--skin', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(build(args.addon, args.skin, args.source, args.output))
