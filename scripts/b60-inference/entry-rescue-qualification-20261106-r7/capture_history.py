"""Metadata-only TrueNAS producer, invoked over existing verified admin SSH.

No task, schedule, backup, credential or access-control mutation. The only
write is a new root-private content-free evidence receipt. Collector source
bytes are hashed by the authenticated invoking transport before interpretation.
"""
import hashlib,json,os,subprocess,time
from pathlib import Path

def call(method,*args):
 p=subprocess.run(['midclt','call',method,*args],capture_output=True,text=True,timeout=20)
 if p.returncode:raise RuntimeError('HISTORY_SOURCE_QUERY_FAILED')
 return json.loads(p.stdout)
def job(v):return {k:v.get(k) for k in ('id','method','arguments','state','time_started','time_finished')}
def tasks(rows):
 out=[]
 for r in rows:
  if r.get('id') in {1,2,3}:
   out.append({'id':r['id'],'enabled':r.get('enabled'),'schedule':{k:r.get('schedule',{}).get(k) for k in ('hour','minute')},'job':job(r.get('job',{}))})
 return sorted(out,key=lambda r:r['id'])
if os.geteuid()!=0:raise RuntimeError('ROOT_PRODUCER_REQUIRED')
before=tasks(call('rsynctask.query'))
history=[job(v) for v in call('core.get_jobs','[["method","=","rsynctask.run"]]') if v.get('arguments') in ([1],[2],[3])]
after=tasks(call('rsynctask.query'))
if before!=after or len(before)!=3 or any(r['job']['state']!='SUCCESS' for r in before):raise RuntimeError('HISTORY_SOURCE_CHANGED_OR_ACTIVE')
if not 3<=len(history)<=128:raise RuntimeError('BOUNDED_HISTORY_REQUIRED')
value={'schema':'b60-truenas-chain-history.v1','source':'truenas@192.168.20.40','producer_sha256':COLLECTOR_SHA256,'observed_epoch':int(time.time()),'tasks':before,'jobs':history}
raw=json.dumps(value,sort_keys=True,separators=(',',':')).encode()
if len(raw)>65536:raise RuntimeError('HISTORY_OVERSIZED')
root=Path('/mnt/Media/.local-ai-lease/b60-chain-history');root.mkdir(mode=0o700,exist_ok=True)
s=root.lstat()
if root.is_symlink() or s.st_uid!=0 or s.st_mode&0o077:raise RuntimeError('HISTORY_CUSTODY')
p=root/'b60-exclusive-20261106-day-r7.json';fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
fd=os.open(root,os.O_RDONLY);os.fsync(fd);os.close(fd)
print(json.dumps({'receipt':value,'sha256':hashlib.sha256(raw).hexdigest(),'path':str(p)},sort_keys=True))
