"""Build deterministic no-execution SA3 runner-activation bundle."""
from __future__ import annotations
import gzip,hashlib,io,json,os,tarfile
from pathlib import Path
REPO=Path(__file__).resolve().parents[2];NAME="aster-sa3-runner-activation-v2.tar.gz";BUNDLE_SHA256="5f4a50d4cbae3021775756b3754ec7226047775df9e5e02cccc106fb30b0fc12"
FILES=("scripts/local-ai/sa3_runner_activation_install.py","scripts/local-ai/full_inference_lab_runtime.py","scripts/local-ai/lab_hours_reserved_runner.py","scripts/local-ai/lab_hours_release_manifest.json")
def build(out):
 out=Path(out)
 if out.exists():
  s=out.lstat()
  if not out.is_dir() or out.is_symlink() or s.st_mode&0o777!=0o700:raise ValueError("OUTPUT_INVALID")
 else:out.mkdir(mode=0o700)
 rows=[];values={}
 for n in FILES:
  p=REPO/n
  if not p.is_file() or p.is_symlink():raise ValueError("SOURCE_INVALID:"+n)
  d=p.read_bytes();values[n]=d;rows.append({"path":n,"sha256":hashlib.sha256(d).hexdigest(),"mode":"0644"})
 values["bundle-manifest.json"]=(json.dumps({"schema":"aster-sa3-runner-activation-bundle.v1","files":rows},sort_keys=True,separators=(",",":"))+"\n").encode();buf=io.BytesIO()
 with gzip.GzipFile(fileobj=buf,mode="wb",mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode="w") as tf:
   for n in sorted(values):
    d=values[n];i=tarfile.TarInfo(n);i.size=len(d);i.mode=0o600 if n=="bundle-manifest.json" else 0o644;i.uid=i.gid=i.mtime=0;i.uname=i.gname="root";tf.addfile(i,io.BytesIO(d))
 d=buf.getvalue();h=hashlib.sha256(d).hexdigest()
 if BUNDLE_SHA256 and h!=BUNDLE_SHA256:raise ValueError("BUNDLE_HASH_INVALID:"+h)
 p=out/NAME;fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
 try:os.write(fd,d);os.fsync(fd)
 finally:os.close(fd)
 return {"archive":str(p),"archive_sha256":h,"files":len(FILES),"effects":"not-attempted"}
def main(argv=None):
 import argparse
 p=argparse.ArgumentParser();p.add_argument("--output-dir",type=Path,required=True);a=p.parse_args(argv)
 try:print(json.dumps(build(a.output_dir),sort_keys=True));return 0
 except (OSError,ValueError) as exc:print(json.dumps({"state":"no_go","code":str(exc)},sort_keys=True));return 1
if __name__=="__main__":raise SystemExit(main())
