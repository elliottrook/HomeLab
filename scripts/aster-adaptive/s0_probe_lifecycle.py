"""Integrated fixed probe candidate. Default transports deny all external I/O.

Shares validated observations and gate semantics with the reviewed fake state
machine. Does not convert real responses into its invented ownership constants.
"""
import hashlib
import json
from s0_fixed_session import FixedSession, denied_spawn
from s0_dns_observe import collect_stub_dns, denied_socket
from s0_probe_state import decode, health, exact, reject, unique, CHECKS
from s0_lxc100_observe import (catalog_digest, require_pinned_catalog, parse_canary,
                               parse_running, parse_health, parse_absence)
from s0_feasibility_supervisor import load_state_ok
from s0_probe_timing import inspect_worker
from s0_lxc_memory import combined_health


def response(result):
    reject(result['status']!='complete','session incomplete')
    return {k:result[k] for k in ('returncode','stdout','stderr')}


def run_candidate(journal,root_hash,*,spawn=denied_spawn,socket_factory=denied_socket,reviewed_manifest_sha256=None):
    require_pinned_catalog(root_hash)
    reject(bool(journal.records),'existing attempt must use read-only recovery')
    baseline=None;receipt=None;worker=None;mutation=False;total=0;stage='preflight';passed=False
    journal.append('begin',{'catalog_sha256':root_hash,'reviewed_manifest_sha256':reviewed_manifest_sha256,
                            'transport':'fixed-live-adapter' if reviewed_manifest_sha256 else 'injected-fixture'})

    def record(op,result):
        nonlocal total
        total+=len(result['stdout'])+len(result['stderr'])
        reject(total>65536,'transcript limit')
        journal.append('observed',{'operation':op,'argv_sha256':result['argv_sha256'],
                                  'response_sha256':hashlib.sha256(result['stdout']+b'\0'+result['stderr']).hexdigest(),
                                  'status':result['status']})
        return response(result)

    def call(op,**kwargs):
        session=FixedSession(op,root_hash,spawn=spawn,**kwargs)
        try:return record(op,session.finish())
        finally:session.close()

    def read_health():
        measured,resources=combined_health(call('health'),call('host-lxc-status'))
        journal.append('resource-observation',resources)
        return measured

    def check_services():
        reject(read_health()!=baseline,'health changed')
        dns_result=collect_stub_dns(socket_factory=socket_factory)
        journal.append('health-dns-verified',{'dns_elapsed_ms':[r['elapsed_ms'] for r in dns_result['responses']]})

    try:
        initial=call('load-state')
        reject(not load_state_ok(**initial),'unit exists or uncertain')
        paths=decode(call('paths'));exact(paths,{'canary_directory_absent','runtime_probe_absent'})
        reject(any(v is not True for v in paths.values()),'existing paths')
        baseline=read_health()
        dns_result=collect_stub_dns(socket_factory=socket_factory)
        journal.append('preflight-verified',{'baseline':baseline,'dns_elapsed_ms':[r['elapsed_ms'] for r in dns_result['responses']]})
        stage='create';journal.append('create-intent',{});mutation=True
        created=parse_canary(call('create-owned-canary'))
        journal.append('canary-created',created)
        stage='run';journal.append('run-intent',{})
        worker=FixedSession('run-proposal-only',root_hash,spawn=spawn)
        ready=worker.await_ready();exact(ready,{'scope','phase','checks','pid'})
        reject(ready['scope']!='invented-fixture-only' or ready['phase']!='ready' or type(ready['pid']) is not int,'readiness schema')
        exact(ready['checks'],CHECKS);reject(any(v is not True for v in ready['checks'].values()),'probe checks failed')
        running,current_canary=inspect_worker(call,worker.started)
        reject(running['main_pid']!=ready['pid'],'worker identity mismatch')
        reject(current_canary!=created,'canary changed')
        receipt={'canary':created,'invocation_id':running['invocation_id'],'main_pid':running['main_pid'],'completed':False}
        journal.append('ownership-bound',receipt)
        result=record('run-proposal-only',worker.finish())
        reject(result['returncode']!=0 or result['stderr']!=b'','worker failure')
        lines=result['stdout'].splitlines();reject(len(lines)!=2,'worker record count')
        first=json.loads(lines[0],object_pairs_hook=unique);last=json.loads(lines[1],object_pairs_hook=unique)
        reject(first!=ready,'readiness changed');exact(last,{'scope','phase','passed'})
        reject(last!={'scope':'invented-fixture-only','phase':'done','passed':True},'completion failed')
        receipt={**receipt,'completed':True};journal.append('worker-completed',receipt)
        stage='postflight';check_services()
        stage='cleanup';journal.append('cleanup-intent',receipt)
        removed=decode(call('guarded-cleanup',receipt=receipt))
        reject(removed!={'removed_owned_canary':True},'cleanup unverified')
        absent=parse_absence(call('absence'));reject(any(v is not True for v in absent.values()),'remaining paths/cgroup')
        # Inactive loaded unit is permissible; no reset-failed/stop by name is issued.
        stage='final-health';check_services()
        journal.append('complete',{'fixture_passed':True,'cleanup_verified':True});passed=True
    except Exception:
        journal.append('failed',{'stage':stage,'mutation_attempted':mutation,
                                 'manual_recovery_required':mutation})
    finally:
        if worker is not None:worker.close()
        if mutation and not passed and baseline is not None:
            try:check_services()
            except Exception:journal.append('health-unverified',{})
    return {'status':'fixture-pass' if passed else 'failed-or-inconclusive',
            'manual_recovery_required':mutation and not passed,'corpus_evaluated':False,
            'remote_stop_issued':False,'live_enabled':reviewed_manifest_sha256 is not None}


def live_entry(*_,**__):raise PermissionError('integrated live entry disabled pending final review')
