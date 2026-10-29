"""Atomic activation of the fixed SA3 reserved-runner transaction."""
from __future__ import annotations
import base64,hashlib,json,os,stat,subprocess,sys
from pathlib import Path

TARGET=Path("/usr/local/libexec/local-ai-lease/full-inference-pilot")
CHECKPOINT=Path("/var/lib/local-ai-lab/checkpoints/sa3-runner-activation-v2")
RESERVATIONS=Path("/var/lib/local-ai-lab/reservations")
FILES={
 "full_inference_lab_runtime.py":("5fa48df16c4db8d2eedcd4a8ab9d615cc07519b713a0028c20019d84ae06ac3d","3026a792bcc1375b98d537680f4f2ff2ee00aeb0e8590498337f8e680d6d8279",0o755),
 "lab_hours_reserved_runner.py":("79b3fb92ced17712f7f5dd8bd40517fbec27ef2b2494c47454fb8fdcd44bf27e","8d222d538e3ffc201cb0a7a29e06a69bf808fe3b6ba7d5c9283a5e26170402bb",0o755),
 "lab_hours_release_manifest.json":("51a9cd3a450710ad755cf924aef0df6e900edcf6cca2db4cffe054cb2437f74c","7c28fb4a6eb439b7a9fbdc79b48298b5740fae07ee26fc7b963adcb4a0aa67b9",0o644),
}
class ActivationError(RuntimeError): pass
def sha(data): return hashlib.sha256(data).hexdigest()
def regular(path,expected,mode,uid):
 s=path.lstat();data=path.read_bytes()
 if (not stat.S_ISREG(s.st_mode) or s.st_uid!=uid or s.st_nlink!=1
     or (mode is not None and stat.S_IMODE(s.st_mode)!=mode)
     or sha(data)!=expected): raise ActivationError("FILE_INVALID:"+path.name)
 return data
def atomic(path,data,mode,uid):
 tmp=path.parent/("."+path.name+".sa3-activation-"+str(os.getpid()));fd=os.open(tmp,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
 try:
  os.write(fd,data);os.fchmod(fd,mode)
  if uid==0:os.fchown(fd,0,0)
  os.fsync(fd)
 finally:os.close(fd)
 os.replace(tmp,path)
def require_no_sa3_booking(root):
 if not root.exists(): return
 for path in root.glob("*.json"):
  value=json.loads(path.read_text())
  if value.get("workload")=="sa3-expanded-source-quality-v1" and value.get("state") in {"reserved","claimed","running"}: raise ActivationError("ACTIVE_SA3_BOOKING_PRESENT")
def install(source_root,*,target=TARGET,checkpoint=CHECKPOINT,reservations=RESERVATIONS,uid=0,run=subprocess.run):
 if os.path.lexists(checkpoint):raise ActivationError("CHECKPOINT_EXISTS")
 require_no_sa3_booking(reservations);old={};new={}
 for name,(before,after,mode) in FILES.items():
  old[name]=regular(target/name,before,mode,uid);new[name]=regular(source_root/"scripts/local-ai"/name,after,None,uid)
 checkpoint.mkdir(parents=True,mode=0o700);os.chmod(checkpoint,0o700)
 if uid==0:os.chown(checkpoint,0,0)
 for name,data in old.items():atomic(checkpoint/(hashlib.sha256(name.encode()).hexdigest()+".json"),(json.dumps({"name":name,"data":base64.b64encode(data).decode()},sort_keys=True)+"\n").encode(),0o600,uid)
 try:
  for name,(_,_,mode) in FILES.items():atomic(target/name,new[name],mode,uid)
  env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONPATH"]=str(target)
  result=run((sys.executable,"-B","-c","import full_inference_lab_runtime,lab_hours_reserved_runner; from lab_hours_reserved_runner import load_manifest; load_manifest()"),env=env,capture_output=True,text=True,timeout=30,check=False)
  if result.returncode!=0:raise ActivationError("IMPORT_OR_MANIFEST_FAILED:"+result.stderr[-240:])
  return {"state":"installed-inactive","files":3,"sa3_runner":"available","effects":"not-attempted","checkpoint":"retained"}
 except BaseException:
  for name,(_,_,mode) in reversed(tuple(FILES.items())):
   rec=json.loads((checkpoint/(hashlib.sha256(name.encode()).hexdigest()+".json")).read_text());atomic(target/name,base64.b64decode(rec["data"]),mode,uid)
  raise
def main(argv=None):
 import argparse
 p=argparse.ArgumentParser();p.add_argument("--source-root",type=Path,required=True);p.add_argument("--apply",action="store_true");a=p.parse_args(argv)
 if not a.apply:print(json.dumps({"state":"source-only","reason":"--apply required"},sort_keys=True));return 2
 try:
  if os.geteuid()!=0:raise ActivationError("ROOT_REQUIRED")
  print(json.dumps(install(a.source_root),sort_keys=True));return 0
 except (ActivationError,OSError,ValueError,subprocess.SubprocessError) as exc:print(json.dumps({"state":"no_go","code":str(exc)},sort_keys=True));return 1
if __name__=="__main__":raise SystemExit(main())
