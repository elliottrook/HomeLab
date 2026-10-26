"""Compose accepted HP helpers into one deterministic installed runtime."""
import argparse
import json
from pathlib import Path
import re

from family_composition import clean_manifest
from family_runtime import (ADDON, COMPONENTS, INSTALL, SKIN_LAUNCHERS,
                            component_manifest, digest, exact_members)


OLD_PREFIX = b'/storage/.aster-staging/'
NEW_PREFIX = (INSTALL+'/').encode()


def encoded(value):
    return json.dumps(value, indent=2, sort_keys=True).encode()+b'\n'


def replace_exact(raw, old, new, code):
    if raw.count(old) != 1:
        raise ValueError(code)
    return raw.replace(old, new)


def addon_launches(raw):
    pattern = re.compile(rb'RunScript\(/storage/\.aster-staging/([A-Za-z0-9._-]+)/([A-Za-z0-9._-]+)\.py')
    raw = pattern.sub(lambda match: b'RunScript(script.asterruntime,'+match.group(1)+b','+match.group(2), raw)
    return raw.replace(b'RunScript(/storage/.aster-camera/view.py,',
                       b'RunScript(script.asterruntime,aster-camera2,view,')


def rewrite_component(name, files, pins):
    if name == 'aster-camera2':
        files = {'view.py': files['view.py']}
    result = {}
    for path, raw in files.items():
        if path.endswith(('.py', '.xml', '.json')):
            raw = addon_launches(raw)
            raw = raw.replace(OLD_PREFIX, NEW_PREFIX)
        result[path] = raw
    if name == 'aster-digest-player8':
        result.pop('resources/lib/deploy_startup.py')
        result['default.py'] = result['default.py'].replace(
            b'import deploy_startup as guard',
            ("sys.path.insert(0,'"+INSTALL+"/shared')\nimport runtime_guard as guard").encode())
        result['resources/lib/runtime_guard.py'] = pins['runtime_guard']
    if name == 'aster-network-preview5':
        result['default.py'] = result['default.py'].replace(
            b'import deploy_startup as guard', b'import runtime_guard as guard')
        result['default.py'] = result['default.py'].replace(
            (INSTALL+'/aster-digest-player8/resources/lib').encode(),
            (INSTALL+'/shared').encode())
    if name == 'aster-home-status1':
        # Only manifest-approved display files are present. Deployment helpers,
        # source snapshots and private feed material never enter this package.
        result['default.py'] = result['default.py'].replace(
            ("SCRIPT='"+INSTALL+"/aster-home-status1/default.py'").encode(),
            b"SCRIPT='script.asterruntime,aster-home-status1,default'")
        result['default.py'] = result['default.py'].replace(
            b"'AlarmClock(AsterHomeStatus,RunScript('+SCRIPT+',tick)",
            b"'AlarmClock(AsterHomeStatus,RunScript('+SCRIPT+',tick)")
        result['default.py'] = replace_exact(
            result['default.py'], b"        hub_data.main('home')\n",
            (b"        for key,value in (('TimerDigital','--:--'),('TimerSecond','0'),\n"
             b"                          ('TimerActive','false'),('TimerExpired','false'),\n"
             b"                          ('TimerName','No active timer'),('TimerLabel','Not connected')):\n"
             b"            if not window.getProperty('AsterHub.Home'+key):\n"
             b"                window.setProperty('AsterHub.Home'+key,value)\n"),
            'family-runtime-home-legacy-feed-call')
    if name == 'aster-camera2':
        result['view.py'] = result['view.py'].replace(
            b"SCRIPT='/storage/.aster-camera/view.py'",
            b"SCRIPT='script.asterruntime,aster-camera2,view'")
    if name == 'aster-global-search-ui22':
        handoff = result['resources/lib/search_handoff.py']
        handoff = handoff.replace(
            ("'RunScript("+INSTALL+"/'+MOVIE_STAGE+'/movie.py,'").encode(),
            b"'RunScript(script.asterruntime,'+MOVIE_STAGE+',movie,'")
        old_series = re.search(rb"SERIES_SHA='([0-9a-f]{64})'", handoff)
        if not old_series:
            raise ValueError('family-runtime-series-pin-source')
        handoff = handoff.replace(old_series.group(1), pins['series'].encode())
        handoff = handoff.replace(
            b"stage=storage/'.aster-staging'/('aster-series-preview24' if kind=='tvshow' else 'aster-music-v2lab-0.1.0-candidate72')",
            b"stage=(storage/'.kodi/addons/script.asterruntime/aster-series-preview24' if kind=='tvshow' else storage/'.kodi/addons/script.asterruntime')")
        handoff = handoff.replace(
            b"raw=(stage/'manifest.json').read_bytes()",
            b"raw=(stage/'manifest.json' if kind=='tvshow' else stage/'music72-manifest.json').read_bytes()")
        result['resources/lib/search_handoff.py'] = handoff
        default = result['default.py']
        start = default.index(b"        native=next(r for r in manifest['files'] if r['path']=='overlay/custom_1127_search.xml')")
        end = default.index(b"        for key in ('Command'", start)
        installed = b'''        family=json.loads((Path('/storage/.kodi/addons/script.asterruntime/family-manifest.json')).read_text())\n        accepted=family['skin']\n        for relative in ('1080i/custom_1127_search.xml','1080i/custom_1128_searchdetails.xml',\n                         'tools/select_dispatch.py','1080i/Home.xml','1080i/custom_1129_artistalbums.xml'):\n            target=Path('/storage/.kodi/addons/skin.asterhome')/relative\n            require(not target.is_symlink() and hashlib.sha256(target.read_bytes()).hexdigest()==accepted[relative],\n                    'installed-search-integration-not-verified')\n'''
        result['default.py'] = default[:start]+installed+default[end:]
        player = result['resources/lib/movie_player.py']
        start = player.index(b'def verify_stage(')
        end = player.index(b'\n@dataclass', start)
        verify = b'''def verify_stage(storage=Path('/storage')):\n    root=storage/'.kodi/addons/script.asterruntime'/MOVIE_STAGE\n    try:\n        family=json.loads((storage/'.kodi/addons/script.asterruntime/family-manifest.json').read_text())\n        expected=family['components'][MOVIE_STAGE]['manifest_sha256']\n        raw=(root/'manifest.json').read_bytes();require(hashlib.sha256(raw).hexdigest()==expected,'movie-runtime-manifest')\n        manifest=json.loads(raw);require(manifest.get('component')==MOVIE_STAGE,'movie-runtime-kind')\n        for row in manifest['files']:\n            path=root/row['path'];require(not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'],'movie-runtime-drift')\n        for name,expected in GUARDS.items():\n            path=storage/'.kodi/addons'/name\n            require(not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest()==expected,'movie-playback-guard-drift')\n    except (OSError,KeyError,TypeError,ValueError):raise MovieUnavailable('movie-runtime-or-guard-unavailable') from None\n'''
        result['resources/lib/movie_player.py'] = player[:start]+verify+player[end:]
    return result


def build(skin, runtime, output):
    skin, runtime, output = Path(skin), Path(runtime), Path(output)
    if output.exists():
        raise ValueError('immutable-family-runtime-output')
    output.mkdir(parents=True)
    addon = output/ADDON
    addon.mkdir()
    here = Path(__file__).resolve().parent
    source = {}
    for name in COMPONENTS:
        folder = runtime/name
        raw = (folder/'manifest.json').read_bytes()
        source[name] = dict(folder=folder, manifest_sha=digest(raw),
                            manifest=json.loads(raw), files=exact_members(folder))
    pins = dict(runtime_guard=(here/'runtime_guard.py').read_bytes())
    # Search verifies the transformed installed series manifest.
    series_files = rewrite_component('aster-series-preview24',
                                     source['aster-series-preview24']['files'], pins)
    series_manifest = encoded(component_manifest('aster-series-preview24', series_files,
                              source['aster-series-preview24']['manifest_sha'],
                              source['aster-series-preview24']['manifest']))
    pins['series'] = digest(series_manifest)
    components = {}
    for name in COMPONENTS:
        files = series_files if name == 'aster-series-preview24' else rewrite_component(
            name, source[name]['files'], pins)
        if name == 'aster-digest-player8':
            # Shared guard is one installed authority, not duplicated code.
            files.pop('resources/lib/runtime_guard.py')
        folder = addon/name
        for relative, raw in sorted(files.items()):
            target = folder/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        manifest = series_manifest if name == 'aster-series-preview24' else encoded(
            component_manifest(name, files, source[name]['manifest_sha'],
                               source[name]['manifest']))
        (folder/'manifest.json').write_bytes(manifest)
        components[name] = dict(manifest_sha256=digest(manifest), files=len(files))
    shared = addon/'shared'
    shared.mkdir()
    (shared/'runtime_guard.py').write_bytes(pins['runtime_guard'])
    (addon/'music72-manifest.json').write_bytes((runtime/'music72-manifest.json').read_bytes())
    addon_xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<addon id="script.asterruntime" name="Aster Runtime" version="2.0.0" provider-name="Aster Home">\n'
        '  <requires><import addon="xbmc.python" version="3.0.0"/></requires>\n'
        '  <extension point="xbmc.python.script" library="default.py"><provides>executable</provides></extension>\n'
        '  <extension point="xbmc.addon.metadata"><summary lang="en_GB">Private Aster page runtime</summary><description lang="en_GB">Verified local page controllers for the Aster television interface.</description><platform>all</platform><license>Private HomeLab</license></extension>\n'
        '</addon>\n').encode()
    (addon/'addon.xml').write_bytes(addon_xml)
    dispatcher = b'''"""Strict dispatcher for Aster's installed page runtime."""\nimport runpy\nfrom pathlib import Path\nimport sys\n\nROOT=Path(__file__).resolve().parent\nCOMPONENTS={"aster-camera2","aster-digest-player8","aster-digest-reader6","aster-global-search-ui22",\n "aster-home-status1","aster-network-preview5","aster-series-preview24","aster-video-scrub5"}\nENTRIES={"default":"default.py","movie":"movie.py","view":"view.py"}\nif len(sys.argv)>=3 and sys.argv[1] in COMPONENTS and sys.argv[2] in ENTRIES:\n path=ROOT/sys.argv[1]/ENTRIES[sys.argv[2]]\n if path.is_file() and not path.is_symlink():\n  sys.argv=[str(path)]+sys.argv[3:]\n  runpy.run_path(str(path),run_name="__main__")\n'''
    (addon/'default.py').write_bytes(dispatcher)
    old_to_new = {source[name]['manifest_sha']: components[name]['manifest_sha256']
                  for name in COMPONENTS}
    skin_rows = []
    skin_hashes = {}
    for relative in SKIN_LAUNCHERS:
        original = (skin/relative).read_bytes()
        raw = addon_launches(original)
        raw = raw.replace(OLD_PREFIX, NEW_PREFIX)
        if relative == 'tools/aster_v2_digest.py':
            raw = raw.replace(b"'RunScript('+str(PLAYER/'default.py')+','+','.join(args)+')'",
                              b"'RunScript(script.asterruntime,aster-digest-player8,default,'+','.join(args)+')'")
        if relative == 'tools/aster_v2_series.py':
            raw = raw.replace(b"'RunScript('+str(STAGE/'default.py')+','+str(identity)+',play)'",
                              b"'RunScript(script.asterruntime,aster-series-preview24,default,'+str(identity)+',play)'")
        for old, new in old_to_new.items():
            raw = raw.replace(old.encode(), new.encode())
        if raw == original:
            raise ValueError('family-runtime-launcher-not-transformed:'+relative)
        target = output/'skin'/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        skin_rows.append(dict(path=relative, before_sha256=digest(original),
                              sha256=digest(raw)))
        skin_hashes[relative] = digest(raw)
    for relative in ('1080i/custom_1127_search.xml', '1080i/custom_1128_searchdetails.xml',
                     '1080i/custom_1129_artistalbums.xml', 'tools/select_dispatch.py'):
        raw = (skin/relative).read_bytes()
        skin_hashes[relative] = digest(raw)
    family = dict(schema=1, kind='aster-family-runtime.v1', components=components,
                  music_manifest_sha256=digest((runtime/'music72-manifest.json').read_bytes()),
                  shared=dict(runtime_guard_sha256=digest(pins['runtime_guard'])),
                  skin=skin_hashes)
    (addon/'family-manifest.json').write_bytes(encoded(family))
    clean_manifest(addon)
    candidate = dict(schema=1, kind='hp-family-release-candidate.v1',
                     addon=ADDON, addon_files=clean_manifest(addon), skin=skin_rows)
    helpers = {
        'family_runtime_install.py': here/'family_runtime_install.py',
        'deploy_family_runtime.py': here/'tools/deploy_family_runtime.py',
        'digest_news_install.py': here/'digest_news_install.py',
    }
    candidate['helpers'] = {}
    for name, path in helpers.items():
        raw = path.read_bytes()
        (output/name).write_bytes(raw)
        candidate['helpers'][name] = digest(raw)
    (output/'manifest.json').write_bytes(encoded(candidate))
    return digest((output/'manifest.json').read_bytes())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--skin', required=True)
    parser.add_argument('--runtime', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(build(args.skin, args.runtime, args.output))
