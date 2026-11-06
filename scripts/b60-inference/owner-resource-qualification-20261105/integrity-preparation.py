"""One reserved R3 read-only integrity preparation before the TTS owner window."""
import os,sys,time,json,hashlib,subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
B='b60-exclusive-20261105-day-r4';R=Path('/var/lib/local-ai-lab');P=Path('/usr/local/libexec/local-ai-lease/exclusive-session')
sys.path.insert(0,str(P))
from host_exclusion import host_exclusion
from lab_hours_exclusive_session import SessionStore,canonical
from lab_hours_reservations import ReservationStore
from retained_archive_integrity import fixed_proxmox_inventory,fixed_resolve,fixed_probe,capture,verify,save_root_owned,load_root_owned
from full_inference_lab_sources import LocalProxmoxFullDrainSourceProducer,AcceptedBaseline,TrustedOwnerAttestation
from fixed_source_adapters import FixedSourceAdapters

def runner(command,timeout):
    p=subprocess.run(command,capture_output=True,text=True,timeout=timeout);return p.returncode,p.stdout

def main():
    assert os.geteuid()==0 and os.uname().nodename=='proxmox'
    deadline=int(sys.argv[1]);now=int(time.time())
    assert 1140<=deadline-now<=1500 and deadline<=1793927700-900
    with host_exclusion(R):
        assert not any(p.exists() for p in [R/'lease.json',R/'lease.lock',R/'full-inference-drain.json',R/'full-inference-drain.lock',Path('/run/local-ai-lab-operation.lock')])
        code,raw=runner(('/usr/local/sbin/local-ai-lease','status'),10);assert code==0 and json.loads(raw)=={'state':'ready'}
        pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in P.glob('*.py')}
        assert hashlib.sha256(canonical(pins)).hexdigest()=='e282a0e6a26a7e0302a70d2dbf953734048a5eb3697704d3cf0dce48803c3cd2'
        bookings=ReservationStore(R/'reservations',expected_uid=0);booking=bookings.get(B)
        assert booking['state']=='reserved' and booking['owner']=='b60-stream-a' and booking['kind']=='exclusive-stack' and booking['start_epoch']==1793927700
        second=bookings.get('b60-exclusive-20261105-day-r5');assert second['state']=='reserved' and second['start_epoch']==1793931300
        for proc in Path('/proc').glob('[0-9]*'):
            try:comm=(proc/'comm').read_text().strip()
            except FileNotFoundError:continue
            assert comm not in {'vzdump','zstd','rsync','pbs-client','proxmox-backup'}
        zone=ZoneInfo('America/Vancouver');cycle=datetime.fromtimestamp(now,zone).strftime('%Y_%m_%d')
        store=SessionStore(R/'exclusive-integrity'/B,expected_uid=0);fd=store.lock();phase='whole-backup-source'
        try:
            store.write('attempt.json',{'schema':'aster-exclusive-integrity-attempt.v1','booking_id':B,'started_epoch':now,'deadline_epoch':deadline,'preparation_only':True,'reason':'fresh-owner-loss-and-resource-qualification'},immutable=True)
            producer=LocalProxmoxFullDrainSourceProducer(runner,AcceptedBaseline('','',''),TrustedOwnerAttestation('b60-stream-a','reserved-early-integrity'))
            assert producer._backup_current(cycle) is True
            adapters=FixedSourceAdapters(runner,clock=lambda:datetime.fromtimestamp(time.time(),zone))
            old=load_root_owned();adapters.backup_from_retained(date_prefix=cycle,lease_issued_epoch=int(time.time()))
            store.write('previous-receipt.json',old,immutable=True)
            phase='archive-integrity-scan'
            receipt=capture(fixed_proxmox_inventory(),date=cycle,resolve=fixed_resolve,lstat=os.lstat,probe=fixed_probe,deadline_epoch=deadline)
            proof=verify(receipt,fixed_proxmox_inventory(),date=cycle,now_epoch=int(time.time()),resolve=fixed_resolve,lstat=os.lstat)
            # Freshness projection is a planning gate; actual admission rechecks.
            verify(receipt,fixed_proxmox_inventory(),date=cycle,now_epoch=booking['start_epoch']+120,resolve=fixed_resolve,lstat=os.lstat)
            phase='receipt-publication';store.write('receipt.json',receipt,immutable=True)
            assert load_root_owned()==old
            save_root_owned(receipt)
            adapters.backup_from_retained(date_prefix=cycle,lease_issued_epoch=int(time.time()))
            store.write('terminal.json',{'schema':'aster-exclusive-integrity-result.v1','booking_id':B,'state':'complete','archive_receipt':proof,'finished_epoch':int(time.time()),'peer_receipt_reused':False,'ai_stack_effects':False,'early_preparation':True},immutable=True)
            second_store=SessionStore(R/'exclusive-integrity'/'b60-exclusive-20261105-day-r5',expected_uid=0)
            second_store.write('terminal.json',{'schema':'aster-exclusive-integrity-result.v1','booking_id':'b60-exclusive-20261105-day-r5','state':'complete','archive_receipt':proof,'finished_epoch':int(time.time()),'ai_stack_effects':False,'shared_scan_booking':B},immutable=True)
            verify(receipt,fixed_proxmox_inventory(),date=cycle,now_epoch=second['start_epoch']+120,resolve=fixed_resolve,lstat=os.lstat)
            print(json.dumps({'state':'early-integrity-complete','booking_id':B,'ai_stack_effects':False}))
        except Exception:
            if not (store.root/'terminal.json').exists():store.write('terminal.json',{'schema':'aster-exclusive-integrity-result.v1','booking_id':B,'state':'no_go','first_failure_phase':phase,'ai_stack_effects':False},immutable=True)
            raise
        finally:os.close(fd)

if __name__=='__main__':main()
