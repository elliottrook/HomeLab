"""Render an offline bootstrap-canary candidate. Local files only; no ISO or VM I/O."""

import hashlib
import json
from pathlib import Path


IMAGE = {
    'url': ('https://cloud.debian.org/images/cloud/trixie/20260914-2601/'
            'debian-13-generic-amd64-20260914-2601.qcow2'),
    'filename': 'debian-13-generic-amd64-20260914-2601.qcow2',
    'bytes': 433651712,
    'sha512': ('a733e7d49442a03e70d03e4eb5aaf3967f3efc69ef70952f9bb10fc1ee2c4876'
               'eb95956b5ad2d31350e5fada768feb651352535fb8cd1233f61998a5a7d2e93c'),
}
RUN_ID = 'bootstrap-canary-002'
INSTANCE_ID = 'aster-s0-bootstrap-canary-002'
FORBIDDEN = ('reviewed-proposal', 'acceptance.json', 'labeling/pilot-s0',
             'private_context', 'human-review')


CANARY_TEMPLATE = '''"""Generated synthetic bootstrap canary; no external inputs."""
import base64,hashlib,json,pathlib
RUN_ID = {run_id!r}
MANIFEST = {manifest!r}
PREFIX = b'ASTER_S0_V1'
CHUNK = 3072
value = {{'authorization':'not-granted','corpus_evaluated':False,
         'fixture':True,'interfaces':sorted(p.name for p in pathlib.Path('/sys/class/net').iterdir()),
         'result':'bootstrap-canary'}}
raw = json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
if len(raw) > 2*1024*1024: raise SystemExit('result-size')
digest = hashlib.sha256(raw).hexdigest()
parts = [raw[i:i+CHUNK] for i in range(0,len(raw),CHUNK)]
lines = [b' '.join((PREFIX,b'BEGIN',RUN_ID.encode(),MANIFEST.encode(),str(len(raw)).encode(),digest.encode(),str(len(parts)).encode()))]
for sequence,part in enumerate(parts):
    lines.append(b' '.join((PREFIX,b'CHUNK',RUN_ID.encode(),str(sequence).encode(),base64.b64encode(part))))
lines.append(b' '.join((PREFIX,b'END',RUN_ID.encode(),str(len(raw)).encode(),digest.encode())))
out = pathlib.Path('/var/lib/aster-s0/output')
(out/'result.json').write_bytes(raw)
(out/'protocol.txt').write_bytes(b'\\n'.join(lines)+b'\\n')
'''


UNIT = '''[Unit]
Description=Aster S0 synthetic bootstrap canary

[Service]
Type=oneshot
User=aster-s0
Group=aster-s0
WorkingDirectory=/var/lib/aster-s0
ExecStart=/usr/bin/python3 -I -S -B /usr/local/lib/aster-s0/canary.py
StandardOutput=journal
StandardError=journal
NoNewPrivileges=yes
CapabilityBoundingSet=
AmbientCapabilities=
PrivateDevices=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ProtectControlGroups=yes
ProtectKernelModules=yes
ProtectKernelTunables=yes
ProtectKernelLogs=yes
ProtectClock=yes
LockPersonality=yes
MemoryDenyWriteExecute=yes
RestrictRealtime=yes
RestrictSUIDSGID=yes
RestrictAddressFamilies=AF_UNIX
ReadWritePaths=/var/lib/aster-s0/output
MemoryMax=512M
TasksMax=64
CPUQuota=100%
RuntimeMaxSec=90
TimeoutStartSec=90
'''


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_canary(value):
    if type(value) is not dict or set(value) != {
            'authorization', 'corpus_evaluated', 'fixture', 'interfaces', 'result'}:
        raise ValueError('canary shape')
    if (value['authorization'] != 'not-granted' or value['corpus_evaluated'] is not False or
            value['fixture'] is not True or value['result'] != 'bootstrap-canary'):
        raise ValueError('canary claim')
    if value['interfaces'] != ['lo']:
        raise ValueError('unexpected network interface')
    return value


def _literal(text, spaces=6):
    pad = ' ' * spaces
    return ''.join((pad + line if line else '') + '\n' for line in text.splitlines())


def render():
    unit = UNIT.encode('utf-8')
    preliminary = CANARY_TEMPLATE.format(run_id=RUN_ID, manifest='0' * 64).encode('utf-8')
    payload = {
        'schema': 'aster-s0-vm-payload.v1',
        'status': 'bootstrap-canary-only',
        'run_id': RUN_ID,
        'image': IMAGE,
        'limits': {'capture_bytes': 4 * 1024 * 1024, 'result_bytes': 2 * 1024 * 1024,
                   'capture_seconds': 300, 'unit_seconds': 90, 'unit_memory_mib': 512},
        'artifact_templates': {'canary_sha256_with_zero_manifest': sha256(preliminary),
                               'unit_sha256': sha256(unit)},
        'accepted_corpus': 'absent',
        'evaluation_authorized': False,
        'infrastructure_authorized': False,
    }
    payload_raw = canonical(payload)
    payload_digest = sha256(payload_raw)
    canary = CANARY_TEMPLATE.format(run_id=RUN_ID, manifest=payload_digest).encode('utf-8')
    meta = ('instance-id: ' + INSTANCE_ID + '\nlocal-hostname: aster-s0-canary\n').encode()
    user = ("#cloud-config\npackage_update: false\npackage_upgrade: false\n"
            "ssh_pwauth: false\ndisable_root: true\nusers:\n"
            "  - name: aster-s0\n    system: true\n    lock_passwd: true\n"
            "    no_create_home: true\n    shell: /usr/sbin/nologin\n"
            "write_files:\n"
            "  - path: /usr/local/lib/aster-s0/canary.py\n    owner: root:root\n"
            "    permissions: '0444'\n    content: |\n" + _literal(canary.decode()) +
            "  - path: /etc/systemd/system/aster-s0-canary.service\n    owner: root:root\n"
            "    permissions: '0444'\n    content: |\n" + _literal(unit.decode()) +
            "  - path: /usr/local/lib/aster-s0/payload-manifest.json\n    owner: root:root\n"
            "    permissions: '0444'\n    content: |\n" + _literal(payload_raw.decode() + '\n') +
            "runcmd:\n"
            "  - [install, -d, -o, aster-s0, -g, aster-s0, -m, '0700', /var/lib/aster-s0/output]\n"
            "  - [systemctl, daemon-reload]\n"
            "  - [sh, -c, 'systemctl start aster-s0-canary.service; rc=$?; if test \"$rc\" -eq 0; then cat /var/lib/aster-s0/output/protocol.txt > /dev/ttyS0 || rc=$?; fi; sync; systemctl poweroff; exit \"$rc\"']\n"
            "final_message: 'aster-s0 bootstrap completed'\n").encode('utf-8')
    config = {
        'schema': 'aster-s0-vm-config-proposal.v1',
        'vmid': 'allocate-next-free-at-creation',
        'name': 'aster-s0-fixture-<build-id>',
        'options': {'agent': 'absent', 'balloon': 0, 'bios': 'ovmf', 'boot': 'order=scsi0',
                    'cores': 1, 'cpu': 'x86-64-v2-AES', 'hotplug': 0, 'machine': 'q35',
                    'memory_mib': 1024, 'network_devices': [], 'onboot': 0, 'ostype': 'l26',
                    'serial0': 'socket', 'sockets': 1, 'tablet': 0, 'vga': 'serial0'},
        'storage': {'os': 'local-lvm:8GiB,virtio-scsi-single,discard=on,backup=0',
                    'efi': 'local-lvm:4MiB,pre-enrolled-keys=0',
                    'seed': 'local:iso/<reviewed-cidata.iso>,media=cdrom,read-only'},
        'forbidden': ['netN', 'agent', 'hostpci', 'virtiofs', 'usb', 'gpu', 'credentials'],
        'start': False,
    }
    files = {'meta-data': meta, 'user-data': user, 'payload-manifest.json': payload_raw + b'\n',
             'canary.py': canary, 'aster-s0-canary.service': unit,
             'vm-config-proposal.json': canonical(config) + b'\n'}
    for name, raw in files.items():
        if any(token.encode() in raw for token in FORBIDDEN):
            raise ValueError('forbidden corpus marker in ' + name)
    candidate = {
        'schema': 'aster-s0-vm-candidate.v1', 'status': 'local-source-only-not-authorized',
        'run_id': RUN_ID, 'instance_id': INSTANCE_ID, 'payload_manifest_sha256': payload_digest,
        'files': {name: {'bytes': len(raw), 'sha256': sha256(raw)} for name, raw in sorted(files.items())},
        'iso_created': False, 'vm_created': False, 'accepted_corpus_included': False,
    }
    files['candidate-manifest.json'] = canonical(candidate) + b'\n'
    return files


def write_candidate(output):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True, mode=0o700)
    files = render()
    for name, raw in files.items():
        path = output / name
        path.write_bytes(raw)
        path.chmod(0o600)
    return files
