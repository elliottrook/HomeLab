#!/usr/bin/env python3
"""Repair the HP voice pilot's two manifest links and persistent mic source."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


SEARCH = Path('/storage/.kodi/addons/script.asterruntime/aster-global-search-ui22')
SKIN = Path('/storage/.kodi/addons/skin.asterhome/1080i/custom_1127_search.xml')
FAMILY = Path('/storage/.kodi/addons/script.asterruntime/family-manifest.json')
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-voice-search1/integration-repair-20261027')
PULSE = Path('/storage/.config/pulse-daemon.conf.d')
CONFIG = PULSE / '50-aster-g20-mic.conf'
SCRIPT = PULSE / 'aster-g20-mic.pa'
SOURCE = Path(__file__).resolve().parent.parent / 'config'

PINS = {
    'runtime': '098a07e63b28efba7a47ad72b867e25a25b5067cd4a2174b4f2f9b0bd94242de',
    'skin': 'cbf80fd89bf06bb55601a3edec328d87a14a79e40fb59d5ec02dfe05a834a9b4',
    'search_manifest': 'bc4b0938ad96a6e0c5f89a991389edc1d46f9b927f2f87735981ad4b483309ca',
    'family_manifest': 'c865df1863d8511a6685f491588746cfd255854ccc96ada4d2fbcf7b6dd66247',
}


def require(value, reason):
    if not value:
        raise RuntimeError(reason)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path, raw, mode=0o600):
    temporary = path.with_name('.' + path.name + '.aster-new')
    with temporary.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.chmod(mode)
    os.replace(temporary, path)


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def main():
    require(os.uname().nodename == 'AsterTV', 'hp-only')
    runtime = SEARCH / 'default.py'
    search_manifest = SEARCH / 'manifest.json'
    require(digest(runtime) == PINS['runtime'], 'voice-runtime-drift')
    require(digest(SKIN) == PINS['skin'], 'voice-skin-drift')
    require(digest(search_manifest) == PINS['search_manifest'], 'search-manifest-drift')
    require(digest(FAMILY) == PINS['family_manifest'], 'family-manifest-drift')
    require(not CHECKPOINT.exists(), 'repair-checkpoint-present')
    require(not CONFIG.exists() and not SCRIPT.exists(), 'pulse-config-present')
    require((SOURCE / CONFIG.name).is_file() and (SOURCE / SCRIPT.name).is_file(),
            'pulse-payload-missing')
    sources = subprocess.run(['pactl', 'list', 'short', 'sources'], check=True,
                             capture_output=True, text=True, timeout=5).stdout
    require(sum(line.split()[1] == 'aster_g20_mic' for line in sources.splitlines()) == 1,
            'live-microphone-source-missing')

    search = json.loads(search_manifest.read_text())
    rows = [row for row in search.get('files', []) if row.get('path') == 'default.py']
    require(len(rows) == 1 and rows[0].get('sha256') ==
            'f5de435f74c67ce42dbe063323dba9e8930a78663ad193419e9d6fb5ab14764d',
            'search-runtime-predecessor')
    rows[0]['sha256'] = PINS['runtime']
    rows[0]['bytes'] = runtime.stat().st_size
    new_search = encoded(search)
    new_search_digest = hashlib.sha256(new_search).hexdigest()

    family = json.loads(FAMILY.read_text())
    require(family['components']['aster-global-search-ui22']['manifest_sha256'] ==
            PINS['search_manifest'], 'family-component-predecessor')
    require(family['skin']['1080i/custom_1127_search.xml'] ==
            'c7f85dc09859db9b4bf7aa3b971564e696e45c021b1880dc4c72913e202b043d',
            'family-skin-predecessor')
    family['components']['aster-global-search-ui22']['manifest_sha256'] = new_search_digest
    family['skin']['1080i/custom_1127_search.xml'] = PINS['skin']
    new_family = encoded(family)

    CHECKPOINT.mkdir(mode=0o700, parents=True)
    shutil.copy2(search_manifest, CHECKPOINT / 'search-manifest.json')
    shutil.copy2(FAMILY, CHECKPOINT / 'family-manifest.json')
    atomic(CHECKPOINT / 'state.json', encoded({
        'schema': 1,
        'pulse_config_absent': True,
        'search_manifest_sha256': PINS['search_manifest'],
        'family_manifest_sha256': PINS['family_manifest'],
    }))
    try:
        PULSE.mkdir(mode=0o700, parents=True, exist_ok=True)
        atomic(CONFIG, (SOURCE / CONFIG.name).read_bytes())
        atomic(SCRIPT, (SOURCE / SCRIPT.name).read_bytes())
        atomic(search_manifest, new_search)
        atomic(FAMILY, new_family)
        installed_search = json.loads(search_manifest.read_text())
        installed_family = json.loads(FAMILY.read_text())
        require(next(row for row in installed_search['files']
                     if row['path'] == 'default.py')['sha256'] == PINS['runtime'],
                'search-manifest-not-advanced')
        require(installed_family['components']['aster-global-search-ui22']
                ['manifest_sha256'] == digest(search_manifest),
                'family-component-not-advanced')
        require(installed_family['skin']['1080i/custom_1127_search.xml'] == PINS['skin'],
                'family-skin-not-advanced')
        require(CONFIG.stat().st_mode & 0o777 == 0o600 and
                SCRIPT.stat().st_mode & 0o777 == 0o600, 'pulse-config-mode')
    except Exception:
        atomic(search_manifest, (CHECKPOINT / 'search-manifest.json').read_bytes())
        atomic(FAMILY, (CHECKPOINT / 'family-manifest.json').read_bytes())
        if CONFIG.exists():
            CONFIG.unlink()
        if SCRIPT.exists():
            SCRIPT.unlink()
        raise
    print(json.dumps({
        'repaired': True,
        'search_manifest_sha256': digest(search_manifest),
        'family_manifest_sha256': digest(FAMILY),
        'persistent_source': 'aster_g20_mic',
        'checkpoint': str(CHECKPOINT),
    }, sort_keys=True))


if __name__ == '__main__':
    main()
