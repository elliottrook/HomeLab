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
}
TARGETS = {
    'runtime-search.py': '/storage/.kodi/addons/script.asterruntime/aster-global-search-ui22/default.py',
    'custom_1127_search.xml': '/storage/.kodi/addons/skin.asterhome/1080i/custom_1127_search.xml',
    'g20s-pro-plus.xml': '/storage/.kodi/userdata/keymaps/g20s-pro-plus.xml',
}
LIBRARIES = (
    'global_search.py', 'voice_search.py', 'voice_capture.py',
    'voice_capture_runner.py', 'voice_search_stt.py', 'voice_search_ui.py',
    'voice_search_runtime.py', 'voice_search_attempt.py',
    'voice_search_transport.py', 'voice_release.py', 'voice_native_policy.py',
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, indent=2, sort_keys=True).encode() + b'\n'


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
    for name, raw in replacements.items():
        (payload / name).write_bytes(raw)
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
        'privacy': {'capture': 'explicit-hold-only', 'maximum_seconds': 10,
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
