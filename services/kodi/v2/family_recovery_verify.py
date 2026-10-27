"""Reconstruct both sides of an Aster family recovery bundle in isolation."""
import hashlib
import json
from pathlib import Path
import re


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def copy(source, target):
    source, target = Path(source), Path(target)
    require(source.is_file() and not source.is_symlink(), 'family-rehearsal-source')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())


def rehearse(bundle, output, pin):
    bundle, output = Path(bundle), Path(output)
    require(not output.exists(), 'family-rehearsal-output-exists')
    require(re.fullmatch('[0-9a-f]{64}', pin or '') and sha(bundle/'manifest.json') == pin,
            'family-rehearsal-pin')
    manifest = json.loads((bundle/'manifest.json').read_text())
    require(manifest.get('kind') == 'aster-family-recovery.v1',
            'family-rehearsal-contract')
    baseline, active = output/'baseline', output/'active'
    external = manifest.get('external', [])
    require(len(external) == 1, 'family-rehearsal-external')
    player = external[0]

    for row in manifest.get('skin', []):
        relative = Path(row['path'])
        require(not relative.is_absolute() and '..' not in relative.parts,
                'family-rehearsal-skin-path')
        copy(bundle/'original'/relative, baseline/'skin'/relative)
        copy(bundle/'skin'/relative, active/'skin'/relative)
        require(sha(baseline/'skin'/relative) == row['before_sha256']
                and sha(active/'skin'/relative) == row['sha256'],
                'family-rehearsal-skin-drift')
    copy(bundle/'external/player.py.before', baseline/player['path'])
    copy(bundle/'external/player.py', active/player['path'])
    require(sha(baseline/player['path']) == player['before_sha256']
            and sha(active/player['path']) == player['sha256'],
            'family-rehearsal-player-drift')
    for row in manifest.get('addon_files', []):
        relative = Path(row['path'])
        require(not relative.is_absolute() and '..' not in relative.parts,
                'family-rehearsal-addon-path')
        copy(bundle/'script.asterruntime'/relative,
             active/'addon/script.asterruntime'/relative)
        target = active/'addon/script.asterruntime'/relative
        require(target.stat().st_size == row['bytes'] and sha(target) == row['sha256'],
                'family-rehearsal-addon-drift')
    require(sha(active/'addon/script.asterruntime/family-manifest.json') ==
            manifest['family_manifest_sha256'], 'family-rehearsal-family-manifest')
    verified_skin = manifest.get('verified_skin', [])
    if verified_skin:
        family = json.loads((active/'addon/script.asterruntime/family-manifest.json').read_text())
        require(len(verified_skin) == len(family['skin'])
                and {row['path']: row['sha256'] for row in verified_skin}
                == family['skin'], 'family-rehearsal-reference-set')
        for row in verified_skin:
            relative = Path(row['path'])
            require(not relative.is_absolute() and '..' not in relative.parts,
                    'family-rehearsal-reference-path')
            destination = active/'verified-skin'/relative
            copy(bundle/'verified-skin'/relative, destination)
            require(destination.stat().st_size == row['bytes']
                    and sha(destination) == row['sha256'],
                    'family-rehearsal-reference-drift')
        addon = active/'addon/script.asterruntime'
        for name, row in family['components'].items():
            require(sha(addon/name/'manifest.json') == row['manifest_sha256'],
                    'family-rehearsal-component-manifest')
        require(sha(addon/'music72-manifest.json') == family['music_manifest_sha256']
                and sha(addon/'shared/runtime_guard.py') ==
                family['shared']['runtime_guard_sha256'],
                'family-rehearsal-shared')
    return dict(passed=True, baseline_skin=len(manifest['skin']),
                active_skin=len(manifest['skin']), addon_files=len(manifest['addon_files']),
                verified_skin=len(verified_skin),
                external_files=len(external), manifest_sha256=pin)

