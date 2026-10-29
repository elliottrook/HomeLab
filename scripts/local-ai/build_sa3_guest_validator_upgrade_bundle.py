"""Build the deterministic SA3 guest-validator correction bundle."""

from __future__ import annotations
import gzip,hashlib,io,json,os,shutil,tarfile
from pathlib import Path

REPO=Path(__file__).resolve().parents[2]
NAME="aster-sa3-guest-validator-v1.tar.gz"
BUNDLE_SHA256="cc4673fb5cb8841f935b9e31978bc194f2f84f250bf082ff9f657e63332a4f3e"
FILES=("scripts/local-ai/sa3_guest_validator_upgrade.py",
       "scripts/local-ai/lab_hours_inactive_target.py",
       "scripts/local-ai/lab_hours_release_manifest.json")

def build(output_dir: Path) -> dict[str,object]:
    output_dir=Path(output_dir)
    if output_dir.exists():
        s=output_dir.lstat()
        if not output_dir.is_dir() or output_dir.is_symlink() or s.st_mode & 0o777 != 0o700: raise ValueError("OUTPUT_INVALID")
    else: output_dir.mkdir(mode=0o700)
    rows=[]; payload={}
    for name in FILES:
        p=REPO/name
        if not p.is_file() or p.is_symlink(): raise ValueError("SOURCE_INVALID:"+name)
        data=p.read_bytes(); payload[name]=data; rows.append({"path":name,"sha256":hashlib.sha256(data).hexdigest(),"mode":"0644"})
    payload["bundle-manifest.json"]=(json.dumps({"schema":"aster-sa3-guest-validator-bundle.v1","files":rows},sort_keys=True,separators=(",",":"))+"\n").encode()
    out=io.BytesIO()
    with gzip.GzipFile(fileobj=out,mode="wb",mtime=0) as gz:
        with tarfile.open(fileobj=gz,mode="w") as tf:
            for name in sorted(payload):
                data=payload[name]; info=tarfile.TarInfo(name); info.size=len(data); info.mode=0o600 if name=="bundle-manifest.json" else 0o644
                info.uid=0;info.gid=0;info.uname="root";info.gname="root";info.mtime=0;tf.addfile(info,io.BytesIO(data))
    data=out.getvalue(); digest=hashlib.sha256(data).hexdigest()
    if BUNDLE_SHA256 and digest != BUNDLE_SHA256: raise ValueError("BUNDLE_HASH_INVALID:"+digest)
    p=output_dir/NAME; fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
    try: os.write(fd,data);os.fsync(fd)
    finally: os.close(fd)
    return {"archive":str(p),"archive_sha256":digest,"files":len(FILES),"effects":"not-attempted"}

def main(argv=None):
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--output-dir",type=Path,required=True);a=p.parse_args(argv)
    try: print(json.dumps(build(a.output_dir),sort_keys=True));return 0
    except (OSError,ValueError) as exc: print(json.dumps({"state":"no_go","code":str(exc)},sort_keys=True));return 1
if __name__=="__main__": raise SystemExit(main())
