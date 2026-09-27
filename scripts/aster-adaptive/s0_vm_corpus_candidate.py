"""Render a local-only, immutable S0 accepted-corpus VM candidate."""

import base64
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
RUN_ID = 'corpus-descriptive-001'
INSTANCE_ID = 'aster-s0-corpus-001'
CORPUS_FILES = tuple(
    f'batch-{batch}/{name}.json'
    for batch in range(1, 4)
    for name in ('reviewed-proposal', 'acceptance', 'effort')
)
CORPUS_MANIFEST = {
    'batch-1/reviewed-proposal.json': '64459d47a6a48bb7e67f6aad766a623ba4fae2f6c0bad0c309f55c880c7e7288',
    'batch-1/acceptance.json': '5e5c498bea895e50a1279b2e89c128b92ac7e7fa3b0e42ed250ec8be45a71437',
    'batch-1/effort.json': '2c8e795f2f3b2d76639269d0df7f876c949a832844044b8d2669480f04cf4d8d',
    'batch-2/reviewed-proposal.json': '0731464ba0d7ea3db596f48d920a7f8492004c34c45600f0efcc15c9aaec5308',
    'batch-2/acceptance.json': '9524eb1e737f553c71db782efafa2a8fde4c6a233bc39ac7e7a765ae75295520',
    'batch-2/effort.json': '1401158fb3e63fed350aafff2056090f544f9543e3ae9d51439e408d53da6ef4',
    'batch-3/reviewed-proposal.json': '962bf5f1c2adaefe4dbbedc92116640019b77c7e4580bc2c2d6b3462750f7a95',
    'batch-3/acceptance.json': 'd165a0bb2927674fe742628d36e8b843acc4b381b328da16af84035cab48a268',
    'batch-3/effort.json': 'b2f62ea4843a5927f71f65d8594ef968798f80f8071e91a8b6e2c540e18e3f5c',
}


ENTRY_TEMPLATE = '''"""Generated exact S0 corpus entry point; no external inputs."""
import base64,hashlib,json,os,pathlib,platform,sys
RUN_ID={run_id!r}
PAYLOAD_SHA256={payload_sha256!r}
FILES={files}
CORPUS_MANIFEST={corpus_manifest}
PREFIX=b'ASTER_S0_V1'
CHUNK=3072
LIB=pathlib.Path('/usr/local/lib/aster-s0')
CORPUS=pathlib.Path('/usr/local/share/aster-s0/corpus')
for name,expected in FILES.items():
    path=(CORPUS/name) if name.startswith('batch-') else (LIB/name)
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:raise SystemExit('artifact-hash')
sys.path.insert(0,str(LIB))
import s0_descriptive as descriptive
import s0_vm_corpus_worker as worker
blobs={{name:(CORPUS/name).read_bytes() for name in CORPUS_MANIFEST}}
rows=descriptive.adapt(blobs,CORPUS_MANIFEST)
engine=worker.load_engine_source(LIB/'routing_smoke.py')
value=worker.compare_accepted(rows,engine)
value.update({{
    'run_id':RUN_ID,
    'payload_manifest_sha256':PAYLOAD_SHA256,
    'dataset_manifest_sha256':hashlib.sha256(descriptive.canonical(CORPUS_MANIFEST)).hexdigest(),
    'development_family_ids':sorted(row['family_id'] for row in rows if row['labels']['split']=='dev'),
    'runtime':{{'python':platform.python_version(),'system':platform.system(),'machine':platform.machine()}},
}})
raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
if not raw or len(raw)>2097152:raise SystemExit('result-size')
digest=hashlib.sha256(raw).hexdigest()
parts=[raw[i:i+CHUNK] for i in range(0,len(raw),CHUNK)]
lines=[b' '.join((PREFIX,b'BEGIN',RUN_ID.encode(),PAYLOAD_SHA256.encode(),str(len(raw)).encode(),digest.encode(),str(len(parts)).encode()))]
for sequence,part in enumerate(parts):
    lines.append(b' '.join((PREFIX,b'CHUNK',RUN_ID.encode(),str(sequence).encode(),base64.b64encode(part))))
lines.append(b' '.join((PREFIX,b'END',RUN_ID.encode(),str(len(raw)).encode(),digest.encode())))
out=pathlib.Path('/var/lib/aster-s0/output')
(out/'result.json').write_bytes(raw)
(out/'protocol.txt').write_bytes(b'\\n'.join(lines)+b'\\n')
'''


UNIT = '''[Unit]
Description=Aster S0 accepted-corpus descriptive comparison

[Service]
Type=oneshot
User=aster-s0
Group=aster-s0
WorkingDirectory=/var/lib/aster-s0
Environment=LANG=C LC_ALL=C
UnsetEnvironment=PYTHONPATH PYTHONHOME PYTHONUSERBASE PYTHONSTARTUP PYTHONINSPECT PYTHONWARNINGS PYTHONBREAKPOINT PYTHONPYCACHEPREFIX LD_PRELOAD LD_LIBRARY_PATH LD_AUDIT LD_DEBUG LD_PROFILE GLIBC_TUNABLES SSH_AUTH_SOCK SSH_AGENT_PID GPG_AGENT_INFO DBUS_SESSION_BUS_ADDRESS KRB5CCNAME AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN OPENAI_API_KEY ANTHROPIC_API_KEY VAULT_TOKEN BAO_TOKEN
ExecStart=/usr/bin/python3 -I -S -B /usr/local/lib/aster-s0/corpus_entry.py
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
ReadOnlyPaths=/usr/local/lib/aster-s0 /usr/local/share/aster-s0/corpus
ReadWritePaths=/var/lib/aster-s0/output
MemoryMax=384M
MemorySwapMax=0
TasksMax=1
CPUQuota=50%
LimitCPU=70
LimitFSIZE=4194304
LimitNOFILE=64
RuntimeMaxSec=75
TimeoutStartSec=75
TimeoutStopSec=3
KillMode=control-group
UMask=0077
'''


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def _repo_root():
    return Path(__file__).resolve().parents[2]


def _yaml_file(path, raw):
    encoded = base64.b64encode(raw).decode('ascii')
    return (f"  - path: {path}\n    owner: root:root\n    permissions: '0444'\n"
            f"    encoding: b64\n    content: {encoded}\n")


def validate_result(value, payload):
    expected = {
        'format', 'scope', 'corpus_evaluated', 'families', 'training_families',
        'development_families', 'profiles', 'stop_reason', 'elapsed_ns',
        'peak_rss_mib', 'execution_approval_claimed_by_guest',
        'promotion_authorized', 'privacy_routing_quality',
        'cloud_requirement_fraction', 'production_local_resolution_fraction',
        'confidence', 'run_id', 'payload_manifest_sha256',
        'dataset_manifest_sha256', 'development_family_ids', 'runtime',
    }
    if type(value) is not dict or set(value) != expected:
        raise ValueError('result shape')
    if (value['format'] != 's0-descriptive-result.v1' or
            value['scope'] != 'accepted-exposed-30-family-descriptive-only' or
            value['corpus_evaluated'] is not True or value['families'] != 30 or
            value['training_families'] != 20 or value['development_families'] != 10 or
            value['stop_reason'] is not None or
            value['execution_approval_claimed_by_guest'] is not False or
            value['promotion_authorized'] is not False or
            any(value[name] is not None for name in (
                'privacy_routing_quality', 'cloud_requirement_fraction',
                'production_local_resolution_fraction', 'confidence'))):
        raise ValueError('result claim')
    if (value['run_id'] != RUN_ID or
            value['payload_manifest_sha256'] != sha256(canonical(payload)) or
            value['dataset_manifest_sha256'] != payload['dataset_manifest_sha256'] or
            value['development_family_ids'] != payload['development_family_ids']):
        raise ValueError('identity')
    if (type(value['elapsed_ns']) is not int or value['elapsed_ns'] < 0 or
            type(value['peak_rss_mib']) not in (int, float) or value['peak_rss_mib'] < 0):
        raise ValueError('resource metrics')
    if type(value['runtime']) is not dict or set(value['runtime']) != {'python', 'system', 'machine'}:
        raise ValueError('runtime shape')
    if any(type(item) is not str or not item for item in value['runtime'].values()):
        raise ValueError('runtime value')
    if set(value['profiles']) != set(payload['profiles']):
        raise ValueError('profiles')
    expected_ids = payload['development_family_ids']
    expected_engines = set(payload['engines'])
    for profile in value['profiles'].values():
        if type(profile) is not dict or set(profile) != {'construction_ns', 'engines', 'disagreements'}:
            raise ValueError('profile shape')
        if type(profile['construction_ns']) is not int or profile['construction_ns'] < 0:
            raise ValueError('construction metric')
        if set(profile['engines']) != expected_engines:
            raise ValueError('engines')
        for engine in profile['engines'].values():
            if type(engine) is not dict or set(engine) != {
                    'rows', 'metrics', 'first_pass_latency', 'warm_latency', 'warm_errors'}:
                raise ValueError('engine shape')
            if engine['warm_errors'] != 0 or engine['warm_latency'].get('count') != 300:
                raise ValueError('warm execution')
            if [row.get('family_id') for row in engine['rows']] != expected_ids:
                raise ValueError('development rows')
            if any(row.get('error') is not None or
                   type(row.get('score')) is not dict or
                   row['score'].get('valid') is not True for row in engine['rows']):
                raise ValueError('row execution')
            if engine['metrics'].get('families') != 10:
                raise ValueError('metrics denominator')
    return value


def render(repo_root=None):
    root = Path(repo_root) if repo_root else _repo_root()
    source_paths = {
        's0_descriptive.py': root / 'scripts/aster-adaptive/s0_descriptive.py',
        's0_vm_corpus_worker.py': root / 'scripts/aster-adaptive/s0_vm_corpus_worker.py',
        'routing_smoke.py': root / 'scripts/aster-adaptive/routing_smoke.py',
    }
    corpus_root = root / 'docs/projects/AI Projects/labeling/pilot-s0'
    sources = {name: path.read_bytes() for name, path in source_paths.items()}
    corpus = {name: (corpus_root / name).read_bytes() for name in CORPUS_FILES}
    if {name: sha256(raw) for name, raw in corpus.items()} != CORPUS_MANIFEST:
        raise ValueError('accepted corpus hash mismatch')
    file_hashes = {name: sha256(raw) for name, raw in sources.items()}
    file_hashes.update({name: sha256(raw) for name, raw in corpus.items()})
    preliminary = ENTRY_TEMPLATE.format(
        run_id=RUN_ID, payload_sha256='0' * 64,
        files=repr(file_hashes), corpus_manifest=repr(CORPUS_MANIFEST)).encode()
    dev_ids = []
    for batch in range(1, 4):
        proposal = json.loads(corpus[f'batch-{batch}/reviewed-proposal.json'])
        dev_ids.extend(row['family_id'] for row in proposal['records']
                       if row['labels']['split'] == 'dev')
    payload = {
        'schema': 'aster-s0-vm-corpus-payload.v1',
        'status': 'accepted-corpus-candidate-not-authorized',
        'run_id': RUN_ID,
        'image': IMAGE,
        'dataset_manifest': CORPUS_MANIFEST,
        'dataset_manifest_sha256': sha256(canonical(CORPUS_MANIFEST)),
        'development_family_ids': sorted(dev_ids),
        'engines': ['always-abstain', 'existing-keyword-rules',
                    'tfidf-nearest-fixed-0.2'],
        'profiles': ['request-only', 'request-plus-verbatim-synthetic-context'],
        'limits': {'capture_bytes': 4 * 1024 * 1024, 'result_bytes': 2 * 1024 * 1024,
                   'capture_seconds': 300, 'unit_seconds': 75,
                   'unit_memory_mib': 384, 'tasks': 1},
        'artifact_templates': {
            'entry_sha256_with_zero_manifest': sha256(preliminary),
            'unit_sha256': sha256(UNIT.encode()),
            'source_files': {name: sha256(raw) for name, raw in sorted(sources.items())},
        },
        'accepted_corpus_included': True,
        'evaluation_authorized': False,
        'network_attachment_authorized': False,
        'credentials_authorized': False,
        'promotion_authorized': False,
    }
    payload_raw = canonical(payload)
    payload_digest = sha256(payload_raw)
    entry = ENTRY_TEMPLATE.format(
        run_id=RUN_ID, payload_sha256=payload_digest,
        files=repr(file_hashes), corpus_manifest=repr(CORPUS_MANIFEST)).encode()
    meta = ('instance-id: ' + INSTANCE_ID + '\nlocal-hostname: aster-s0-corpus-v1\n').encode()
    unit = UNIT.encode()
    user = bytearray(b"#cloud-config\npackage_update: false\npackage_upgrade: false\n"
                     b"ssh_pwauth: false\ndisable_root: true\nusers:\n"
                     b"  - name: aster-s0\n    system: true\n    lock_passwd: true\n"
                     b"    no_create_home: true\n    shell: /usr/sbin/nologin\nwrite_files:\n")
    for name, raw in sorted(sources.items()):
        user.extend(_yaml_file('/usr/local/lib/aster-s0/' + name, raw).encode())
    user.extend(_yaml_file('/usr/local/lib/aster-s0/corpus_entry.py', entry).encode())
    user.extend(_yaml_file('/usr/local/lib/aster-s0/payload-manifest.json', payload_raw + b'\n').encode())
    user.extend(_yaml_file('/etc/systemd/system/aster-s0-corpus.service', unit).encode())
    for name, raw in sorted(corpus.items()):
        user.extend(_yaml_file('/usr/local/share/aster-s0/corpus/' + name, raw).encode())
    user.extend(b"runcmd:\n"
                b"  - [install, -d, -o, aster-s0, -g, aster-s0, -m, '0700', /var/lib/aster-s0/output]\n"
                b"  - [systemctl, daemon-reload]\n"
                b"  - [sh, -c, 'systemctl start aster-s0-corpus.service; rc=$?; if test -s /var/lib/aster-s0/output/protocol.txt; then cat /var/lib/aster-s0/output/protocol.txt > /dev/ttyS0 || rc=$?; fi; sync; systemctl poweroff; exit \"$rc\"']\n"
                b"final_message: 'aster-s0 corpus candidate completed'\n")
    config = {
        'schema': 'aster-s0-vm-config-proposal.v1',
        'vmid': 122, 'name': 'aster-s0-corpus-v1',
        'options': {'agent': 'absent', 'balloon': 0, 'bios': 'ovmf',
                    'boot': 'order=scsi0', 'cores': 1, 'cpu': 'x86-64-v2-AES',
                    'hotplug': 0, 'machine': 'q35', 'memory_mib': 1024,
                    'network_devices': [], 'onboot': 0, 'ostype': 'l26',
                    'serial0': 'socket', 'sockets': 1, 'tablet': 0, 'vga': 'serial0'},
        'storage': {'os': 'local-lvm:8GiB,virtio-scsi-single,discard=on,backup=0',
                    'efi': 'local-lvm:4MiB,pre-enrolled-keys=0',
                    'seed': 'local:iso/aster-s0-corpus-descriptive-001.iso,media=cdrom,read-only'},
        'forbidden': ['netN', 'agent', 'hostpci', 'virtiofs', 'usb', 'gpu', 'credentials'],
        'start': False,
    }
    files = {
        'meta-data': meta, 'user-data': bytes(user),
        'payload-manifest.json': payload_raw + b'\n', 'corpus_entry.py': entry,
        'aster-s0-corpus.service': unit,
        'vm-config-proposal.json': canonical(config) + b'\n',
    }
    for name, raw in sorted(sources.items()):
        files['source/' + name] = raw
    for name, raw in sorted(corpus.items()):
        files['corpus/' + name] = raw
    candidate = {
        'schema': 'aster-s0-vm-corpus-candidate.v1',
        'status': 'local-source-only-not-authorized',
        'run_id': RUN_ID, 'instance_id': INSTANCE_ID,
        'payload_manifest_sha256': payload_digest,
        'files': {name: {'bytes': len(raw), 'sha256': sha256(raw)}
                  for name, raw in sorted(files.items())},
        'iso_created': False, 'vm_created': False, 'executed': False,
        'accepted_corpus_included': True, 'accepted_corpus_evaluated': False,
    }
    files['candidate-manifest.json'] = canonical(candidate) + b'\n'
    return files


def write_candidate(output, repo_root=None):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True, mode=0o700)
    files = render(repo_root)
    for name, raw in files.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        path.chmod(0o600)
    return files


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        raise SystemExit('usage: s0_vm_corpus_candidate.py OUTPUT')
    write_candidate(sys.argv[1])
