"""Build the immutable HP candidate for Aster's native Seerr page."""

import argparse
import hashlib
import json
from pathlib import Path

from seerr_home_launcher import add_requests


ADDON = 'script.asterseerr'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, indent=2, sort_keys=True).encode() + b'\n'


def build(home, output):
    home, output = Path(home), Path(output)
    if output.exists() or not home.is_file() or home.is_symlink():
        raise ValueError('seerr-build-path')
    output.mkdir(parents=True)
    here = Path(__file__).resolve().parent
    addon = output / ADDON
    library = addon / 'resources/lib'
    library.mkdir(parents=True)
    sources = {
        'default.py': here / 'seerr_native/default.py',
        'resources/lib/seerr_request_model.py': here / 'seerr_request_model.py',
        'resources/lib/seerr_broker_client.py': here / 'seerr_broker_client.py',
        'resources/lib/seerr_page_model.py': here / 'seerr_page_model.py',
    }
    for relative, source in sources.items():
        if not source.is_file() or source.is_symlink():
            raise ValueError('seerr-build-source')
        target = addon / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    addon_xml = b'''<?xml version="1.0" encoding="UTF-8"?>
<addon id="script.asterseerr" name="Aster Requests" version="2.0.0" provider-name="Aster Home">
  <requires><import addon="xbmc.python" version="3.0.0"/></requires>
  <extension point="xbmc.python.script" library="default.py"><provides>executable</provides></extension>
  <extension point="xbmc.addon.metadata"><summary lang="en_GB">Private Aster Seerr request page</summary><description lang="en_GB">Credential-free client for Aster's restricted household request broker.</description><platform>all</platform><license>Private HomeLab</license></extension>
</addon>
'''
    (addon / 'addon.xml').write_bytes(addon_xml)
    addon_rows = []
    for path in sorted(addon.rglob('*')):
        if path.is_file():
            raw = path.read_bytes()
            addon_rows.append({'path': path.relative_to(addon).as_posix(),
                               'bytes': len(raw), 'sha256': digest(raw)})
    original = home.read_bytes()
    transformed = add_requests(original.decode('utf-8')).encode()
    overlay = (here / 'seerr_native/overlay/custom_1132_requests.xml').read_bytes()
    skin_files = {
        '1080i/Home.xml': (transformed, digest(original)),
        '1080i/custom_1132_requests.xml': (overlay, None),
    }
    skin_rows = []
    for relative, (raw, before) in skin_files.items():
        target = output / 'skin' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        skin_rows.append({'path': relative, 'bytes': len(raw),
                          'sha256': digest(raw), 'before_sha256': before})
    helpers = {}
    for name in ('seerr_install.py', 'deploy_seerr_page.py'):
        source = here / (name if name == 'seerr_install.py' else 'tools/' + name)
        raw = source.read_bytes()
        (output / name).write_bytes(raw)
        helpers[name] = digest(raw)
    manifest = {'schema': 1, 'kind': 'hp-seerr-page.v1', 'addon': ADDON,
                'addon_files': addon_rows, 'skin': skin_rows, 'helpers': helpers}
    (output / 'manifest.json').write_bytes(encoded(manifest))
    return digest((output / 'manifest.json').read_bytes())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--home', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(build(args.home, args.output))
