#!/usr/bin/env python3
"""Mac mini coordinator; fixed reviewed operations, never an interactive AI loop."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time
from zoneinfo import ZoneInfo

TZ=ZoneInfo('America/Vancouver')
BRIDGE='/var/lib/b60-inference/nightly/bridge.py'
MIRROR='/root/b60-nightly/mirror-receipt.py'
def now(): return datetime.now(TZ)
def atomic(path, value):
    raw=(json.dumps(value,sort_keys=True)+'\n').encode()
    temporary=path.with_name(path.name+'.tmp')
    with os.fdopen(os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)
def call(host,*arguments,timeout=180):
    command=shlex.join(arguments)
    result=subprocess.run(['/usr/bin/ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
        '-o','IdentityAgent=none','-o','ConnectTimeout=10','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2',host,command],
        capture_output=True,text=True,timeout=timeout)
    if result.returncode: raise RuntimeError('bounded '+host+' operation failed rc='+str(result.returncode))
    return json.loads(result.stdout)
class Coordinator:
    def __init__(self,state,transport=call,clock=now,sleep=time.sleep):
        self.state=Path(state);self.transport=transport;self.clock=clock;self.sleep=sleep
        self.reserved=False;self.events=[]
    def event(self,stage,**fields):
        self.events.append(dict(at=self.clock().isoformat(),stage=stage,**fields))
        atomic(self.state/'status.json',dict(schema_version='1.0.0',run_id=self.run_id,events=self.events))
    def host(self,action,**fields):
        return self.transport('proxmox','/usr/bin/python3',BRIDGE,action,'--run-id',self.run_id,
            '--payload',json.dumps(fields,sort_keys=True),timeout=1500 if action=='prepare' else 180)
    def wait(self,hour,minute):
        target=self.clock().replace(hour=hour,minute=minute,second=0,microsecond=0)
        while self.clock()<target: self.sleep(min(40,(target-self.clock()).total_seconds()))
    def execute(self,read_only=False):
        local=self.clock()
        self.run_id=local.strftime('%Y%m%d')+'-native-openvino-nightly-1'
        if read_only:
            # No attempt claim, waits, reservation, recovery timer or GPU command.
            return self.host('inspect')
        if not (local.hour==21 and local.minute>=40 or local.hour==22 and local.minute<=5):
            return {'skipped':'outside preparation window','at':local.isoformat()}
        self.state.mkdir(parents=True,exist_ok=True,mode=0o700)
        os.chmod(self.state,0o700)
        with (self.state/'coordinator.lock').open('a') as lock:
            try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError: return {'skipped':'coordinator already running'}
            if (self.state/'review-required.json').exists():
                return {'skipped':'review required; no automatic experiment retry'}
            complete=0
            for record in self.state.glob('*.result.json'):
                stages=[e['stage'] for e in json.loads(record.read_text())['events']]
                complete+=int('comparison_complete' in stages and 'failed' not in stages and 'recovery_unconfirmed' not in stages)
            if complete>=2: return {'skipped':'two comparison sessions complete; await analysis'}
            claim=self.state/(self.run_id+'.attempt.json')
            if claim.exists(): return {'skipped':'daily attempt already claimed; no automatic retry'}
            with os.fdopen(os.open(claim,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as stream:
                json.dump({'started_at':local.isoformat(),'run_id':self.run_id},stream)
            self.event('preparation_started')
            try:
                preparation=self.host('prepare')
                if abs((self.clock()-datetime.fromisoformat(preparation['host_time'])).total_seconds())>30:
                    raise RuntimeError('mini/Proxmox clock skew exceeds 30 seconds')
                receipt=self.transport('truenas','/usr/bin/python3',MIRROR,'--archive-name',preparation['archive_name'],timeout=1000)
                if preparation['sha256']!=receipt['sha256'] or preparation['bytes']!=receipt['bytes']:
                    raise RuntimeError('backup/mirror hash or size mismatch')
                if self.clock().hour!=21 and not (self.clock().hour==22 and self.clock().minute<=9):
                    raise RuntimeError('preparation missed quiesce deadline')
                self.event('checkpoint_verified',archive_name=preparation['archive_name'],sha256=receipt['sha256'])
                self.wait(22,0)
                # Mark intent BEFORE an SSH operation: an uncertain response must
                # take the release path, even if the remote mutation succeeded.
                self.reserved=True
                self.host('reserve')
                self.event('restoration_watchdogs_armed_and_news_paused')
                while not self.host('drained')['drained']:
                    if self.clock().hour!=22 or self.clock().minute>=10:
                        raise RuntimeError('consumer drain deadline')
                    self.sleep(10)
                self.wait(22,12)
                receipt=self.transport('truenas','/usr/bin/python3',MIRROR,'--archive-name',preparation['archive_name'],timeout=180)
                preflight=self.host('preflight',mirror=receipt,backup=preparation)
                self.event('preflight_passed',collected_at=preflight['collected_at'])
                self.wait(22,15)
                self.host('start')
                self.event('bounded_comparison_started')
                while True:
                    status=self.host('status')
                    if status['terminal']:
                        if not status['success']: raise RuntimeError('experiment failed; inspect sanitized host evidence')
                        break
                    if self.clock().hour!=22 and not (self.clock().hour==23 and self.clock().minute<20):
                        raise RuntimeError('experiment cutoff reached')
                    self.sleep(20)
                self.event('comparison_complete')
            except Exception as error:
                # Never print subprocess stderr, credentials or raw inference.
                self.event('failed',reason=str(error) if isinstance(error,RuntimeError) else type(error).__name__)
                if any(e['stage']=='bounded_comparison_started' for e in self.events):
                    atomic(self.state/'review-required.json',{'run_id':self.run_id,'reason':'failed experiment; review required before further GPU runs'})
                raise
            finally:
                try:
                    if self.reserved:
                        try:
                            self.host('release')
                            self.event('accepted_sycl_and_schedules_restored')
                        except Exception:
                            self.event('recovery_unconfirmed',independent_host_watchdogs_retained=True)
                            if not (self.state/'review-required.json').exists():
                                atomic(self.state/'review-required.json',{'run_id':self.run_id,'reason':'unconfirmed recovery; do not retry'})
                            raise
                finally:
                    # Recovery failure must not erase the durable terminal record.
                    # Keep the review latch and independent host watchdogs intact.
                    atomic(self.state/(self.run_id+'.result.json'),dict(schema_version='1.0.0',run_id=self.run_id,events=self.events))
        return {'completed':True,'run_id':self.run_id}
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',type=Path,required=True)
    parser.add_argument('--read-only-check',action='store_true')
    args=parser.parse_args()
    print(json.dumps(Coordinator(args.state).execute(args.read_only_check),sort_keys=True))
if __name__=='__main__': main()
