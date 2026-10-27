"""Build the immutable HP voice-search pilot from exact active predecessors."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from voice_keymap import build as keymap
from voice_search_patch import controller, window


PINS = {
    'runtime-search.py': 'f5de435f74c67ce42dbe063323dba9e8930a78663ad193419e9d6fb5ab14764d',
    'custom_1127_search.xml': 'c7f85dc09859db9b4bf7aa3b971564e696e45c021b1880dc4c72913e202b043d',
    'g20s-pro-plus.xml': '1c3661aa1c9109b9390b9004203ce6cbe53d03d559f88a019db01d22a430d2c1',
    'search-manifest.json': 'bc4b0938ad96a6e0c5f89a991389edc1d46f9b927f2f87735981ad4b483309ca',
    'family-manifest.json': 'c865df1863d8511a6685f491588746cfd255854ccc96ada4d2fbcf7b6dd66247',
}
TARGETS = {
    'runtime-search.py': '/storage/.kodi/addons/script.asterruntime/aster-global-search-ui22/default.py',
    'custom_1127_search.xml': '/storage/.kodi/addons/skin.asterhome/1080i/custom_1127_search.xml',
    'g20s-pro-plus.xml': '/storage/.kodi/userdata/keymaps/g20s-pro-plus.xml',
    'search-manifest.json': '/storage/.kodi/addons/script.asterruntime/aster-global-search-ui22/manifest.json',
    'family-manifest.json': '/storage/.kodi/addons/script.asterruntime/family-manifest.json',
}
LIBRARIES = (
    'global_search.py', 'voice_search.py', 'voice_capture.py',
    'voice_capture_runner.py', 'voice_search_stt.py', 'voice_search_ui.py',
    'voice_search_runtime.py', 'voice_search_attempt.py',
    'voice_search_transport.py', 'voice_release.py', 'voice_native_policy.py',
)
HWDB_NAME = '99-aster-g20-voice.hwdb'
HWDB_TARGET = '/storage/.config/hwdb.d/' + HWDB_NAME
PULSE_FILES = {
    '50-aster-g20-mic.conf': '/storage/.config/pulse-daemon.conf.d/50-aster-g20-mic.conf',
    'aster-g20-mic.pa': '/storage/.config/pulse-daemon.conf.d/aster-g20-mic.pa',
}
EVENTLIRCD_NAME = 'eventlircd-aster-retry.conf'
EVENTLIRCD_TARGET = '/storage/.config/system.d/eventlircd.service.d/aster-retry.conf'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, indent=2, sort_keys=True).encode() + b'\n'


def integrated_manifests(search_raw, family_raw, runtime_raw, window_raw):
    search = json.loads(search_raw)
    rows = [row for row in search.get('files', []) if row.get('path') == 'default.py']
    if (len(rows) != 1 or rows[0].get('sha256') != PINS['runtime-search.py']
            or type(rows[0].get('bytes')) is not int or rows[0]['bytes'] <= 0):
        raise ValueError('voice-search-manifest-drift')
    rows[0].update(bytes=len(runtime_raw), sha256=digest(runtime_raw))
    search_result = encoded(search)
    family = json.loads(family_raw)
    component = family.get('components', {}).get('aster-global-search-ui22', {})
    skin = family.get('skin', {})
    if (component.get('manifest_sha256') != PINS['search-manifest.json']
            or skin.get('1080i/custom_1127_search.xml') != PINS['custom_1127_search.xml']):
        raise ValueError('voice-family-manifest-drift')
    component['manifest_sha256'] = digest(search_result)
    skin['1080i/custom_1127_search.xml'] = digest(window_raw)
    return search_result, encoded(family)


def build(predecessors, output):
    predecessors, output = Path(predecessors), Path(output)
    if output.exists():
        raise ValueError('immutable-voice-output')
    source = {name: (predecessors / name).read_bytes() for name in PINS}
    if {name: digest(raw) for name, raw in source.items()} != PINS:
        raise ValueError('voice-predecessor-drift')
    output.mkdir(parents=True)
    payload = output / 'payload'
    addon = payload / 'script.astervoice.v2lab'
    library = addon / 'resources/lib'
    library.mkdir(parents=True)
    here = Path(__file__).resolve().parent
    shutil.copyfile(here / 'script.astervoice.v2lab/addon.xml', addon / 'addon.xml')
    shutil.copyfile(here / 'script.astervoice.v2lab/default.py', addon / 'default.py')
    for name in LIBRARIES:
        shutil.copyfile(here / name, library / name)
    replacements = {
        'runtime-search.py': controller(source['runtime-search.py']),
        'custom_1127_search.xml': window(source['custom_1127_search.xml']),
        'g20s-pro-plus.xml': keymap(source['g20s-pro-plus.xml']),
    }
    search_manifest, family_manifest = integrated_manifests(
        source['search-manifest.json'], source['family-manifest.json'],
        replacements['runtime-search.py'], replacements['custom_1127_search.xml'])
    replacements['search-manifest.json'] = search_manifest
    replacements['family-manifest.json'] = family_manifest
    for name, raw in replacements.items():
        (payload / name).write_bytes(raw)
    shutil.copyfile(here / 'config' / HWDB_NAME, payload / HWDB_NAME)
    for name in PULSE_FILES:
        shutil.copyfile(here / 'config' / name, payload / name)
    shutil.copyfile(here / 'config' / EVENTLIRCD_NAME, payload / EVENTLIRCD_NAME)
    addon_rows = []
    for path in sorted(addon.rglob('*')):
        if path.is_file():
            relative = path.relative_to(addon).as_posix()
            addon_rows.append({'path': relative, 'bytes': path.stat().st_size,
                               'sha256': digest(path.read_bytes())})
    manifest = {
        'schema': 1, 'kind': 'hp-voice-search-pilot.v1',
        'addon': {'id': 'script.astervoice.v2lab', 'files': addon_rows},
        'replacements': [
            {'path': name, 'target': TARGETS[name], 'before_sha256': PINS[name],
             'sha256': digest(replacements[name])}
            for name in sorted(replacements)
        ],
        'installs': [{
            'path': HWDB_NAME,
            'target': HWDB_TARGET,
            'sha256': digest((payload / HWDB_NAME).read_bytes()),
        }] + [dict(path=name, target=PULSE_FILES[name],
                   sha256=digest((payload / name).read_bytes()))
              for name in sorted(PULSE_FILES)] + [{
                  'path': EVENTLIRCD_NAME,
                  'target': EVENTLIRCD_TARGET,
                  'sha256': digest((payload / EVENTLIRCD_NAME).read_bytes()),
              }],
        'privacy': {'capture': 'explicit-single-press', 'maximum_seconds': 4,
                    'audio_retained': False, 'transcript_retained': False,
                    'speech_path': '/v1/stt'},
    }
    helper = here / 'tools/deploy_voice_search.py'
    shutil.copyfile(helper, output / helper.name)
    manifest['helper'] = {'path': helper.name,
                          'sha256': digest((output / helper.name).read_bytes())}
    (output / 'manifest.json').write_bytes(encoded(manifest))
    return digest((output / 'manifest.json').read_bytes())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--predecessors', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(build(args.predecessors, args.output))
