"""Historical chain verification plus fresh current fixed-source admission.

Only an immutable transport-observed TrueNAS receipt pinned in the protected
booking card is accepted. Historical selected jobs are named explicitly;
latest jobs are not relabelled as the historical chain. Archives, mirror,
whole Proxmox job, consumer and hardware gates remain independently current.
"""
import hashlib,json,os,time
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
CAPTURE_SHA='1b9089d00aa045da7771e09e5aef0572003172456bf25699ba51abe2f62e4b67'
ZONE=ZoneInfo('America/Vancouver')

def require(v):
 if v is not True:raise RuntimeError('HISTORICAL_BACKUP_CHAIN_REFUSED')
def view_tasks(rows):
 out=[]
 for r in rows:
  if r.get('id') in {1,2,3}:
   j=r.get('job',{});out.append({'id':r['id'],'enabled':r.get('enabled'),'schedule':{k:r.get('schedule',{}).get(k) for k in ('hour','minute')},'job':{k:j.get(k) for k in ('id','method','arguments','state','time_started','time_finished')}})
 return sorted(out,key=lambda r:r['id'])
def select_history(value,current,*,cycle,now,artifact_ctimes):
 require(isinstance(value,dict) and set(value)=={'schema','source','producer_sha256','observed_epoch','tasks','jobs'})
 require(value['schema']=='b60-truenas-chain-history.v1' and value['source']=='truenas@192.168.20.40' and value['producer_sha256']==CAPTURE_SHA)
 require(type(value['observed_epoch']) is int and 0<=now-value['observed_epoch']<=7200)
 require(view_tasks(current)==value['tasks'] and len(value['tasks'])==3)
 require(all(r['job']['state']=='SUCCESS' for r in value['tasks']))
 require(isinstance(value['jobs'],list) and 3<=len(value['jobs'])<=128)
 selected=[]
 for task in (1,3,2):
  candidates=[]
  for j in value['jobs']:
   if not isinstance(j,dict) or j.get('arguments')!=[task] or j.get('method')!='rsynctask.run' or j.get('state')!='SUCCESS':continue
   start=j.get('time_started',{}).get('$date');finish=j.get('time_finished',{}).get('$date')
   if type(start) is not int or type(finish) is not int or not start<=finish<=value['observed_epoch']*1000:continue
   begun=datetime.fromtimestamp(start/1000,ZONE);done=datetime.fromtimestamp(finish/1000,ZONE)
   if begun.strftime('%Y_%m_%d')==cycle and done.strftime('%Y_%m_%d')==cycle and done.hour*60+done.minute<=255:candidates.append(j)
  require(bool(candidates));chosen=max(candidates,key=lambda j:j['time_finished']['$date'])
  row=next(r for r in value['tasks'] if r['id']==task)
  selected.append(dict(row,job=chosen))
 from fixed_source_adapters import _schedule_ok
 require(_schedule_ok(selected,date_prefix=cycle,artifact_ctimes=tuple(artifact_ctimes),lease_issued_epoch=now))
 # A later successful redundant pull is permitted only while the complete
 # latest metadata still exactly matches the authenticated pinned capture.
 # Failed/active/new/different jobs, chronology or artifacts reject admission.
 return selected

def backup(adapter,store,card,*,date_prefix,lease_issued_epoch):
 from lab_hours_exclusive_profile import protected_bytes
 from fixed_source_adapters import _truenas,_json
 from backup_receipt_adapter import verify_proxmox_artifacts,verify_lxc110_mirror
 from retained_archive_integrity import load_root_owned,verify,fixed_resolve
 from source_receipts import BackupSourceReceipt
 from admission_gate import EXPECTED_BACKUP_SOURCE
 root=Path('/var/lib/local-ai-lab');p=root/'backup-chain-history'/(card['booking_id']+'.json')
 raw=protected_bytes(p,maximum=65536)
 require(hashlib.sha256(raw).hexdigest()==card['backup_history_sha256'])
 current=_json(adapter.runner,_truenas(('midclt','call','rsynctask.query')),10)
 inventory=_json(adapter.runner,('pvesh','get','/nodes/proxmox/storage/backups/content','--content','backup','--output-format','json'),30)
 artifacts=verify_proxmox_artifacts(inventory,date_prefix=date_prefix)
 chosen=select_history(json.loads(raw),current,cycle=date_prefix,now=lease_issued_epoch,artifact_ctimes=[a.ctime for a in artifacts])
 mirror=_json(adapter.runner,_truenas(('midclt','call','filesystem.listdir','/mnt/Recovery/guests/aster-lxc110')),10)
 verify_lxc110_mirror(mirror,artifacts[1])
 proof=verify(load_root_owned(),inventory,date=date_prefix,now_epoch=lease_issued_epoch,resolve=fixed_resolve,lstat=os.lstat)
 store.write('backup-history-admission.json',{'schema':'b60-backup-historical-admission.v1','booking_id':card['booking_id'],'historical_source_sha256':hashlib.sha256(raw).hexdigest(),'source_observed_epoch':json.loads(raw)['observed_epoch'],'admission_epoch':lease_issued_epoch,'selected_job_ids':[r['job']['id'] for r in chosen],'latest_job_ids':[r['job']['id'] for r in view_tasks(current)],'archive_receipt':proof,'current_mirror_verified':True,'current_latest_jobs_exactly_match_capture':True},immutable=True)
 completed=datetime.fromtimestamp(chosen[-1]['job']['time_finished']['$date']/1000,ZONE)
 return BackupSourceReceipt(EXPECTED_BACKUP_SOURCE,EXPECTED_BACKUP_SOURCE,completed.hour*60+completed.minute,proof,True,True)
