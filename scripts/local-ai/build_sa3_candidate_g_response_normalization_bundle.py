"""Build deterministic candidate-g response-normalization inactive bundle."""
from __future__ import annotations
import gzip, hashlib, io, json, os, subprocess, tarfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STREAM_COMMIT = "56d4d2272cad0cdbd0e5b3fbbc71f35690a4fbbb"
BUNDLE_NAME = "sa3-candidate-g-response-normalization-r1.tar.gz"
PLATFORM_FILES = tuple("scripts/local-ai/" + name for name in (
    "lab_hours_workloads.py", "lab_hours_release_manifest.json",
    "aster_llama_sa3_evidence_envelope_wrapper.py",
    "sa3_evidence_envelope_inactive_install.py",
    "sa3_candidate_g_diagnostic_inactive_install.py",
    "sa3_candidate_g_response_normalization_inactive_install.py",
))
STREAM_FILE = "services/aster-agent/evals/sa3_evidence_envelope_runner_v1.py"

def build(output_dir: Path) -> dict[str, object]:
    output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=False,mode=0o700)
    selected={p:(REPO/p).read_bytes() for p in PLATFORM_FILES}
    selected[STREAM_FILE]=subprocess.check_output(("git","show",f"{STREAM_COMMIT}:{STREAM_FILE}"),cwd=REPO)
    manifest={"schema":"aster-sa3-candidate-g-response-normalization-bundle.v1",
      "platform_commit":subprocess.check_output(("git","rev-parse","HEAD"),cwd=REPO,text=True).strip(),
      "stream_commit":STREAM_COMMIT,
      "files":[{"path":p,"sha256":hashlib.sha256(d).hexdigest()} for p,d in sorted(selected.items())]}
    selected["bundle-manifest.json"]=(json.dumps(manifest,sort_keys=True,separators=(",",":"))+"\n").encode()
    output=io.BytesIO()
    with gzip.GzipFile(fileobj=output,mode="wb",mtime=0) as compressed:
      with tarfile.open(fileobj=compressed,mode="w") as archive:
       for p,d in sorted(selected.items()):
        info=tarfile.TarInfo(p); info.size=len(d); info.mode=0o600
        info.uid=info.gid=0; info.uname=info.gname="root"; info.mtime=0
        archive.addfile(info,io.BytesIO(d))
    target=output_dir/BUNDLE_NAME
    fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
    try: os.write(fd,output.getvalue()); os.fsync(fd)
    finally: os.close(fd)
    return {"archive":str(target),"sha256":hashlib.sha256(output.getvalue()).hexdigest(),"files":len(selected),"effects":"not-attempted"}

if __name__=="__main__":
 import argparse
 p=argparse.ArgumentParser(); p.add_argument("--output-dir",type=Path,required=True)
 print(json.dumps(build(p.parse_args().output_dir),sort_keys=True))
