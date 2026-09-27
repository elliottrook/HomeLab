"""Generated invented isolation probe; no external inputs."""
import base64,errno,hashlib,json,os,pathlib,socket
RUN_ID = 'isolation-fixture-002'
MANIFEST = '73b4d01f94f9ab31919ba024320e70d8152fe6efdd03896ef1cdc086ff1ff63c'
PREFIX = b'ASTER_S0_V1'
CHUNK = 3072
EXPECTED_ENV = frozenset({
    'HOME','INVOCATION_ID','JOURNAL_STREAM','LANG','LC_ALL','LOGNAME',
    'MEMORY_PRESSURE_WATCH','MEMORY_PRESSURE_WRITE','PATH','SHELL',
    'SYSTEMD_EXEC_PID','USER'
})
keys = frozenset(os.environ)
checks = {
    'environment_allowlisted': keys <= EXPECTED_ENV,
    'fixed_locale': os.environ.get('LANG') == 'C' and os.environ.get('LC_ALL') == 'C',
    'unprivileged': os.geteuid() != 0,
    'loopback_only': sorted(p.name for p in pathlib.Path('/sys/class/net').iterdir()) == ['lo'],
}
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
       {errno.EPERM, errno.EACCES, errno.EAFNOSUPPORT})
denied('unix_socket_denied', lambda: socket_attempt(socket.AF_UNIX),
       {errno.EPERM, errno.EACCES, errno.EAFNOSUPPORT})
denied('fork_denied', fork_attempt, {errno.EPERM, errno.EACCES, errno.EAGAIN})
denied('unrelated_read_denied', denied_read, {errno.EPERM, errno.EACCES})
denied('system_write_denied', denied_write, {errno.EROFS, errno.EPERM, errno.EACCES})
value = {
    'authorization': 'invented-fixture-only',
    'checks': checks,
    'corpus_evaluated': False,
    'fixture': True,
    'result': 'isolation-pass' if all(checks.values()) else 'isolation-fail',
}
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
(out/'protocol.txt').write_bytes(b'\n'.join(lines)+b'\n')
raise SystemExit(0 if all(checks.values()) else 1)
