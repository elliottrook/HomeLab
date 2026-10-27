"""Generate the two narrow read-only AsterReader publication mounts."""

from __future__ import annotations


SERVER = '192.168.20.40'
BASE = '/mnt/Media/AsterReader'
TARGET = '/storage/aster-reader'
OPTIONS = 'ro,nosuid,nodev,noexec,relatime,vers=4.2,proto=tcp,soft,timeo=50,retrans=2,_netdev'


def units():
    result = {}
    for leaf in ('ready', 'generations'):
        escaped = 'storage-aster\\x2dreader-' + leaf
        where = TARGET + '/' + leaf
        mount = f'''[Unit]
Description=Aster Books published {leaf} (read-only)
After=network-online.target
Wants=network-online.target

[Mount]
What={SERVER}:{BASE}/{leaf}
Where={where}
Type=nfs
Options={OPTIONS}
TimeoutSec=15
'''.encode()
        automount = f'''[Unit]
Description=Automount Aster Books published {leaf}

[Automount]
Where={where}
TimeoutIdleSec=300

[Install]
WantedBy=multi-user.target
'''.encode()
        result[escaped + '.mount'] = mount
        result[escaped + '.automount'] = automount
    return result
