"""Prepare a private broker-only Compose recovery from exact live settings."""
import hashlib
import json
from pathlib import Path
import subprocess

import yaml


ROOT = Path('/mnt/Media/appdata/dockge/unified-media-shadow/.aster-checkpoints/aster-acquisition-plain-ok1')
OLD = 'sha256:ff853b82fec2abb3cdbd60486fb64f91d035db30bce2e3c76f218829e5a40750'
NEW = 'sha256:e649732f3bc662d5d3f42afd00d010941011ea571d2108ed0c0a7bdf739584c1'


def require(value, code):
    if not value:
        raise RuntimeError(code)


def save(path, raw):
    with path.open('xb') as stream:
        stream.write(raw)
    path.chmod(0o600)


def main():
    info = json.loads(subprocess.check_output(['docker', 'inspect', 'unified-aster-seerr-broker']))[0]
    require(info['Image'] == OLD and info['State']['Running'], 'broker-live-image-drift')
    host = info['HostConfig']
    for key in ('Privileged', 'ReadonlyRootfs', 'CapAdd', 'CapDrop', 'SecurityOpt',
                'Devices', 'DeviceRequests', 'ExtraHosts', 'Dns', 'Tmpfs',
                'Ulimits', 'Memory', 'NanoCpus', 'CpuShares', 'PidsLimit', 'Init'):
        require(not host.get(key), 'broker-nondefault-host-setting:'+key)
    require(host['NetworkMode'] == 'unified-media-shadow_default'
            and list(info['NetworkSettings']['Networks']) == ['unified-media-shadow_default'],
            'broker-network-drift')
    require(host['RestartPolicy']['Name'] == 'unless-stopped', 'broker-restart-drift')
    mounts = info['Mounts']
    require(len(mounts) == 6 and all(m['Type'] == 'bind' and not m['RW'] for m in mounts),
            'broker-mount-drift')
    require(host['PortBindings'] == {'8788/tcp': [{'HostIp': '192.168.20.40', 'HostPort': '8788'}]},
            'broker-port-drift')
    config = info['Config']
    health = config['Healthcheck']
    require(set(health) <= {'Test', 'Interval', 'Timeout', 'StartPeriod', 'Retries'},
            'broker-health-contract')
    service = {
        'image': NEW, 'container_name': 'unified-aster-seerr-broker',
        'environment': config['Env'], 'command': config['Cmd'],
        'user': config['User'], 'working_dir': config['WorkingDir'],
        'restart': 'unless-stopped', 'networks': ['default'],
        'ports': ['192.168.20.40:8788:8788'],
        'volumes': [{'type': 'bind', 'source': m['Source'], 'target': m['Destination'],
                     'read_only': True, 'bind': {'propagation': m['Propagation']}} for m in mounts],
        'healthcheck': {'test': health['Test'], 'retries': health.get('Retries', 0)},
    }
    if config.get('Entrypoint'):
        service['entrypoint'] = config['Entrypoint']
    for key, field in (('Interval', 'interval'), ('Timeout', 'timeout'), ('StartPeriod', 'start_period')):
        if key in health:
            service['healthcheck'][field] = str(health[key])+'ns'
    document = {'services': {'aster-seerr-broker': service},
                'networks': {'default': {'external': True, 'name': 'unified-media-shadow_default'}}}
    save(ROOT/'broker-candidate.yaml', yaml.safe_dump(document, sort_keys=True).encode())
    document['services']['aster-seerr-broker']['image'] = OLD
    save(ROOT/'broker-rollback.yaml', yaml.safe_dump(document, sort_keys=True).encode())
    # Retained privately: Env is necessary to prove exact preservation.
    baseline = {'environment': config['Env'], 'command': config['Cmd'],
                'user': config['User'], 'working_dir': config['WorkingDir'],
                'entrypoint': config.get('Entrypoint'), 'healthcheck': health,
                'mounts': sorted((m['Source'], m['Destination'], m['RW'], m['Propagation']) for m in mounts),
                'ports': host['PortBindings'], 'restart': host['RestartPolicy'],
                'network': host['NetworkMode']}
    save(ROOT/'live-contract.json', json.dumps(baseline, sort_keys=True).encode())
    print(json.dumps({'prepared': True, 'source_image': OLD, 'candidate_image': NEW,
                      'mounts': len(mounts), 'private_files': 3}))


if __name__ == '__main__':
    main()
