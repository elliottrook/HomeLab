#!/usr/bin/env python3
"""Operator-run, bounded Frigate ingress deployment for VM 102.

Keeps native recovery on 8971 and streams unchanged. Moves internal 5000 to
loopback; exposes only metrics to Prometheus and browser access to NPM with a
verified owner header. Does not edit Frigate config or authentication secrets.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request

BASE = Path('/opt/frigate')
IMAGE = 'nginx@sha256:608a100c71651bf5b773c89083b4a1ad7ef4b2bd05d7a7e552271e03123692ad'
NAME = 'authentik-frigate-ingress'
CONFIG = '''pid /tmp/nginx.pid;
events { worker_connections 1024; }
http {
  access_log off;
  error_log /dev/stderr warn;
  client_body_temp_path /tmp/client;
  proxy_temp_path /tmp/proxy;
  fastcgi_temp_path /tmp/fastcgi;
  uwsgi_temp_path /tmp/uwsgi;
  scgi_temp_path /tmp/scgi;
  map $http_upgrade $connection_upgrade { default upgrade; '' close; }
  map "$remote_addr|$http_x_homelab_authentik_user" $owner_ok {
    default 0;
    "192.168.50.23|jason" 1;
  }
  server {
    listen 192.168.20.10:5000;
    location = /api/metrics {
      allow 192.168.20.31;
      deny all;
      limit_except GET { deny all; }
      proxy_pass http://127.0.0.1:5000;
    }
    location / { return 403; }
  }
  server {
    listen 192.168.20.10:8972;
    if ($owner_ok = 0) { return 403; }
    client_max_body_size 100M;
    location / {
      proxy_pass http://127.0.0.1:5000;
      proxy_http_version 1.1;
      proxy_set_header Host $host;
      proxy_set_header X-Forwarded-Proto https;
      proxy_set_header X-Forwarded-For $remote_addr;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection $connection_upgrade;
      proxy_read_timeout 3600s;
      proxy_buffering off;
    }
  }
}
'''


def run(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, **kwargs)


def health():
    for _ in range(60):
        r = run(['docker', 'inspect', '--format', '{{.State.Health.Status}}', 'frigate'])
        if r.stdout.strip() == b'healthy':
            return
        time.sleep(2)
    raise RuntimeError('Frigate did not become healthy within 120 seconds')


def status(url, headers=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def main():
    assert os.geteuid() == 0, 'Run in the administrator terminal'
    os.umask(0o077)
    compose = BASE / 'compose.yaml'
    before = compose.read_bytes()
    old = b'"5000:5000"'
    assert before.count(old) == 1, 'Unexpected ports: stop for review'
    assert b'127.0.0.1:5000:5000' not in before
    cfg = BASE / 'config/config.yaml'
    config_hash = hashlib.sha256(cfg.read_bytes()).hexdigest()
    run(['findmnt', '-rn', '-t', 'nfs4', '-T', str(BASE / 'storage')])
    existing = run(['docker', 'ps', '-a', '--filter', 'name=^/' + NAME + '$', '--format', '{{.Names}}'])
    assert not existing.stdout.strip(), 'Ingress already exists: inspect before retrying'
    state = json.loads(run(['docker', 'inspect', 'frigate']).stdout)[0]
    assert state['State']['Health']['Status'] == 'healthy'
    original_image = state['Image']
    checkpoint = Path('/root/authentik-frigate-deploy-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    checkpoint.mkdir(mode=0o700)
    shutil.copyfile(compose, checkpoint / 'compose.yaml')
    shutil.copyfile(cfg, checkpoint / 'config.yaml')
    (checkpoint / 'container-inspect.json').write_text(json.dumps(state))
    with sqlite3.connect('file:/opt/frigate/config/frigate.db?mode=ro', uri=True) as db:
        with sqlite3.connect(checkpoint / 'frigate.db') as backup:
            db.backup(backup)
            assert backup.execute('pragma integrity_check').fetchone()[0] == 'ok'
    ingress = BASE / 'authentik-ingress'
    assert not ingress.exists(), 'Candidate directory already exists: inspect before retrying'
    ingress.mkdir(mode=0o755)
    os.chmod(ingress, 0o755)
    nginx = ingress / 'nginx.conf'
    nginx.write_text(CONFIG)
    os.chmod(nginx, 0o644)
    # Pull only the pinned guard image; never upgrade Frigate's mutable tag.
    run(['docker', 'pull', IMAGE])
    common = ['--network', 'host', '--user', '101:101', '--read-only',
              '--tmpfs', '/tmp:rw,noexec,nosuid,size=64m', '--cap-drop', 'ALL',
              '--security-opt', 'no-new-privileges:true',
              '--mount', 'type=bind,src=' + str(nginx) + ',dst=/etc/nginx/nginx.conf,readonly']
    run(['docker', 'run', '--rm'] + common + [IMAGE, 'nginx', '-t'])
    try:
        compose.write_bytes(before.replace(old, b'"127.0.0.1:5000:5000"'))
        run(['docker', 'compose', 'config', '--quiet'], cwd=BASE)
        run(['docker', 'compose', 'up', '-d', '--pull', 'never', '--no-deps', 'frigate'], cwd=BASE)
        health()
        after = json.loads(run(['docker', 'inspect', 'frigate']).stdout)[0]
        assert after['Image'] == original_image, 'Unexpected image change'
        bindings = after['HostConfig']['PortBindings']
        assert bindings['5000/tcp'] == [{'HostIp': '127.0.0.1', 'HostPort': '5000'}]
        for port in ('8971/tcp', '8554/tcp', '8555/tcp', '8555/udp'):
            assert bindings[port] == state['HostConfig']['PortBindings'][port]
        run(['docker', 'run', '-d', '--name', NAME, '--restart', 'unless-stopped'] + common + [IMAGE])
        time.sleep(2)
        assert status('http://127.0.0.1:5000/api/version') == 200
        assert status('http://192.168.20.10:5000/api/profile') == 403
        assert status('http://192.168.20.10:8972/api/profile', {'X-Homelab-Authentik-User': 'jason'}) == 403
        assert hashlib.sha256(cfg.read_bytes()).hexdigest() == config_hash
    except Exception:
        subprocess.run(['docker', 'rm', '-f', NAME], capture_output=True)
        compose.write_bytes(before)
        run(['docker', 'compose', 'up', '-d', '--pull', 'never', '--no-deps', 'frigate'], cwd=BASE)
        health()
        print('Deployment failed; original Compose restored. Checkpoint:', checkpoint)
        raise
    print('Ingress deployed; Frigate healthy. Checkpoint:', checkpoint)
    print('Configuration and image unchanged; streams preserved; direct/spoofed browser access denied.')
    print('Next: verify Prometheus metrics, NPM owner gate, live view and new recordings.')


if __name__ == '__main__':
    main()
