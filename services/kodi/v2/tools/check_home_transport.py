"""Manual/Doctor-capable fixed-file delivery health, read-only on both hosts."""
import json
from pathlib import Path
import shlex
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from home_delivery_health import assess

SOURCE=r'''
import json,stat
from pathlib import Path
p=Path(REPORT)
s=p.lstat()
if p.is_symlink() or not stat.S_ISREG(s.st_mode) or stat.S_IMODE(s.st_mode)!=0o600 or s.st_nlink!=1 or not 0<s.st_size<=4096:raise SystemExit(1)
raw=json.loads(p.read_bytes())
keys={'ok','code','checked_at','last_success_at','last_source_at','last_sha256','sha256','source_at','received_at','readings'}
print(json.dumps({k:v for k,v in raw.items() if k in keys},separators=(',',':')))
'''

def command(path):return SOURCE.replace('REPORT',repr(path))
def run(host,argv):
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=4',host,shlex.join(argv)],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=20,check=True)
    if len(result.stdout)>16000:raise ValueError('health-result-size')
    return json.loads(result.stdout)

def main():
    try:
        if len(sys.argv)!=1:raise ValueError('health-no-arguments')
        guest=run('proxmox',['qm','guest','exec','103','--','docker','exec','homeassistant','python3','-c',command('/config/.aster-home-delivery/health.json')])
        if guest.get('exitcode')!=0 or guest.get('out-truncated')!=0:raise ValueError('health-source-unavailable')
        ha=json.loads(guest['out-data'])
        hp=run('root@192.168.1.140',['python3','-c',command('/storage/.aster-checkpoints/aster-home-status1/delivery-health.json')])
        result=assess(ha,hp)
    except (ValueError,OSError,subprocess.SubprocessError,KeyError):result=dict(ok=False,code='delivery-health-unavailable')
    print(json.dumps(result));return 0 if result['ok'] else 1

if __name__=='__main__':raise SystemExit(main())
