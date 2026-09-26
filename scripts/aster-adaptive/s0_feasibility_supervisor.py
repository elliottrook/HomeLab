"""Bounded Mac supervisor fixtures and non-executing exact command proposals.

run_fixture accepts only named, constant local child programs. Nothing invokes SSH.
The proposed remote command set cannot be passed to this supervisor's executor.
"""
import hashlib
import json
import os
import selectors
import shlex
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

UNIT = 'aster-s0-feasibility-20260926.service'
CANARY_DIR = '/var/tmp/aster-s0-feasibility-20260926'
PAYLOAD_SHA256 = '497ffce4be2431284dc8a03b5bc33e48ed4264199dba36e9c0925fe8252f9850'
PAYLOAD = (Path(__file__).resolve().parents[2] / 'docs/projects/AI Projects/experiments/s0-routing-descriptive-v1/lxc100-fixture-payload.py.txt')
SSH = ('/usr/bin/ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'root@192.168.50.10')
CAP = 8192
DEADLINE = 20.0
CREATE_SOURCE = ('import os; p="/var/tmp/aster-s0-feasibility-20260926"; '
                 'os.mkdir(p,0o755); os.chmod(p,0o755); '
                 'f=os.open(p+"/canary",os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644); '
                 'os.fchmod(f,0o644); os.write(f,b"x"); os.close(f)')
CLEANUP_SOURCE = ('import os,stat; p="/var/tmp/aster-s0-feasibility-20260926"; '
                  's=os.lstat(p); assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.geteuid() and stat.S_IMODE(s.st_mode)==0o755; '
                  'assert os.listdir(p)==["canary"]; '
                  'f=os.open(p+"/canary",os.O_RDONLY|os.O_NOFOLLOW); '
                  't=os.fstat(f); assert stat.S_ISREG(t.st_mode) and t.st_uid==os.geteuid() and t.st_nlink==1 and stat.S_IMODE(t.st_mode)==0o644; '
                  'assert os.read(f,2)==b"x"; os.close(f); os.unlink(p+"/canary"); os.rmdir(p)')
PROPERTIES = (
    'Environment=LANG=C LC_ALL=C',
    'UnsetEnvironment=PYTHONPATH PYTHONHOME PYTHONUSERBASE PYTHONSTARTUP PYTHONINSPECT PYTHONWARNINGS PYTHONBREAKPOINT PYTHONPYCACHEPREFIX LD_PRELOAD LD_LIBRARY_PATH LD_AUDIT LD_DEBUG LD_PROFILE GLIBC_TUNABLES DYLD_INSERT_LIBRARIES DYLD_LIBRARY_PATH DYLD_FRAMEWORK_PATH DYLD_FALLBACK_LIBRARY_PATH DYLD_FALLBACK_FRAMEWORK_PATH SSH_AUTH_SOCK SSH_AGENT_PID GPG_AGENT_INFO DBUS_SESSION_BUS_ADDRESS KRB5CCNAME AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN OPENAI_API_KEY ANTHROPIC_API_KEY VAULT_TOKEN BAO_TOKEN',
    'Type=exec', 'DynamicUser=yes', 'NoNewPrivileges=yes', 'CapabilityBoundingSet=',
    'PrivateNetwork=yes', 'PrivateDevices=yes', 'ProtectSystem=strict', 'ProtectHome=yes',
    'InaccessiblePaths=/etc /opt /srv /var /run', 'TemporaryFileSystem=/tmp:ro',
    'ProtectKernelTunables=yes', 'ProtectKernelModules=yes', 'ProtectControlGroups=yes',
    'SystemCallArchitectures=native',
    'SystemCallFilter=~@network-io @mount clone clone3 fork vfork', 'SystemCallErrorNumber=EPERM',
    'MemoryMax=67108864', 'MemorySwapMax=0', 'TasksMax=1', 'CPUQuota=10%',
    'LimitCPU=2', 'LimitFSIZE=8192', 'RuntimeMaxSec=15', 'TimeoutStopSec=2',
    'KillMode=control-group', 'UMask=0077', 'WorkingDirectory=/',
)
FIXTURES = {
    'success': 'import os; os.write(1,b"fixture-out"); os.write(2,b"fixture-err")',
    'flood-both': 'import os,time; os.write(1,b"a"*5000); os.write(2,b"b"*5000); time.sleep(30)',
    'stderr-flood': 'import os,time; os.write(2,b"b"*16384); time.sleep(30)',
    'timeout': 'import time; time.sleep(30)',
    'nonzero': 'import os; os.write(2,b"fixture-failure"); raise SystemExit(3)',
    'invalid-utf8': 'import os; os.write(1,bytes([255]))',
    'closed-streams': 'import os,time; os.close(1); os.close(2); time.sleep(30)',
}


FIXTURE_HASHES = {'success': '29d673cfaf514b5e973ee1779027d875bcedef7aa82a806722fc9f9d6bf83a02', 'flood-both': 'b91d1a05f872359633fca2788f2d8dddb161a37fbc704ff69233ce04dbe3d075', 'stderr-flood': '717a14a720e1fcd59720c70413e279d2c792cfe7008214929a8046130ab54d4b', 'timeout': '92a1825dd7748fa5edf4c515a2a8325e6c81d6f9f3b3d5a88141b2de03d248e2', 'nonzero': 'a19e1fb00745191297847272626e797fa3adabae6904dfad3dc94767fbaf7f2e', 'invalid-utf8': '10ac92e615c412142a63b5ea046ab35ea724a731a391441fb5d53066bf9782dd', 'closed-streams': 'e777087541f8eab33fb07b0c906fbe49eb2e05e47076e15f37a85ef7f97488bc'}

def sha(raw): return hashlib.sha256(raw).hexdigest()


def remote_args(inner):
    # Pure construction only. Exactly one remote shell string, never JSON shell escaping.
    return [*SSH, shlex.join(['pct', 'exec', '100', '--', *inner])]


def command_proposal():
    raw = PAYLOAD.read_bytes()
    if sha(raw) != PAYLOAD_SHA256: raise ValueError('constant payload hash changed')
    payload = raw.decode('utf-8')
    commands = {
        'create-canary': remote_args(['/usr/bin/python3.13', '-I', '-S', '-B', '-c', CREATE_SOURCE]),
        'remove-canary': remote_args(['/usr/bin/python3.13', '-I', '-S', '-B', '-c', CLEANUP_SOURCE]),
        'load-state': remote_args(['/usr/bin/systemctl', 'show', UNIT, '-p', 'LoadState']),
        'stop-only-probe': remote_args(['/usr/bin/systemctl', 'stop', UNIT]),
        'reset-only-probe': remote_args(['/usr/bin/systemctl', 'reset-failed', UNIT]),
        'run-proposal-only': remote_args(['/usr/bin/systemd-run', '--unit='+UNIT, '--wait', '--pipe', '--quiet',
                                          *['--property='+x for x in PROPERTIES],
                                          '/usr/bin/python3.13', '-I', '-S', '-B', '-c', payload]),
    }
    return {'commands': commands, 'command_sha256': sha(json.dumps(commands, sort_keys=True).encode()),
            'payload_sha256': PAYLOAD_SHA256, 'live_authorized': False}


def verify_proposal(candidate):
    if candidate != command_proposal(): raise ValueError('command/payload proposal mismatch')


def load_state_ok(returncode, stdout, stderr):
    return (type(returncode) is int and returncode == 0 and stdout == b'LoadState=not-found\n'
            and stderr == b'')


def execute_remote(*_, **__):
    raise PermissionError('remote/live execution disabled; no approval path in this implementation')


def run_fixture(name, *, deadline=DEADLINE):
    if type(name) is not str or name not in FIXTURES: raise ValueError('unknown fixed fixture')
    if type(deadline) not in (int, float) or not 0 < deadline <= DEADLINE:
        raise ValueError('invalid fixture deadline')
    if sha(FIXTURES[name].encode()) != FIXTURE_HASHES[name]: raise ValueError('fixture source hash changed')
    argv = [sys.executable, '-I', '-S', '-B', '-c', FIXTURES[name]]
    argv_hash = sha(json.dumps(argv).encode())
    retained = {'stdout': bytearray(), 'stderr': bytearray()}
    total = 0; status = 'running'; killed = False; reaped = False
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='aster-s0-supervisor-fixture-') as scratch:
        child = subprocess.Popen(argv, cwd=scratch, env={'LANG':'C','LC_ALL':'C'},
                                 stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, start_new_session=True, close_fds=True)
        selector = selectors.DefaultSelector()
        try:
            for label, stream in (('stdout',child.stdout),('stderr',child.stderr)):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, label)
            while selector.get_map() or child.poll() is None:
                remaining = deadline - (time.monotonic()-started)
                if remaining <= 0: status='timeout'; break
                for key,_ in selector.select(min(.05,remaining)):
                    try: chunk=os.read(key.fileobj.fileno(),1024)
                    except BlockingIOError: continue
                    if not chunk:
                        selector.unregister(key.fileobj); continue
                    room=CAP-total
                    retained[key.data].extend(chunk[:room]); total += min(len(chunk),room)
                    if len(chunk)>room: status='output-limit'; break
                if status!='running': break
            if status=='running': status='complete' if child.wait(timeout=1)==0 else 'child-failed'
        finally:
            selector.close()
            if child.poll() is None:
                os.killpg(child.pid,signal.SIGKILL);killed=True
            try:
                child.wait(timeout=2);reaped=True
            finally:
                child.stdout.close();child.stderr.close()
    text = {}
    try: text = {k:bytes(v).decode('utf-8',errors='strict') for k,v in retained.items()}
    except UnicodeDecodeError:
        status='invalid-output';text={'stdout':None,'stderr':None}
    fallback = {'needed':status!='complete','executed':False,
                'scope':'representation-only; fixture child is local, no SSH invocation',
                'argv':remote_args(['/usr/bin/systemctl','stop',UNIT])}
    return {'scope':'invented-local-child-only','fixture':name,'argv_sha256':argv_hash,
            'status':status,'returncode':child.returncode,'retained_bytes':total,
            'output':text,'killed':killed,'reaped':reaped,
            'elapsed_seconds':time.monotonic()-started,'remote_stop_fallback':fallback,
            'live_authorized':False,'corpus_evaluated':False}


if __name__=='__main__':
    raise SystemExit('No execution CLI. Named fixture tests only; remote gate disabled.')
