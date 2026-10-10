#!/usr/bin/env python3
"""Run locally as an authorized administrator on TrueNAS; no schedule changes.

Exports only secondary Pi-hole ingress/network reconstruction material into
its existing backup hub. Excludes app databases, DNS history and credentials.
An export is not evidence that snapshots or the off-site relay have run.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from truenas_api_client import Client


def main():
    os.umask(0o077)
    guard = Path('/mnt/Media/appdata/authentik-browser-ingress/pihole-secondary')
    with Client() as client:
        config = client.call('app.config', 'pihole')
    assert not config['pihole']['web_password'], 'Review changed credential posture before export'
    envs = config['pihole']['additional_envs']
    assert envs == [{'name': 'FTLCONF_webserver_acl', 'value': '+127.0.0.1,+172.31.250.1'}]
    network = config['network']
    assert set(network) == {'dns_opts', 'dns_port', 'host_network', 'https_port', 'networks', 'web_port'}
    assert not network['dns_opts'], 'Review unexpected DNS options before export'
    networks = []
    for name in ('authentik-pihole-private', 'authentik-pihole-service'):
        item = json.loads(subprocess.check_output(['docker', 'network', 'inspect', name]))[0]
        networks.append({key: item[key] for key in ('Name', 'Driver', 'Internal', 'EnableIPv6', 'IPAM', 'Options')})
    # Ensure guard sources contain no credential directives before copying.
    for name in ('nginx.conf', 'compose.json'):
        source = (guard / name).read_text()
        assert not any(word in source.lower() for word in ('password', 'secret', 'api_key', 'bearer '))
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    target = Path('/mnt/Recovery/configuration/service-reconstruction/pihole-secondary') / stamp
    target.mkdir(parents=True, mode=0o700)
    for directory in (target, target.parent, target.parent.parent):
        directory.chmod(0o700)
    for name in ('nginx.conf', 'compose.json'):
        shutil.copyfile(guard / name, target / name)
    (target / 'managed-app-network-patch.json').write_text(json.dumps({
        'network': network, 'pihole': {'additional_envs': envs}}, indent=2))
    (target / 'docker-networks.json').write_text(json.dumps(networks, indent=2))
    (target / 'README.txt').write_text(
        'Secondary Pi-hole guard reconstruction only. No application data or credentials. '
        'Restore both Docker networks before applying the managed-app patch; do not expose '
        'the backend web port. Follow HomeLab docs/runbooks/Pi-hole-Single-Login.md. '
        'Refresh after configuration changes. Verify subsequent snapshot and relay completion '
        'separately before claiming replicated protection.\n')
    hashes = {}
    for path in target.iterdir():
        path.chmod(0o600)
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = target / 'SHA256SUMS.json'
    manifest.write_text(json.dumps(hashes, indent=2))
    manifest.chmod(0o600)
    for name, expected in hashes.items():
        assert hashlib.sha256((target / name).read_bytes()).hexdigest() == expected
    print(json.dumps({'bundle': str(target), 'files_verified': len(hashes),
                      'replication_status': 'awaiting existing schedules'}))


if __name__ == '__main__':
    main()
