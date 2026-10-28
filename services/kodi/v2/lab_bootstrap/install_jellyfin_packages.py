"""Install vetted upstream Jellyfin packages on the fresh AsterTV lab only.

Run on the lab after downloading the listed upstream ZIPs into STAGING.
No profile, credential, or production state is copied by this script.
"""

import os
import hashlib
import stat
import zipfile

STAGING = '/storage/.aster-staging/astertv-v2-lab-candidate'
ADDONS = '/storage/.kodi/addons'
PACKAGES = {
    'script.module.websocket': (
        'script.module.websocket-1.6.4.zip',
        '4de56d48fd80d963e48afa810e11d9fea2c44e023d511859a50ae693d771cd86'),
    'script.module.typing_extensions': (
        'script.module.typing_extensions-4.7.1.zip',
        '943aaf77ecca936258ee49a20b294eb2995f7f118599e8b89d537be77e74e646'),
    'plugin.video.jellyfin': (
        'plugin.video.jellyfin-2.2.0+py3.zip',
        '58cc72c0eedc624a98a255f5c95c64b6e0f6f906c9666d0893fee152eb4fb8b1'),
}

if os.uname().nodename != 'AsterTV':
    raise RuntimeError('lab-only installer')

for addon_id, (filename, expected_sha256) in PACKAGES.items():
    destination = os.path.join(ADDONS, addon_id)
    if os.path.lexists(destination):
        raise RuntimeError('target exists: ' + destination)
    path = os.path.join(STAGING, filename)
    with open(path, 'rb') as package:
        if hashlib.sha256(package.read()).hexdigest() != expected_sha256:
            raise RuntimeError('checksum mismatch: ' + filename)
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            path = member.filename
            kind = stat.S_IFMT(member.external_attr >> 16)
            if (not path.startswith(addon_id + '/')
                    or '..' in path.split('/')
                    or kind not in (0, stat.S_IFDIR, stat.S_IFREG)):
                raise RuntimeError('unsafe member: ' + path)
        archive.extractall(ADDONS)
    print('installed', addon_id)
