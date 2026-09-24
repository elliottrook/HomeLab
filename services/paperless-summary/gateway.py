"""Root-owned host gateway. Fixed Docker command; strict Unix capability API."""
import grp
import json
import os
from pathlib import Path
import pwd
import socket
import socketserver
import struct
import subprocess

from broker_contract import validate

BASE = Path(__file__).resolve().parent
SOCKET = '/run/paperless-summary/broker.sock'


def bridge_program():
    statements = ['import os,sys,types,json',
                  'os.environ.setdefault("DJANGO_SETTINGS_MODULE","paperless.settings")',
                  'import django; django.setup()']
    for name in ('broker_contract', 'django_bridge'):
        source = (BASE / (name + '.py')).read_text()
        statements += [f'm=types.ModuleType({name!r}); sys.modules[{name!r}]=m',
                       f'exec({source!r},m.__dict__)']
    statements += ['from django_bridge import dispatch',
                   'print(json.dumps(dispatch(json.load(sys.stdin))))']
    return '\n'.join(statements)


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(90)
        _, uid, _ = struct.unpack('3i', self.connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        if uid not in (0, self.server.worker_uid):
            return
        action = 'invalid'
        try:
            raw = self.rfile.readline(65537)
            if len(raw) > 65536 or not raw.endswith(b'\n'):
                raise ValueError('request_limit')
            request = json.loads(raw)
            action = validate(request)
            result = subprocess.run(
                ['/usr/bin/docker', 'exec', '-i', 'paperless-ngx-webserver-1',
                 'python3', '-c', self.server.program],
                input=json.dumps(request), text=True, capture_output=True, timeout=60, check=True)
            if len(result.stdout) > 2_000_000:
                raise ValueError('response_limit')
            response = {'ok': True, 'result': json.loads(result.stdout)}
        except Exception:
            # Do not emit document data, tokens, or child stderr in failures.
            response = {'ok': False, 'error': 'capability_failed'}
        print(json.dumps({'action': action, 'caller_uid': uid, 'ok': response['ok']}), flush=True)
        self.wfile.write(json.dumps(response).encode() + b'\n')


def main():
    uid = pwd.getpwnam('paperless-summary').pw_uid
    gid = grp.getgrnam('paperless-summary').gr_gid
    if os.path.lexists(SOCKET):
        raise SystemExit('Socket already exists; do not replace an unknown listener')
    with socketserver.UnixStreamServer(SOCKET, Handler) as server:
        server.worker_uid = uid
        server.program = bridge_program()
        os.chown(SOCKET, 0, gid)
        os.chmod(SOCKET, 0o660)
        try:
            server.serve_forever()
        finally:
            os.unlink(SOCKET)


if __name__ == '__main__':
    main()
