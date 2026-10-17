"""One-shot sanitized HA/Frigate status -> disposable Mac Kodi Home feed.

Run manually. No camera frame, URL, token or Home Assistant credential crosses
the boundary. Source-local commands project only the approved fields.
"""

import json
import os
import shlex
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from hub_feeds import MAX_BYTES, home_view


SOURCE = '/mnt/data/supervisor/share/aster-home-registry/latest.json'
DESTINATION = (Path.home() / 'Library/Application Support/Kodi/userdata/addon_data/'
               'skin.asterhome/feeds/home.json')
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5']


def guest(*argv):
    command = shlex.join(['qm', 'guest', 'exec', '103', '--', *argv])
    result = subprocess.run(SSH + ['proxmox', command], capture_output=True,
                            check=True, timeout=20)
    reply = json.loads(result.stdout)
    if reply.get('exitcode') != 0 or reply.get('out-truncated') != 0:
        raise ValueError('Guest read failed or was truncated')
    return reply.get('out-data', '').strip()


def camera_status():
    projection = ('import json,sys; d=json.load(sys.stdin); '
                  'v=d.get("cameras",{}).get("front_of_house"); '
                  'assert isinstance(v,dict), "camera absent"; '
                  'print(json.dumps({"alias":"Front of house",'
                  '"status":"online" if isinstance(v,dict) and '
                  'float(v.get("camera_fps",0))>0 else "offline"}))')
    command = ('curl -fsS --max-time 5 http://127.0.0.1:5000/api/stats | '
               'python3 -c ' + shlex.quote(projection))
    result = subprocess.run(SSH + ['frigate', command], capture_output=True,
                            check=True, timeout=15)
    return json.loads(result.stdout)


def main():
    modified = int(guest('stat', '-c', '%Y', SOURCE))
    fields = '{schema_version,snapshot_id,lights,temperatures,weather,rooms,entities,timers,media_providers}'
    # QEMU guest-agent text forwarding can mojibake non-ASCII output; JSON
    # escapes preserve the exact unit across the transport.
    snapshot = json.loads(guest('jq', '-ac', fields, SOURCE))
    if snapshot.get('schema_version') != 3 or snapshot.get('snapshot_id') != 'ha-home-pilot-v3':
        raise ValueError('Unexpected Home snapshot')
    if any(snapshot.get(key) != [] for key in ('rooms', 'entities', 'timers', 'media_providers')):
        raise ValueError('Unexpected Home aliases')
    if any(item.get('alias') != 'laundry lights' for item in snapshot.get('lights', [])):
        raise ValueError('Unexpected light alias')
    if any(item.get('alias') not in {'hall temperature', 'outside temperature',
                                      'closet temperature'} for item in snapshot.get('temperatures', [])):
        raise ValueError('Unexpected temperature alias')
    try:
        snapshot['cameras'] = [camera_status()]
    except (OSError, ValueError, subprocess.SubprocessError):
        snapshot['cameras'] = []  # No stale or invented camera status.
    feed = {'schema_version': 1,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'source_updated_at': datetime.fromtimestamp(modified, timezone.utc).isoformat(),
            'snapshot': snapshot}
    home_view(feed)
    encoded = (json.dumps(feed, ensure_ascii=False, separators=(',', ':')) + '\n').encode()
    if len(encoded) > MAX_BYTES:
        raise ValueError('Home feed exceeds size limit')
    DESTINATION.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.home.', dir=DESTINATION.parent)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, DESTINATION)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(f'Installed read-only Home feed: {len(snapshot["lights"])} light, '
          f'{len(snapshot["temperatures"])} temperatures, '
          f'{len(snapshot["weather"])} weather, '
          f'{len(snapshot["cameras"])} camera status')


if __name__ == '__main__':
    main()
