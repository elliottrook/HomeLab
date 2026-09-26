"""Fixed one-shot adapter implementation; invocation entry remains disabled.

No command-line interface, operation/path argument, environment inheritance,
credential output or automatic retry. Trusted tests replace Popen/socket only.
"""
import hashlib
import json
from pathlib import Path
import socket
import subprocess

from s0_lxc100_observe import command_catalog, catalog_digest
from s0_owned_cleanup import argv as cleanup_argv
from s0_probe_journal import Journal
from s0_probe_lifecycle import run_candidate
from validate_label_batch import unique

ROOT=Path(__file__).resolve().parents[2]
EXPERIMENT='docs/projects/AI Projects/experiments/s0-routing-descriptive-v1/'
MANIFEST=ROOT/EXPERIMENT/'lxc100-live-candidate-manifest.json'
JOURNAL=Path('/private/tmp/aster-s0-lxc100-one-shot-20260926')
MODULES=('s0_live_candidate.py','s0_probe_timing.py','s0_probe_lifecycle.py','s0_probe_journal.py',
         's0_owned_cleanup.py','s0_fixed_session.py','s0_lxc100_observe.py','s0_dns_observe.py',
         's0_probe_state.py','s0_feasibility_supervisor.py','validate_label_batch.py',
         'test_s0_live_candidate.py','test_s0_probe_lifecycle.py','test_s0_lxc100_candidate.py',
         'test_s0_probe_state.py','test_s0_feasibility_supervisor.py')
ARTIFACTS=frozenset('scripts/aster-adaptive/'+name for name in MODULES)|frozenset(EXPERIMENT+name for name in
    ('lxc100-fixture-payload.py.txt','LXC100-FEASIBILITY-PLAN.md','LXC100-LIVE-CANDIDATE.md','lxc100-integrated-manifest.json'))
OPERATIONS=frozenset({'load-state','paths','health','create-owned-canary','run-proposal-only',
                      'unit-properties','cgroup','canary-stat','absence'})


def verify_bundle(expected_sha256):
    if type(expected_sha256) is not str or len(expected_sha256)!=64:raise ValueError('review pin required')
    with MANIFEST.open('rb') as f:raw=f.read(32769)
    if len(raw)>32768 or hashlib.sha256(raw).hexdigest()!=expected_sha256:raise ValueError('manifest pin mismatch')
    value=json.loads(raw,object_pairs_hook=unique)
    if set(value)!={'format','status','base_commit','parent_integrated_manifest_sha256','artifacts','command_catalog_sha256','tests_passed','live_invoked'}:raise ValueError('manifest schema')
    if value['format']!='s0-live-candidate.v1' or value['status']!='review-required-invocation-disabled' or value['base_commit']!='28a9e49' or value['live_invoked'] is not False:raise ValueError('manifest state')
    if set(value['artifacts'])!=ARTIFACTS:raise ValueError('artifact set mismatch')
    for name,expected in value['artifacts'].items():
        path=ROOT/name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('artifact mismatch')
    if value['parent_integrated_manifest_sha256']!=value['artifacts'][EXPERIMENT+'lxc100-integrated-manifest.json']:raise ValueError('parent pin mismatch')
    if value['command_catalog_sha256']!=catalog_digest():raise ValueError('catalog mismatch')
    return value


class FixedDNS:
    """Connected UDP socket pinned to one DNS server; no arbitrary peer API."""
    def __init__(self):
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        try:self.sock.settimeout(2);self.sock.connect(('192.168.20.20',53))
        except BaseException:self.sock.close();raise
    def settimeout(self,value):
        if value!=2:raise ValueError('fixed timeout only')
        self.sock.settimeout(2)
    def sendto(self,packet,peer):
        import struct
        from s0_probe_state import QUERY_ID,QUESTION
        expected=struct.pack('!6H',QUERY_ID,0x0100,1,0,0,0)+QUESTION
        if peer!=('192.168.20.20',53) or packet!=expected:raise ValueError('fixed DNS query only')
        return self.sock.send(packet)
    def recvfrom(self,size):
        if size!=513:raise ValueError('fixed DNS bound only')
        return self.sock.recvfrom(513)
    def close(self):self.sock.close()


class FixedAdapter:
    """Not an authorization API. Construct only after the reviewed one-shot gate."""
    def __init__(self,reviewed_pin):
        self.pin=reviewed_pin;self.bundle=verify_bundle(reviewed_pin)

    def spawn(self,argv,**kwargs):
        verify_bundle(self.pin)
        allowed=[v for k,v in command_catalog().items() if k in OPERATIONS]
        if argv not in allowed:
            # Fixed cleanup source with only validated bounded receipt data.
            import shlex
            from s0_owned_cleanup import SOURCE
            from s0_feasibility_supervisor import SSH
            if type(argv) is not list or len(argv)!=len(SSH)+1 or argv[:len(SSH)]!=list(SSH):raise ValueError('fixed SSH only')
            inner=shlex.split(argv[-1])
            if len(inner)!=11 or inner[:9]!=['pct','exec','100','--','/usr/bin/python3.13','-I','-S','-B','-c'] or inner[9]!=SOURCE:raise ValueError('fixed cleanup only')
            receipt=json.loads(inner[10],object_pairs_hook=unique)
            if cleanup_argv(receipt)!=argv:raise ValueError('noncanonical cleanup data')
        required={'env':{'LANG':'C','LC_ALL':'C'},'stdin':subprocess.DEVNULL,
                  'stdout':subprocess.PIPE,'stderr':subprocess.PIPE,'start_new_session':True,'close_fds':True}
        if kwargs!=required:raise ValueError('fixed process options required')
        # Exact argv starts /usr/bin/ssh; no shell=True, Git transport or wrapper.
        return subprocess.Popen(argv,**required)

    def dns(self):
        verify_bundle(self.pin)
        return FixedDNS()


def _prepared_one_shot(reviewed_pin):
    """Complete call path for review only. Never called by enabled entry/tests."""
    adapter=FixedAdapter(reviewed_pin)
    # Fixed exclusive path means a previous/partial attempt prevents a rerun.
    with Journal(JOURNAL,create=True) as journal:
        return run_candidate(journal,adapter.bundle['command_catalog_sha256'],
                             spawn=adapter.spawn,socket_factory=adapter.dns,
                             reviewed_manifest_sha256=reviewed_pin)


def invoke_once(*_,**__):
    raise PermissionError('final technical review pending; one-shot invocation disabled')


if __name__=='__main__':invoke_once()
