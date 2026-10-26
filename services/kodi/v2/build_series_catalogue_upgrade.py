"""Build a hash-pinned in-place successor for the installed HP series component."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(raw): return hashlib.sha256(raw).hexdigest()
def encoded(value): return json.dumps(value, indent=2, sort_keys=True).encode()+b'\n'


def read_exact(folder, manifest):
    result = {}
    for row in manifest['files']:
        path = folder/row['path']; raw = path.read_bytes()
        if path.is_symlink() or digest(raw) != row['sha256'] or len(raw) != row['bytes']:
            raise ValueError('catalogue-upgrade-source-drift')
        result[row['path']] = raw
    return result


def build(active_addon, active_skin, candidate, output):
    active_addon, active_skin = Path(active_addon), Path(active_skin)
    candidate, output = Path(candidate), Path(output)
    if output.exists(): raise ValueError('catalogue-upgrade-output-exists')
    output.mkdir(parents=True)
    family_path = active_addon/'family-manifest.json'
    family_raw = family_path.read_bytes(); family = json.loads(family_raw)
    old_component = active_addon/'aster-series-preview24'
    old_manifest_raw = (old_component/'manifest.json').read_bytes()
    old_manifest = json.loads(old_manifest_raw); read_exact(old_component, old_manifest)
    if (family['components']['aster-series-preview24']['manifest_sha256'] != digest(old_manifest_raw)
            or len(old_manifest['files']) != 6):
        raise ValueError('catalogue-upgrade-series-predecessor')
    source_raw = (candidate/'manifest.json').read_bytes(); source = json.loads(source_raw)
    if source.get('kind') != 'hp-series-player' or len(source.get('files', [])) != 8:
        raise ValueError('catalogue-upgrade-candidate')
    files = read_exact(candidate, source)
    installed_manifest = dict(source, component='aster-series-preview24',
                              source_manifest_sha256=digest(source_raw))
    installed_manifest_raw = encoded(installed_manifest)
    installed_sha = digest(installed_manifest_raw)
    component = output/'component'; component.mkdir()
    for relative, raw in files.items():
        path = component/relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    (component/'manifest.json').write_bytes(installed_manifest_raw)

    launcher_path = active_skin/'tools/aster_v2_series.py'
    launcher_before = launcher_path.read_bytes()
    old_sha = digest(old_manifest_raw).encode(); new_sha = installed_sha.encode()
    if launcher_before.count(old_sha) != 1 or launcher_before.count(b"len(manifest.get('files',[]))!=6") != 1:
        raise ValueError('catalogue-upgrade-launcher-predecessor')
    launcher = launcher_before.replace(old_sha, new_sha).replace(
        b"len(manifest.get('files',[]))!=6", b"len(manifest.get('files',[]))!=8")

    search_root = active_addon/'aster-global-search-ui22'
    handoff_path = search_root/'resources/lib/search_handoff.py'
    handoff_before = handoff_path.read_bytes()
    if handoff_before.count(old_sha) != 1 or handoff_before.count(
            b"len(rows)!=(6 if kind=='tvshow' else 48)") != 1:
        raise ValueError('catalogue-upgrade-search-predecessor')
    handoff = handoff_before.replace(old_sha, new_sha).replace(
        b"len(rows)!=(6 if kind=='tvshow' else 48)",
        b"len(rows)!=(8 if kind=='tvshow' else 48)")
    search_manifest_path = search_root/'manifest.json'
    search_manifest_before = search_manifest_path.read_bytes()
    search_manifest = json.loads(search_manifest_before)
    rows = [row for row in search_manifest['files']
            if row['path'] == 'resources/lib/search_handoff.py']
    if len(rows) != 1 or rows[0]['sha256'] != digest(handoff_before):
        raise ValueError('catalogue-upgrade-search-manifest')
    rows[0].update(bytes=len(handoff), sha256=digest(handoff))
    search_manifest_raw = encoded(search_manifest)
    search_sha = digest(search_manifest_raw)

    family['components']['aster-series-preview24'].update(
        files=8, manifest_sha256=installed_sha)
    family['components']['aster-global-search-ui22'].update(
        files=len(search_manifest['files']), manifest_sha256=search_sha)
    family['skin']['tools/aster_v2_series.py'] = digest(launcher)
    family_new = encoded(family)

    replacements = {
        'skin/tools/aster_v2_series.py': (launcher_before, launcher),
        'addon/aster-global-search-ui22/resources/lib/search_handoff.py':
            (handoff_before, handoff),
        'addon/aster-global-search-ui22/manifest.json':
            (search_manifest_before, search_manifest_raw),
        'addon/family-manifest.json': (family_raw, family_new),
    }
    rows = []
    for relative, (before, after) in sorted(replacements.items()):
        path = output/'replacements'/relative; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(after)
        rows.append(dict(path=relative, before_sha256=digest(before),
                         sha256=digest(after), bytes=len(after)))
    manifest = dict(schema=1, kind='hp-series-catalogue-upgrade.v1',
        component='aster-series-preview24',
        before_component_manifest_sha256=digest(old_manifest_raw),
        component_manifest_sha256=installed_sha,
        component_files=len(files), replacements=rows)
    here = Path(__file__).resolve().parent
    helpers = {'series_catalogue_upgrade_install.py': here/'series_catalogue_upgrade_install.py',
               'deploy_series_catalogue.py': here/'tools/deploy_series_catalogue.py'}
    manifest['helpers'] = {}
    for name, source_path in helpers.items():
        raw = source_path.read_bytes(); (output/name).write_bytes(raw)
        manifest['helpers'][name] = digest(raw)
    (output/'manifest.json').write_bytes(encoded(manifest))
    return digest((output/'manifest.json').read_bytes())


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--active-addon',required=True);parser.add_argument('--active-skin',required=True)
    parser.add_argument('--candidate',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();print(build(args.active_addon,args.active_skin,args.candidate,args.output))
