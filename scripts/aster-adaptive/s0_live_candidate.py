"""Fixed one-shot adapter implementation; invocation requires the approval record.

No command-line options, generic operation/path argument, environment inheritance,
credential output or automatic retry. Trusted tests replace Popen/socket only.
"""
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys

from s0_lxc100_observe import command_catalog, catalog_digest
from s0_owned_cleanup import argv as cleanup_argv
from s0_probe_journal import Journal, canonical
from s0_probe_lifecycle import run_candidate
from validate_label_batch import unique
from s0_verified_read import read_owned_regular

ROOT=Path(__file__).resolve().parents[2]
EXPERIMENT='docs/projects/AI Projects/experiments/s0-routing-descriptive-v1/'
MANIFEST=ROOT/EXPERIMENT/'lxc100-attempt-3-manifest.json'
APPROVAL=ROOT/EXPERIMENT/'lxc100-attempt-3-approval.json'
JOURNAL=Path('/private/tmp/aster-s0-lxc100-attempt-3-20260926')
MODULES=('s0_lxc_memory.py','test_s0_attempt_2.py','test_s0_attempt_3.py','s0_verified_read.py','test_s0_authority_gate.py','s0_live_candidate.py','s0_probe_timing.py','s0_probe_lifecycle.py','s0_probe_journal.py',
         's0_owned_cleanup.py','s0_fixed_session.py','s0_lxc100_observe.py','s0_dns_observe.py',
         's0_probe_state.py','s0_feasibility_supervisor.py','validate_label_batch.py',
         'test_s0_live_candidate.py','test_s0_probe_lifecycle.py','test_s0_lxc100_candidate.py',
         'test_s0_probe_state.py','test_s0_feasibility_supervisor.py')
ARTIFACTS=frozenset('scripts/aster-adaptive/'+name for name in MODULES)|frozenset(EXPERIMENT+name for name in
    ('lxc100-fixture-payload.py.txt','LXC100-FEASIBILITY-PLAN.md','LXC100-ATTEMPT-2.md','RUN-FAILURE-OBSERVABILITY.md','RUN-003-GO-NO-GO.md','lxc100-integrated-manifest.json','lxc100-live-candidate-manifest.json','run-001/manifest.json','run-001/000.json','run-001/001.json','run-001/002.json','run-001/003.json','run-001/004.json','run-002/manifest.json','fixtures/pct-status-100-run001-diagnosis.txt'))
OPERATIONS=frozenset({'load-state','paths','health','create-owned-canary','run-proposal-only',
                      'unit-properties','cgroup','canary-stat','absence','host-lxc-status'})


def verify_bundle(expected_sha256):
    if type(expected_sha256) is not str or len(expected_sha256)!=64:raise ValueError('review pin required')
    raw=read_owned_regular(MANIFEST,32768)
    if len(raw)>32768 or hashlib.sha256(raw).hexdigest()!=expected_sha256:raise ValueError('manifest pin mismatch')
    value=json.loads(raw,object_pairs_hook=unique)
    if set(value)!={'format','status','base_commit','parent_integrated_manifest_sha256','artifacts','command_catalog_sha256','tests_passed','live_invoked'}:raise ValueError('manifest schema')
    if value['format']!='s0-live-candidate.v1' or value['status']!='attempt-3-released-candidate' or value['base_commit']!='4d561d7' or value['live_invoked'] is not False:raise ValueError('manifest state')
    if set(value['artifacts'])!=ARTIFACTS:raise ValueError('artifact set mismatch')
    for name,expected in value['artifacts'].items():
        path=ROOT/name
        if hashlib.sha256(read_owned_regular(path,131072)).hexdigest()!=expected:raise ValueError('artifact mismatch')
    if value['parent_integrated_manifest_sha256']!=value['artifacts'][EXPERIMENT+'lxc100-integrated-manifest.json']:raise ValueError('parent pin mismatch')
    if value['command_catalog_sha256']!=catalog_digest():raise ValueError('catalog mismatch')
    return value


def verify_prior_readonly_abort():
    root=ROOT/EXPERIMENT/'run-001'
    evidence=json.loads(read_owned_regular(root/'manifest.json',8192),object_pairs_hook=unique)
    if evidence['attempt']!='run-001' or evidence['source_commit']!='6715a05' or evidence['mutation_attempted'] is not False:
        raise ValueError('prior attempt not read-only')
    previous='0'*64;events=[]
    expected=['begin','observed','observed','observed','failed']
    for i in range(5):
        name=f'{i:03}.json';raw=read_owned_regular(root/name,8192)
        digest=hashlib.sha256(raw).hexdigest()
        if evidence['journal_files_sha256'][name]!=digest:raise ValueError('prior record hash')
        row=json.loads(raw,object_pairs_hook=unique)
        if canonical(row)!=raw or row['sequence']!=i or row['previous']!=previous or row['event']!=expected[i]:raise ValueError('prior journal chain/event')
        previous=digest;events.append(row)
    if events[-1]['data']!={'manual_recovery_required':False,'mutation_attempted':False,'stage':'preflight'}:
        raise ValueError('prior mutation uncertainty')
    if [r['data']['operation'] for r in events[1:4]]!=['load-state','paths','health']:
        raise ValueError('unexpected prior operations')


def verify_prior_run002():
    root=ROOT/EXPERIMENT/'run-002'
    evidence=json.loads(read_owned_regular(root/'manifest.json',16384),object_pairs_hook=unique)
    required={'format','attempt','date','result','failure_stage','precise_failure_cause','mutation_attempted',
              'manual_recovery_required','remote_stop_issued','corpus_evaluated','reviewed_manifest_sha256',
              'approval_record_sha256','command_catalog_sha256','post_run_readonly_dns_diagnostic',
              'files_sha256','consumed_approval_record_sha256'}
    if set(evidence)!=required or evidence['format']!='s0-run-evidence.v1' or evidence['attempt']!='run-002':
        raise ValueError('run002 evidence schema')
    if (evidence['result']!='failed-or-inconclusive' or evidence['failure_stage']!='preflight' or
        evidence['mutation_attempted'] is not False or evidence['manual_recovery_required'] is not False or
        evidence['remote_stop_issued'] is not False or evidence['corpus_evaluated'] is not False):
        raise ValueError('run002 mutation uncertainty')
    files=evidence['files_sha256']
    if type(files) is not dict or not files:raise ValueError('run002 file index')
    for name,expected in files.items():
        if type(name) is not str or '/' in name or name in ('.','..') or type(expected) is not str or len(expected)!=64:
            raise ValueError('run002 file index')
        if hashlib.sha256(read_owned_regular(root/name,131072)).hexdigest()!=expected:raise ValueError('run002 file hash')
    if files.get('reviewed-manifest.json')!=evidence['reviewed_manifest_sha256'] or files.get('approval-record.json')!=evidence['approval_record_sha256'] or files.get('consumed-approval-record.json')!=evidence['consumed_approval_record_sha256']:
        raise ValueError('run002 provenance hash')
    previous='0'*64;events=[]
    expected_events=['begin','observed','observed','observed','observed','resource-observation','failed']
    for i,event in enumerate(expected_events):
        raw=read_owned_regular(root/f'{i:03}.json',8192);row=json.loads(raw,object_pairs_hook=unique)
        if canonical(row)!=raw or row['sequence']!=i or row['previous']!=previous or row['event']!=event:raise ValueError('run002 journal chain')
        previous=hashlib.sha256(raw).hexdigest();events.append(row)
    if events[-1]['data']!={'manual_recovery_required':False,'mutation_attempted':False,'stage':'preflight'}:
        raise ValueError('run002 terminal uncertainty')
    if [r['data']['operation'] for r in events[1:5]]!=['load-state','paths','health','host-lxc-status']:
        raise ValueError('run002 operation order')


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
    """Fixed call path; the no-argument launcher validates the record first."""
    adapter=FixedAdapter(reviewed_pin)
    # Fixed exclusive path means a previous/partial attempt prevents a rerun.
    with Journal(JOURNAL,create=True) as journal:
        return run_candidate(journal,adapter.bundle['command_catalog_sha256'],
                             spawn=adapter.spawn,socket_factory=adapter.dns,
                             reviewed_manifest_sha256=reviewed_pin)


SCOPE={
    'attempt':'run-003',
    'host_resource_query':'pct status 100 --verbose',
    'maximum_container_inventory':32,
    'target':'Proxmox 192.168.50.10 / LXC 100',
    'unit':'aster-s0-feasibility-20260926.service',
    'canary':'/var/tmp/aster-s0-feasibility-20260926',
    'purpose':'one fixed invented-fixture isolation feasibility probe',
    'dns_target':'192.168.20.20:53',
    'runtime_max_seconds':15,
    'memory_max_bytes':67108864,
    'tasks_max':1,
    'accepted_corpus_evaluation':False,
    'package_installation':False,
    'other_infrastructure_changes':False,
    'git_push':False,
    'automatic_retry':False,
    'automatic_interrupted_recovery':False,
}
PROVENANCE={
    'human':'Jason',
    'authorization':'fresh explicit approval granted for exactly one run-003',
    'source':'Jason replied approve to the approve-both request after final run-003 scope was presented',
    'coordinating_task':'01a0d957-799b-7353-acbc-4765e85619f2',
    'cryptographic_identity_proof':False,
}


def validate_approval():
    raw=read_owned_regular(APPROVAL,8192)
    value=json.loads(raw,object_pairs_hook=unique)
    if set(value)!={'format','scope','provenance','reviewed_manifest_sha256','release'}:raise ValueError('approval schema')
    if value['format']!='s0-fixture-approval.v1' or canonical(value['scope'])!=canonical(SCOPE) or canonical(value['provenance'])!=canonical(PROVENANCE):
        raise ValueError('approval scope/provenance mismatch')
    release=value['release']
    if type(release) is not dict or set(release)!={'technical_review','exclusive_operator_window','one_shot_execution','human_approval'}:
        raise ValueError('release schema')
    if release!={'technical_review':'passed','exclusive_operator_window':'confirmed','one_shot_execution':'released','human_approval':'approved-for-run-003'}:
        raise PermissionError('final technical review and operator window release required')
    pin=value['reviewed_manifest_sha256']
    verify_bundle(pin)
    verify_prior_readonly_abort()
    verify_prior_run002()
    return pin


def invoke_once():
    # No flags, approval Boolean or caller-supplied hash/path can bypass the record.
    if len(sys.argv)!=1:raise PermissionError('one-shot launcher accepts no arguments')
    pin=validate_approval()
    return _prepared_one_shot(pin)


if __name__=='__main__':
    result=invoke_once()
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if result['status']=='fixture-pass' else 1)
