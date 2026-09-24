"""OPNsense source-local narrow UI rule; dry-run unless --apply is provided."""
import copy
import json
import os
from pathlib import Path
import re
import sys
import time
import xml.etree.ElementTree as E

path = Path('/conf/config.xml')
raw = path.read_text()
root = E.fromstring(raw)
source_id = 'd43f8bac-aec7-4f47-93dc-450afb86c9db'
target_id = 'fdc0bfb3-9dd4-4bca-869c-a571f8d64f02'
source = next(r for r in root.iter('rule') if r.get('uuid') == source_id)
expected = {'source_net': 'MGMT_ADMIN_HOSTS', 'interface': 'lan',
            'destination_net': '192.168.70.13', 'destination_port': '8080',
            'protocol': 'TCP', 'action': 'pass', 'enabled': '1', 'quick': '1'}
assert all(source.findtext(k) == v for k, v in expected.items()), 'Reference rule drift'
assert not any(r.get('uuid') == target_id for r in root.iter('rule')), 'Rule already exists'
assert not any(r.findtext('sequence') == '3151' for r in root.iter('rule')), 'Sequence in use'
assert not any(r.findtext('destination_net') == '192.168.70.15' and r.findtext('destination_port') == '8000' for r in root.iter('rule')), 'Inspect existing target rule'
match = re.search(r'<rule uuid="' + source_id + r'">.*?</rule>', raw, re.S)
assert match
candidate = match.group().replace(source_id, target_id).replace('<sequence>3150</sequence>', '<sequence>3151</sequence>').replace('<destination_net>192.168.70.13</destination_net>', '<destination_net>192.168.70.15</destination_net>').replace('<destination_port>8080</destination_port>', '<destination_port>8000</destination_port>')
candidate = re.sub(r'<description>.*?</description>', '<description>Allow approved administrators to Paperless UI (LXC 115)</description>', candidate, flags=re.S)
new = raw[:match.end()] + '\n          ' + candidate + raw[match.end():]
parsed = E.fromstring(new)
assert len(list(parsed.iter('rule'))) == len(list(root.iter('rule'))) + 1
print(json.dumps({'rule_uuid': target_id, 'source': 'MGMT_ADMIN_HOSTS',
                  'destination': '192.168.70.15:8000/TCP', 'interface': 'lan',
                  'mode': 'apply' if '--apply' in sys.argv else 'dry-run'}))
if '--apply' in sys.argv:
    backup = Path('/conf/backup') / ('config-paperless-ui-before-' + time.strftime('%Y%m%d-%H%M%S') + '.xml')
    fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(raw)
    meta = path.stat()
    temporary = path.with_name('config.xml.paperless-candidate')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(new)
        stream.flush()
        os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), meta.st_mode & 0o777)
        os.fchown(stream.fileno(), meta.st_uid, meta.st_gid)
    os.replace(temporary, path)
    print(json.dumps({'backup': str(backup), 'reload_pending': True}))
