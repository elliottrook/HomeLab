"""Install the checkpointed code-only Aster v2 candidate on a fresh lab Kodi."""

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

ARCHIVE = Path('/storage/.aster-staging/astertv-v2-lab-candidate/astertv-v2-code-only.tar.gz')
EXPECTED_SHA256 = '13d586ae3a30ba03ccc9ea3f2f291e337b814d38dc1805dbbc998d690c4b8f7d'
ADDONS = Path('/storage/.kodi/addons')
CHECKPOINT = Path('/storage/.aster-checkpoints/astertv-v2-fresh-lab-install-20261028')
IDS = {
    'plugin.audio.asterbooks', 'plugin.video.asterhome',
    'resource.uisounds.asterhome', 'screensaver.asterhome.v2lab',
    'script.asteracquisition', 'script.astermusic.v2lab',
    'script.asterruntime', 'script.asterseerr', 'script.astervoice.v2lab',
    'service.aster.playerui', 'service.aster.startup', 'skin.asterhome',
}

if os.uname().nodename != 'AsterTV':
    raise RuntimeError('lab-only installer')
if subprocess.run(['systemctl', 'is-active', '--quiet', 'kodi']).returncode == 0:
    raise RuntimeError('stop Kodi before installing')
if CHECKPOINT.exists():
    raise RuntimeError('checkpoint already exists')
if any((ADDONS / addon_id).exists() for addon_id in IDS):
    raise RuntimeError('Aster add-on target already exists')
if hashlib.sha256(ARCHIVE.read_bytes()).hexdigest() != EXPECTED_SHA256:
    raise RuntimeError('candidate archive checksum mismatch')

with tarfile.open(ARCHIVE, 'r:gz') as archive:
    members = archive.getmembers()
    roots = set()
    for member in members:
        if member.name in ('.', './'):
            continue
        if not member.name.startswith('./'):
            raise RuntimeError('unexpected archive path: ' + member.name)
        parts = member.name[2:].split('/')
        if not parts or parts[0] not in IDS:
            raise RuntimeError('unexpected archive path: ' + member.name)
        if '..' in parts or not (member.isdir() or member.isfile()):
            raise RuntimeError('unsafe archive member: ' + member.name)
        roots.add(parts[0])
    if roots != IDS:
        raise RuntimeError('candidate add-on inventory mismatch')

    CHECKPOINT.mkdir(parents=True, mode=0o700)
    shutil.copytree('/storage/.kodi/userdata', CHECKPOINT / 'userdata.before')
    (CHECKPOINT / 'archive.sha256').write_text(EXPECTED_SHA256 + '\n')
    archive.extractall(ADDONS, filter='data')
    # Tar does not retain the source skin's empty fonts directory. Kodi still
    # probes it while loading its font set, so recreate it deterministically.
    (ADDONS / 'skin.asterhome' / 'fonts').mkdir(mode=0o755, exist_ok=True)

print('installed', len(IDS), 'Aster add-ons; checkpoint', CHECKPOINT)
