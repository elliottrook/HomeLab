"""Build a clean recovery bundle from the verified active HP family.

The active runtime is authoritative for accepted successor bytes.  The retained
family6 checkpoint is authoritative only for the eight pre-family skin files.
The Jellyfin idle-guard checkpoint similarly supplies its exact predecessor.
No profile, database, credential, cache or playback state enters the bundle.
"""
import hashlib
import json
from pathlib import Path

from family_composition import clean_manifest
from family_runtime import COMPONENTS, SKIN_LAUNCHERS, exact_members


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encoded(value):
    return json.dumps(value, indent=2, sort_keys=True).encode() + b'\n'


def write(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def build(addon, skin, family_checkpoint, player, guard_checkpoint, output):
    addon, skin, family_checkpoint = map(Path, (addon, skin, family_checkpoint))
    player, guard_checkpoint, output = map(Path, (player, guard_checkpoint, output))
    require(not output.exists(), 'family-recovery-output-exists')
    require(all(path.is_dir() and not path.is_symlink()
                for path in (addon, skin, family_checkpoint, guard_checkpoint)),
            'family-recovery-source')

    family_raw = (addon/'family-manifest.json').read_bytes()
    family = json.loads(family_raw)
    require(family.get('kind') == 'aster-family-runtime.v1'
            and set(family.get('components', {})) == set(COMPONENTS)
            and isinstance(family.get('skin'), dict), 'family-recovery-contract')

    payload = output/'script.asterruntime'
    for name in ('addon.xml', 'default.py', 'music72-manifest.json'):
        write(payload/name, (addon/name).read_bytes())
    write(payload/'family-manifest.json', family_raw)
    write(payload/'shared/runtime_guard.py', (addon/'shared/runtime_guard.py').read_bytes())
    require(sha(payload/'music72-manifest.json') == family['music_manifest_sha256']
            and sha(payload/'shared/runtime_guard.py') ==
            family['shared']['runtime_guard_sha256'], 'family-recovery-shared-drift')

    for name in COMPONENTS:
        component = addon/name
        manifest_raw = (component/'manifest.json').read_bytes()
        require(sha(component/'manifest.json') ==
                family['components'][name]['manifest_sha256'],
                'family-recovery-component-manifest')
        members = exact_members(component)
        require(len(members) == family['components'][name]['files'],
                'family-recovery-component-count')
        write(payload/name/'manifest.json', manifest_raw)
        for relative, raw in members.items():
            write(payload/name/relative, raw)

    # Every skin identity declared by the active family must be exact, including
    # the four Search files that are verified but not owned by family rollback.
    for relative, expected in family['skin'].items():
        require(sha(skin/relative) == expected, 'family-recovery-skin-drift')

    old_manifest = json.loads((family_checkpoint/'manifest.json').read_text())
    require(old_manifest.get('kind') == 'hp-family-release-candidate.v1'
            and json.loads((family_checkpoint/'state.json').read_text()).get('state') == 'installed',
            'family-recovery-old-checkpoint')
    old_rows = {row['path']: row for row in old_manifest.get('skin', [])}
    require(set(old_rows) == set(SKIN_LAUNCHERS), 'family-recovery-old-skin-set')
    skin_rows = []
    for relative in SKIN_LAUNCHERS:
        backup = family_checkpoint/'original'/relative
        require(sha(backup) == old_rows[relative]['before_sha256'],
                'family-recovery-original-drift')
        write(output/'original'/relative, backup.read_bytes())
        write(output/'skin'/relative, (skin/relative).read_bytes())
        skin_rows.append(dict(path=relative, before_sha256=sha(backup),
                              sha256=sha(skin/relative)))

    guard = json.loads((guard_checkpoint/'manifest.json').read_text())
    require(guard.get('kind') == 'hp-jellyfin-idle-guard.v1'
            and json.loads((guard_checkpoint/'state.json').read_text()).get('state') == 'installed'
            and sha(player) == guard.get('sha256')
            and sha(guard_checkpoint/'player.py.before') == guard.get('before_sha256'),
            'family-recovery-guard-drift')
    write(output/'external/player.py', player.read_bytes())
    write(output/'external/player.py.before',
          (guard_checkpoint/'player.py.before').read_bytes())

    # Re-run the debris/staging-reference audit on the assembled runtime.
    addon_rows = clean_manifest(payload)
    manifest = dict(schema=1, kind='aster-family-recovery.v1',
                    family_manifest_sha256=sha(payload/'family-manifest.json'),
                    addon_files=addon_rows, skin=skin_rows,
                    external=[dict(path='.kodi/addons/plugin.video.jellyfin/jellyfin_kodi/player.py',
                                   before_sha256=guard['before_sha256'],
                                   sha256=guard['sha256'], bytes=player.stat().st_size)])
    helpers = (Path(__file__).with_name('family_recovery_install.py'),
               Path(__file__).with_name('tools')/'deploy_family_recovery.py')
    manifest['helpers'] = {}
    for helper in helpers:
        write(output/helper.name, helper.read_bytes())
        manifest['helpers'][helper.name] = sha(output/helper.name)
    (output/'manifest.json').write_bytes(encoded(manifest))
    return sha(output/'manifest.json')



