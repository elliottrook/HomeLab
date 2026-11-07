"""Exact116 source-local gateway-env coverage; no file contents are emitted.
The accepted helpers are unchanged; only one additional exact path is allowed.
"""
import hashlib,os,sys
from pathlib import Path
BASE=Path('/usr/local/libexec/local-ai-lease/entry-checkpoint')
BOOKING='b60-exclusive-20261106-day-r4'
PINS={'lab_hours_guest_checkpoint.py': '76e8f228fcbcd302a67dbbfd8538a2f1e0dd2e39449b0e4745152c32aef9d76b', 'lab_hours_file_checkpoint.py': '5938e967448073ecce2afc733fb569a7bef113b9ddd2fb4385cf64ec7af783f7', 'lab_hours_unit_adapter.py': 'f4781de620e9c0c10bf01eab162eb2564d8baf1d4d84670117649d368325bcbd', 'lab_hours_prepare_entry_plan.py': '2cf80b75ca067c2d9bb2aad861c81261ed304177e24040dff8f33487c883778a'}
def require(v):
 if v is not True:raise RuntimeError('FIXED116_SCOPE_REFUSED')
def initialize():
 require(os.geteuid()==0)
 for n,sha in PINS.items():
  p=BASE/n;s=p.lstat();require(p.is_file() and not p.is_symlink() and s.st_uid==0 and s.st_nlink==1 and not s.st_mode&0o022 and hashlib.sha256(p.read_bytes()).hexdigest()==sha)
 sys.path.insert(0,str(BASE))
 import lab_hours_guest_checkpoint as gc
 import lab_hours_prepare_entry_plan as prepare
 old=gc.EXACT_CONFIG_FILES;require(old==prepare.EXACT_CONFIG_FILES)
 extra=Path('/etc/epub-narration/gateway.env')
 require(extra not in old)
 gc.EXACT_CONFIG_FILES=prepare.EXACT_CONFIG_FILES=old|{extra}
 return gc,prepare,old
def main():
 gc,prepare,old=initialize()
 try:
  a=sys.argv[1:];require(bool(a))
  if a[0]=='prepare':
   require(a==['prepare','--guest-id','116','--booking-id',BOOKING]);sys.argv=[str(BASE/'lab_hours_prepare_entry_plan.py'),*a[1:]];return prepare.main()
  require(a[0]=='checkpoint' and a[1] in {'capture','verify','restore'})
  x=a[1:];parent='/var/lib/local-ai-lab-entry/'+BOOKING
  expected=[x[0],'--guest-id','116','--plan',parent+'/plan.json','--checkpoint',parent+'/files','--receipt',parent+'/receipt.json','--deadline']
  require(len(x) in {11,12} and x[:10]==expected and x[10].isdigit())
  require(x[11:]==(['--effect-authorized'] if x[0] in {'capture','restore'} else []))
  sys.argv=[str(BASE/'lab_hours_guest_checkpoint.py'),*x];return gc.main()
 finally:gc.EXACT_CONFIG_FILES=prepare.EXACT_CONFIG_FILES=old
if __name__=='__main__':
 try:raise SystemExit(main())
 except Exception:print('{"state":"no_go","code":"FIXED116_SCOPE_REFUSED"}');raise SystemExit(1)
