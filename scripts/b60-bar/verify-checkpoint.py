#!/usr/bin/env python3
"""Verify the fresh archive and exact accepted files without exposing contents."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile

ARCHIVE=Path('/mnt/backups/dump/vzdump-lxc-110-2026_10_11-00_28_16.tar.zst')
EXPECTED={
 'etc/systemd/system/aster-llama.service':'6b09f4580ef49b1c61532d22f48cc5091ec95a0e823f73893db7a83f5c1a461e',
 'opt/llama.cpp-b11429/llama-server':'5faf410bbbc00a1b94b09ee01623699f255365628dfa73b1ee552d9e52a2231d',
 'usr/share/ollama/.ollama/models/blobs/sha256-cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13':'cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13',
}
def digest(f):
 h=hashlib.sha256()
 for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 assert ARCHIVE.is_file() and not ARCHIVE.is_symlink()
 subprocess.run(['zstd','-t','--quiet',str(ARCHIVE)],check=True,timeout=600,capture_output=True)
 with ARCHIVE.open('rb') as f:checksum=digest(f)
 process=subprocess.Popen(['zstd','-dc',str(ARCHIVE)],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 found={}
 try:
  with tarfile.open(fileobj=process.stdout,mode='r|') as tar:
   for member in tar:
    name=member.name.removeprefix('./')
    if name in EXPECTED:
     assert member.isfile(),'unexpected archive artifact type'
     found[name]=digest(tar.extractfile(member))
  assert process.wait(timeout=30)==0
 finally:
  if process.poll() is None:process.terminate();process.wait(timeout=30)
 assert found==EXPECTED,'accepted recovery files missing or different'
 proof={'archive':str(ARCHIVE),'bytes':ARCHIVE.stat().st_size,'sha256':checksum,
        'accepted_files_verified':found,'compressed_integrity_passed':True,
        'completed_at':datetime.now(timezone.utc).isoformat()}
 path=Path('/var/lib/b60-inference/evidence/sycl-prepromotion-checkpoint-20261011.json')
 with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as f:
  json.dump(proof,f,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
 print(json.dumps(proof,sort_keys=True))
if __name__=='__main__':main()
