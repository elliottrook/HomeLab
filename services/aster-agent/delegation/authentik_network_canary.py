"""Operator-only finite Mac HTTPS identity test. Default prints source fingerprint.

Reuses source-local temporary identity lifecycle. Secret request/response frames
travel only through an owned SSH pipe and TLS to the fixed Authentik host; never
stdout of this controller, files or environment. No model or gateway deployment.
--run requires approval of the fingerprint; no automatic retry.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import selectors
import shlex
import subprocess
import time
import httpx

PATHS = {'/application/o/token/', '/application/o/introspect/', '/application/o/revoke/'}
PREFIX = 'ASTER_HTTP='


def forward(frame, client):
    if not isinstance(frame, dict) or set(frame) != {'path', 'data', 'authorization'}:
        raise ValueError('Invalid transport frame')
    if frame['path'] not in PATHS or not isinstance(frame['data'], dict):
        raise ValueError('Forbidden identity endpoint')
    headers = {}
    auth = frame['authorization']
    if auth is not None:
        if not isinstance(auth, str) or not auth.startswith('Basic ') or len(auth) > 16384:
            raise ValueError('Invalid introspection credential frame')
        headers['Authorization'] = auth
    with client.stream('POST', 'https://auth.elliottrook.com'+frame['path'],
                       data=frame['data'], headers=headers) as response:
        body = b''
        for chunk in response.iter_bytes():
            body += chunk
            if len(body) > 32768:
                raise ValueError('Identity response limit')
        # Never forward HTML/error diagnostics back through the protocol.
        return {'status': response.status_code,
                'json': json.loads(body) if response.status_code == 200 and body else {}}


def fingerprint():
    root = Path(__file__).parent
    hashes = {name: hashlib.sha256((root/name).read_bytes()).hexdigest()
              for name in ('authentik_canary.py', 'authentik_network_canary.py')}
    return hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()


def remote_source():
    source = (Path(__file__).parent/'authentik_canary.py').read_text()
    # Static source only in argv; all credentials are created later in memory.
    return '''import json, sys
class RemoteResponse:
    def __init__(self, value):
        self.status_code = value['status']; self.value = value['json']
    def json(self): return self.value
class RemoteClient:
    def __init__(self, **kwargs): pass
    def post(self, path, data, **kwargs):
        print('ASTER_HTTP='+json.dumps({'path':path,'data':data,
              'authorization':kwargs.get('HTTP_AUTHORIZATION')}), flush=True)
        line = sys.stdin.readline(65537)
        if not line or len(line) > 65536: raise RuntimeError('Controller unavailable')
        return RemoteResponse(json.loads(line))
ASTER_AUTH_HTTP_CLIENT=RemoteClient
ASTER_WORKER_AUTH_CANARY=True
''' + source


def run():
    encoded = base64.b64encode(remote_source().encode()).decode()
    shell_code = "import base64; exec(compile(base64.b64decode("+repr(encoded)+"),'network_auth_canary','exec'))"
    remote = 'pct exec 106 -- docker exec -i authentik-server-1 ak shell -c '+shlex.quote(shell_code)
    process = subprocess.Popen(['ssh', '-o', 'BatchMode=yes', 'proxmox', remote],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    selector = selectors.DefaultSelector(); selector.register(process.stdout, selectors.EVENT_READ)
    deadline = time.monotonic()+120
    buffer = b''; result = None; requests = 0
    try:
        with httpx.Client(timeout=5, follow_redirects=False, trust_env=False) as client:
            while time.monotonic() < deadline:
                if not selector.select(min(1, max(0, deadline-time.monotonic()))):
                    if process.poll() is not None: break
                    continue
                import os
                data = os.read(process.stdout.fileno(), 65536)
                if not data: break
                buffer += data
                if len(buffer) > 131072: raise ValueError('SSH response limit')
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    if line.startswith(PREFIX.encode()):
                        requests += 1
                        if requests > 4: raise ValueError('Request count exceeded')
                        try:
                            reply = forward(json.loads(line[len(PREFIX):]), client)
                        except Exception:
                            reply = {'status':503, 'json':{}}
                        process.stdin.write(json.dumps(reply).encode()+b'\n'); process.stdin.flush()
                    elif line.startswith(b'ASTER_AUTH_CANARY='):
                        raw = json.loads(line.split(b'=',1)[1])
                        # Whitelist only boolean values, never arbitrary remote output.
                        result = {'checks': {key: value for key,value in raw.get('checks',{}).items()
                                             if key in {'active','issuer','audience','client','subject_present',
                                               'scope','bounded_lifetime','revocation_response','revoked_denied'}
                                             and type(value) is bool},
                                  'temporary_objects_removed': raw.get('temporary_objects_removed') is True}
            process.stdin.close()  # EOF permits source-local finally cleanup on interruption.
            process.wait(timeout=15)
            if result is None or process.returncode != 0:
                raise RuntimeError('Canary incomplete; reconcile candidate objects before retry')
            result['https_requests'] = requests
            print(json.dumps(result))
    finally:
        if not process.stdin.closed: process.stdin.close()
        try: process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=5)
        process.stdout.close(); selector.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--approved-sha256')
    args = parser.parse_args()
    if not args.run:
        print(json.dumps({'manifest_sha256': fingerprint(), 'remote_changes': False}))
    elif args.approved_sha256 != fingerprint():
        raise SystemExit('Source changed or fingerprint missing; no remote execution')
    else:
        try: run()
        except Exception:
            raise SystemExit('Canary incomplete; verify temporary identity cleanup before any retry') from None
