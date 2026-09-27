"""Render the offline V3b corrected invented-fixture isolation candidate.

This module only creates local source files.  It cannot create an ISO, VM, or run.
"""

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
RUN_ID = 'isolation-fixture-002'
INSTANCE_ID = 'aster-s0-isolation-fixture-002'
FORBIDDEN = ('reviewed-proposal', 'acceptance.json', 'labeling/pilot-s0',
             'private_context', 'human-review')


PROBE_TEMPLATE = '''"""Generated invented isolation probe; no external inputs."""
import base64,errno,hashlib,json,os,pathlib,socket
RUN_ID = {run_id!r}
MANIFEST = {manifest!r}
PREFIX = b'ASTER_S0_V1'
CHUNK = 3072
EXPECTED_ENV = frozenset({{
    'HOME','INVOCATION_ID','JOURNAL_STREAM','LANG','LC_ALL','LOGNAME',
    'MEMORY_PRESSURE_WATCH','MEMORY_PRESSURE_WRITE','PATH','SHELL',
    'SYSTEMD_EXEC_PID','USER'
}})
keys = frozenset(os.environ)
checks = {{
    'environment_allowlisted': keys <= EXPECTED_ENV,
    'fixed_locale': os.environ.get('LANG') == 'C' and os.environ.get('LC_ALL') == 'C',
    'unprivileged': os.geteuid() != 0,
    'loopback_only': sorted(p.name for p in pathlib.Path('/sys/class/net').iterdir()) == ['lo'],
}}
os.environ.clear()
checks['environment_cleared'] = not os.environ

def denied(name, operation, allowed):
    try:
        operation()
    except OSError as exc:
        checks[name] = exc.errno in allowed
    else:
        checks[name] = False

def socket_attempt(family):
    value = socket.socket(family, socket.SOCK_STREAM)
    value.close()

def fork_attempt():
    child = os.fork()
    if child == 0:
        os._exit(0)
    os.waitpid(child, 0)

def denied_read():
    with open('/srv/aster-s0-isolation-fixture-002/canary', 'rb') as stream:
        stream.read(1)

def denied_write():
    path = '/usr/aster-s0-isolation-fixture-denied'
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    os.unlink(path)

denied('inet_socket_denied', lambda: socket_attempt(socket.AF_INET),
       {{errno.EPERM, errno.EACCES, errno.EAFNOSUPPORT}})
denied('unix_socket_denied', lambda: socket_attempt(socket.AF_UNIX),
       {{errno.EPERM, errno.EACCES, errno.EAFNOSUPPORT}})
denied('fork_denied', fork_attempt, {{errno.EPERM, errno.EACCES, errno.EAGAIN}})
denied('unrelated_read_denied', denied_read, {{errno.EPERM, errno.EACCES}})
denied('system_write_denied', denied_write, {{errno.EROFS, errno.EPERM, errno.EACCES}})
value = {{
    'authorization': 'invented-fixture-only',
    'checks': checks,
    'corpus_evaluated': False,
    'fixture': True,
    'result': 'isolation-pass' if all(checks.values()) else 'isolation-fail',
}}
raw = json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
if len(raw) > 8192:
    raise SystemExit('result-size')
digest = hashlib.sha256(raw).hexdigest()
parts = [raw[i:i+CHUNK] for i in range(0,len(raw),CHUNK)]
lines = [b' '.join((PREFIX,b'BEGIN',RUN_ID.encode(),MANIFEST.encode(),str(len(raw)).encode(),digest.encode(),str(len(parts)).encode()))]
for sequence,part in enumerate(parts):
    lines.append(b' '.join((PREFIX,b'CHUNK',RUN_ID.encode(),str(sequence).encode(),base64.b64encode(part))))
lines.append(b' '.join((PREFIX,b'END',RUN_ID.encode(),str(len(raw)).encode(),digest.encode())))
out = pathlib.Path('/var/lib/aster-s0/output')
(out/'result.json').write_bytes(raw)
(out/'protocol.txt').write_bytes(b'\\n'.join(lines)+b'\\n')
raise SystemExit(0 if all(checks.values()) else 1)
'''


UNIT = '''[Unit]
Description=Aster S0 invented isolation fixture

[Service]
Type=oneshot
User=aster-s0
Group=aster-s0
WorkingDirectory=/var/lib/aster-s0
Environment=LANG=C LC_ALL=C
UnsetEnvironment=PYTHONPATH PYTHONHOME PYTHONUSERBASE PYTHONSTARTUP PYTHONINSPECT PYTHONWARNINGS PYTHONBREAKPOINT PYTHONPYCACHEPREFIX LD_PRELOAD LD_LIBRARY_PATH LD_AUDIT LD_DEBUG LD_PROFILE GLIBC_TUNABLES SSH_AUTH_SOCK SSH_AGENT_PID GPG_AGENT_INFO DBUS_SESSION_BUS_ADDRESS KRB5CCNAME AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN OPENAI_API_KEY ANTHROPIC_API_KEY VAULT_TOKEN BAO_TOKEN
ExecStart=/usr/bin/python3 -I -S -B /usr/local/lib/aster-s0/isolation_probe.py
StandardOutput=journal
StandardError=journal
NoNewPrivileges=yes
CapabilityBoundingSet=
AmbientCapabilities=
PrivateNetwork=yes
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
SystemCallArchitectures=native
SystemCallFilter=~@network-io clone clone3 fork vfork
SystemCallErrorNumber=EPERM
InaccessiblePaths=/srv/aster-s0-isolation-fixture-002
ReadWritePaths=/var/lib/aster-s0/output
MemoryMax=64M
MemorySwapMax=0
TasksMax=1
CPUQuota=10%
LimitCPU=2
LimitFSIZE=8192
RuntimeMaxSec=15
TimeoutStartSec=15
TimeoutStopSec=2
KillMode=control-group
UMask=0077
'''


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_result(value):
    required_checks = {
        'environment_allowlisted', 'environment_cleared', 'fixed_locale',
        'fork_denied', 'inet_socket_denied', 'loopback_only',
        'system_write_denied', 'unix_socket_denied', 'unprivileged',
        'unrelated_read_denied',
    }
    if type(value) is not dict or set(value) != {
            'authorization', 'checks', 'corpus_evaluated', 'fixture', 'result'}:
        raise ValueError('result shape')
    if (value['authorization'] != 'invented-fixture-only' or
            value['corpus_evaluated'] is not False or value['fixture'] is not True):
        raise ValueError('authority claim')
    if type(value['checks']) is not dict or set(value['checks']) != required_checks:
        raise ValueError('check shape')
    if any(item is not True for item in value['checks'].values()):
        raise ValueError('isolation check failed')
    if value['result'] != 'isolation-pass':
        raise ValueError('result claim')
    return value


def _literal(text, spaces=6):
    pad = ' ' * spaces
    return ''.join((pad + line if line else '') + '\n' for line in text.splitlines())


def render():
    unit = UNIT.encode('utf-8')
    preliminary = PROBE_TEMPLATE.format(run_id=RUN_ID, manifest='0' * 64).encode('utf-8')
    payload = {
        'schema': 'aster-s0-vm-isolation-payload.v2',
        'status': 'invented-fixture-only',
        'run_id': RUN_ID,
        'image': IMAGE,
        'limits': {'capture_bytes': 1024 * 1024, 'result_bytes': 8192,
                   'capture_seconds': 300, 'unit_seconds': 15,
                   'unit_memory_mib': 64, 'tasks': 1},
        'required_checks': sorted({
            'environment_allowlisted', 'environment_cleared', 'fixed_locale',
            'fork_denied', 'inet_socket_denied', 'loopback_only',
            'system_write_denied', 'unix_socket_denied', 'unprivileged',
            'unrelated_read_denied'}),
        'artifact_templates': {'probe_sha256_with_zero_manifest': sha256(preliminary),
                               'unit_sha256': sha256(unit)},
        'accepted_corpus': 'absent',
        'evaluation_authorized': False,
        'network_attachment_authorized': False,
        'credentials_authorized': False,
    }
    payload_raw = canonical(payload)
    payload_digest = sha256(payload_raw)
    probe = PROBE_TEMPLATE.format(run_id=RUN_ID, manifest=payload_digest).encode('utf-8')
    meta = ('instance-id: ' + INSTANCE_ID + '\nlocal-hostname: aster-s0-isolation-v2\n').encode()
    user = ("#cloud-config\npackage_update: false\npackage_upgrade: false\n"
            "ssh_pwauth: false\ndisable_root: true\nusers:\n"
            "  - name: aster-s0\n    system: true\n    lock_passwd: true\n"
            "    no_create_home: true\n    shell: /usr/sbin/nologin\n"
            "write_files:\n"
            "  - path: /usr/local/lib/aster-s0/isolation_probe.py\n    owner: root:root\n"
            "    permissions: '0444'\n    content: |\n" + _literal(probe.decode()) +
            "  - path: /etc/systemd/system/aster-s0-isolation.service\n    owner: root:root\n"
            "    permissions: '0444'\n    content: |\n" + _literal(unit.decode()) +
            "  - path: /usr/local/lib/aster-s0/payload-manifest.json\n    owner: root:root\n"
            "    permissions: '0444'\n    content: |\n" + _literal(payload_raw.decode() + '\n') +
            "runcmd:\n"
            "  - [install, -d, -o, root, -g, root, -m, '0755', /srv/aster-s0-isolation-fixture-002]\n"
            "  - [sh, -c, 'umask 077; printf x > /srv/aster-s0-isolation-fixture-002/canary; chmod 0644 /srv/aster-s0-isolation-fixture-002/canary']\n"
            "  - [install, -d, -o, aster-s0, -g, aster-s0, -m, '0700', /var/lib/aster-s0/output]\n"
            "  - [systemctl, daemon-reload]\n"
            "  - [sh, -c, 'systemctl start aster-s0-isolation.service; rc=$?; if test -s /var/lib/aster-s0/output/protocol.txt; then cat /var/lib/aster-s0/output/protocol.txt > /dev/ttyS0 || rc=$?; fi; sync; systemctl poweroff; exit \"$rc\"']\n"
            "final_message: 'aster-s0 corrected isolation fixture completed'\n").encode('utf-8')
    config = {
        'schema': 'aster-s0-vm-config-proposal.v1',
        'vmid': 'allocate-next-free-at-creation',
        'name': 'aster-s0-isolation-v2-<build-id>',
        'options': {'agent': 'absent', 'balloon': 0, 'bios': 'ovmf',
                    'boot': 'order=scsi0', 'cores': 1, 'cpu': 'x86-64-v2-AES',
                    'hotplug': 0, 'machine': 'q35', 'memory_mib': 1024,
                    'network_devices': [], 'onboot': 0, 'ostype': 'l26',
                    'serial0': 'socket', 'sockets': 1, 'tablet': 0, 'vga': 'serial0'},
        'storage': {'os': 'local-lvm:8GiB,virtio-scsi-single,discard=on,backup=0',
                    'efi': 'local-lvm:4MiB,pre-enrolled-keys=0',
                    'seed': 'local:iso/<reviewed-cidata.iso>,media=cdrom,read-only'},
        'forbidden': ['netN', 'agent', 'hostpci', 'virtiofs', 'usb', 'gpu', 'credentials'],
        'start': False,
    }
    files = {
        'meta-data': meta, 'user-data': user, 'payload-manifest.json': payload_raw + b'\n',
        'isolation_probe.py': probe, 'aster-s0-isolation.service': unit,
        'vm-config-proposal.json': canonical(config) + b'\n',
    }
    for name, raw in files.items():
        if any(token.encode() in raw for token in FORBIDDEN):
            raise ValueError('forbidden corpus marker in ' + name)
    candidate = {
        'schema': 'aster-s0-vm-isolation-candidate.v2',
        'status': 'local-source-only-not-authorized', 'run_id': RUN_ID,
        'instance_id': INSTANCE_ID, 'payload_manifest_sha256': payload_digest,
        'files': {name: {'bytes': len(raw), 'sha256': sha256(raw)}
                  for name, raw in sorted(files.items())},
        'iso_created': False, 'vm_created': False, 'executed': False,
        'accepted_corpus_included': False,
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


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        raise SystemExit('usage: s0_vm_isolation_candidate.py OUTPUT')
    write_candidate(sys.argv[1])
