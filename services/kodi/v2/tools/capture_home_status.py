"""One-shot operator capture of the new display report; never a TV identity."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from home_status_model import view

SOURCE=r'''
import json,stat
from pathlib import Path
p=Path('/share/aster-home-registry/dashboard.json')
if p.is_symlink() or p.parent.is_symlink():raise SystemExit(1)
before=p.stat()
if not stat.S_ISREG(before.st_mode) or stat.S_IMODE(before.st_mode)!=0o600 or before.st_nlink!=1 or not 0<before.st_size<=262144:raise SystemExit(1)
raw=p.read_bytes()
after=p.stat()
if any(getattr(before,k)!=getattr(after,k) for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_nlink')):raise SystemExit(1)
value=json.loads(raw)
if value.get('schema_version')!=4 or value.get('snapshot_id')!='ha-home-dashboard-v4':raise SystemExit(1)
keys={'id','name','kind','availability','state','value','unit','condition','humidity','remaining','finishes_at'}
rows=value.get('entities')
if not isinstance(rows,list) or len(rows)>256 or any(not isinstance(r,dict) for r in rows):raise SystemExit(1)
clean={'schema_version':4,'snapshot_id':'ha-home-dashboard-v4','observed_at':value.get('observed_at'),
       'entities':[{k:r[k] for k in keys if k in r} for r in rows]}
print(json.dumps(clean,ensure_ascii=True,allow_nan=False,separators=(',',':')))
'''

def main():
    parser=argparse.ArgumentParser();parser.add_argument('destination',type=Path);args=parser.parse_args()
    command=shlex.join(['qm','guest','exec','103','--','docker','exec','homeassistant','python3','-c',SOURCE])
    reply=subprocess.run(['ssh','-o','BatchMode=yes','proxmox',command],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=30,check=True)
    if len(reply.stdout)>524288:raise ValueError('home-status-transport-size')
    guest=json.loads(reply.stdout)
    if guest.get('exitcode')!=0 or guest.get('out-truncated')!=0:raise ValueError('home-status-source-failed')
    raw=guest.get('out-data','').encode()
    result=view(raw)
    if result.state!='fresh':raise ValueError('home-status-source-'+result.state)
    fd=os.open(str(args.destination),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:stream.write(raw)
    print(json.dumps(dict(captured=True,readings=len(result.rows),fresh=True,credentials_exported=False,scheduled=False)))

if __name__=='__main__':main()
