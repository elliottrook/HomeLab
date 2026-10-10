#!/usr/bin/env python3
"""Synthetic Pi-hole ingress proof; NEVER deploys or copies production config.

Run on a Docker host with its installed Pi-hole and the pinned nginx image.
Uses two named disposable containers, network none, no published ports and a
synthetic database. Removes only its own containers and temporary config.
The loopback trust addresses are test fixtures, not production configuration.
"""
import json
from pathlib import Path
import subprocess
import tempfile
import time

BACKEND = 'authentik-pihole-proof-backend'
GUARD = 'authentik-pihole-proof-guard'
HOMEPAGE = 'authentik-pihole-proof-homepage'
NGINX = 'nginx@sha256:608a100c71651bf5b773c89083b4a1ad7ef4b2bd05d7a7e552271e03123692ad'
CONFIG = '''pid /tmp/nginx.pid;
events { worker_connections 128; }
http {
  access_log off;
  error_log /dev/stderr warn;
  client_body_temp_path /tmp/client;
  proxy_temp_path /tmp/proxy;
  fastcgi_temp_path /tmp/fastcgi;
  uwsgi_temp_path /tmp/uwsgi;
  scgi_temp_path /tmp/scgi;
  map "$remote_addr|$http_x_homelab_authentik_user" $owner_ok {
    default 0;
    "127.0.0.1|jason" 1;
  }
  map $http_origin $origin_ok {
    default 0;
    "" 1;
    "https://dns1.elliottrook.com" 1;
  }
  map "$request_method|$http_origin" $write_ok {
    default 0;
    ~^(GET|HEAD)\\| 1;
    ~^(POST|PUT|PATCH|DELETE)\\|https://dns1\\.elliottrook\\.com$ 1;
  }
  server {
    listen 127.0.0.1:8081;
    if ($owner_ok = 0) { return 403; }
    if ($origin_ok = 0) { return 403; }
    if ($write_ok = 0) { return 403; }
    if ($http_sec_fetch_site = cross-site) { return 403; }
    location / {
      proxy_pass http://127.0.0.1:8080;
      proxy_set_header Host dns1.elliottrook.com;
      proxy_set_header X-Forwarded-Proto https;
      proxy_set_header X-Forwarded-For $remote_addr;
      proxy_set_header Authorization "";
      proxy_set_header X-FTL-SID "";
      proxy_set_header X-Homelab-Authentik-User "";
    }
  }
  server {
    listen 127.0.0.1:8082;
    allow 127.0.0.1;
    deny all;
    location = /api/stats/summary {
      limit_except GET { deny all; }
      proxy_pass http://127.0.0.1:8080;
      proxy_set_header Authorization "";
      proxy_set_header X-FTL-SID "";
      proxy_set_header Cookie "";
    }
    location / { return 403; }
  }
}
'''

def run(*args, check=True):
    return subprocess.run(args, check=check, capture_output=True, text=True)

def inspect(name):
    return json.loads(run('docker', 'inspect', name).stdout)[0]

def request(port, path, headers=(), method='GET', source=None, body=None):
    args = ['docker', 'exec', BACKEND, 'curl', '--max-time', '3', '-sS',
            '-o', '/dev/null', '-w', '%{http_code}', '-X', method]
    if source:
        args += ['--interface', source]
    for header in headers:
        args += ['-H', header]
    if body is not None:
        args += ['-H', 'Content-Type: application/json', '--data', body]
    return run(*args, f'http://127.0.0.1:{port}{path}', check=False).stdout

def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installed-container', default='pihole')
    parser.add_argument('--homepage-container', help='Optionally prove the installed widget without a key')
    args = parser.parse_args()
    before = inspect(args.installed_container)
    homepage_before = inspect(args.homepage_container) if args.homepage_container else None
    for name in (BACKEND, GUARD, HOMEPAGE):
        if run('docker', 'inspect', name, check=False).returncode == 0:
            raise RuntimeError(f'Refusing existing fixture name: {name}')
    run('docker', 'image', 'inspect', NGINX)
    created = []
    results = []
    def expect(label, expected, *a, **kw):
        actual = request(*a, **kw)
        result = {'check': label, 'expected': expected, 'actual': actual,
                  'passed': actual == expected}
        results.append(result)
        print(json.dumps(result), flush=True)
        assert actual == expected, label
    try:
        with tempfile.TemporaryDirectory(prefix='pihole-synthetic-proof-') as directory:
            config = Path(directory) / 'nginx.conf'
            config.write_text(CONFIG)
            config.chmod(0o644)
            startup = '''mkdir -p /var/log/pihole
cat > /etc/pihole/pihole.toml <<'TOML'
[dns]
port = 0
[webserver]
port = "127.0.0.1:8080"
[webserver.api]
pwhash = ""
TOML
pihole-FTL sqlite3 /etc/pihole/gravity.db < /etc/.pihole/advanced/Templates/gravity.db.sql
exec pihole-FTL no-daemon
'''
            run('docker', 'run', '-d', '--pull', 'never', '--name', BACKEND,
                '--network', 'none', '--no-healthcheck', '--entrypoint', 'sh',
                before['Image'], '-ec', startup)
            created.append(BACKEND)
            for _ in range(30):
                if request(8080, '/api/stats/summary') == '200':
                    break
                time.sleep(1)
            fixture = inspect(BACKEND)
            assert fixture['HostConfig']['NetworkMode'] == 'none'
            assert not fixture['HostConfig']['PortBindings'] and not fixture['Mounts']
            expect('synthetic_passwordless_ui', '200', 8080, '/admin/')
            expect('synthetic_passwordless_api', '200', 8080, '/api/config')
            body = '{"blocking":false,"timer":5}'
            expect('unguarded_cross_origin_write_demonstration', '200', 8080,
                   '/api/dns/blocking', method='POST', body=body,
                   headers=['Origin: https://untrusted.example'])
            run('docker', 'run', '-d', '--pull', 'never', '--name', GUARD,
                '--network', 'container:' + BACKEND, '--user', '101:101',
                '--read-only', '--tmpfs', '/tmp:rw,noexec,nosuid,size=16m',
                '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true',
                '-v', str(config) + ':/etc/nginx/nginx.conf:ro',
                '--entrypoint', 'nginx', NGINX, '-g', 'daemon off;')
            created.append(GUARD)
            for _ in range(20):
                if request(8081, '/admin/') == '403':
                    break
                time.sleep(0.5)
            owner = ['X-Homelab-Authentik-User: jason']
            expect('anonymous_denied', '403', 8081, '/admin/')
            expect('wrong_owner_denied', '403', 8081, '/admin/',
                   headers=['X-Homelab-Authentik-User: other'])
            expect('spoofed_identity_from_wrong_peer_denied', '403', 8081,
                   '/api/config', headers=owner + ['X-Forwarded-For: 127.0.0.1'],
                   source='127.0.0.2')
            expect('owner_ui_allowed', '200', 8081, '/admin/', headers=owner)
            expect('owner_api_allowed', '200', 8081, '/api/config', headers=owner)
            expect('foreign_origin_write_denied', '403', 8081, '/api/dns/blocking',
                   method='POST', body=body,
                   headers=owner + ['Origin: https://untrusted.example'])
            expect('missing_origin_write_denied', '403', 8081, '/api/dns/blocking',
                   method='POST', body=body, headers=owner)
            expect('same_origin_write_allowed', '200', 8081, '/api/dns/blocking',
                   method='POST', body=body,
                   headers=owner + ['Origin: https://dns1.elliottrook.com'])
            expect('cross_site_fetch_denied', '403', 8081, '/api/config',
                   headers=owner + ['Sec-Fetch-Site: cross-site'])
            expect('widget_summary_allowed', '200', 8082, '/api/stats/summary')
            expect('widget_config_denied', '403', 8082, '/api/config')
            expect('widget_write_denied', '403', 8082, '/api/stats/summary',
                   method='POST', body='{}')
            expect('widget_wrong_peer_denied', '403', 8082, '/api/stats/summary',
                   source='127.0.0.2')
            if homepage_before:
                hp = Path(directory) / 'homepage'
                hp.mkdir()
                (hp / 'services.yaml').write_text('- Proof:\n    - Pi-hole:\n        widget:\n          type: pihole\n          url: http://127.0.0.1:8082\n          version: 6\n')
                for name, content in [('settings.yaml', '{}'), ('widgets.yaml', '[]'),
                                      ('bookmarks.yaml', '[]'), ('docker.yaml', '{}')]:
                    (hp / name).write_text(content)
                run('docker', 'run', '-d', '--pull', 'never', '--name', HOMEPAGE,
                    '--network', 'container:' + BACKEND, '--no-healthcheck',
                    '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true',
                    '--memory', '512m', '--cpus', '1',
                    '-e', 'HOMEPAGE_ALLOWED_HOSTS=127.0.0.1:3000',
                    '-e', 'HOSTNAME=127.0.0.1', '-v', str(hp) + ':/app/config',
                    '--entrypoint', 'node', homepage_before['Image'], 'server.js')
                created.append(HOMEPAGE)
                path = '/api/services/proxy?group=Proof&service=Pi-hole&index=0'
                for _ in range(30):
                    if request(3000, path) == '200':
                        break
                    time.sleep(1)
                expect('installed_homepage_widget_without_key', '200', 3000, path)
                response = run('docker', 'exec', BACKEND, 'curl', '--max-time', '3',
                               '-sS', 'http://127.0.0.1:3000' + path).stdout
                fields = json.loads(response)
                assert all(k in fields for k in ('domains_being_blocked',
                           'ads_blocked_today', 'ads_percentage_today', 'dns_queries_today'))
                print(json.dumps({'widget_statistics_fields_verified': True}))
    finally:
        for name in reversed(created):
            run('docker', 'rm', '-f', name)
        if homepage_before:
            hp_after = inspect(args.homepage_container)
            assert homepage_before['Id'] == hp_after['Id']
            assert homepage_before['State']['StartedAt'] == hp_after['State']['StartedAt']
            print(json.dumps({'production_homepage_unchanged': True}))
        after = inspect(args.installed_container)
        assert before['Id'] == after['Id']
        assert before['State']['StartedAt'] == after['State']['StartedAt']
        print(json.dumps({'production_container_unchanged': True,
                          'production_running': after['State']['Running'],
                          'synthetic_containers_removed': created}))
    print(json.dumps({'passed': len(results), 'total': len(results),
                      'scope': 'synthetic fixture only; not deployment approval',
                      'pihole_image': before['Image']}))

if __name__ == '__main__':
    main()
