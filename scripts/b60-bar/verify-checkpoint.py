#!/usr/bin/env python3
"""Verify the fresh archive and exact accepted files without exposing contents."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import threading

ARCHIVE=Path('/mnt/backups/dump/vzdump-lxc-110-2026_10_11-00_28_16.tar.zst')
PROOF=Path('/var/lib/b60-inference/evidence/sycl-prepromotion-checkpoint-20261011.json')
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
 # One sequential read proves compressed digest, frame integrity and selected
 # tar content together. Do not scan the 38 GB archive three separate times.
 checksum=hashlib.sha256();errors=[]
 process=subprocess.Popen(['zstd','-dc'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 def feed():
  try:
   with ARCHIVE.open('rb') as source:
    for chunk in iter(lambda:source.read(4*1024*1024),b''):
     checksum.update(chunk);process.stdin.write(chunk)
   process.stdin.close()
  except BaseException as e:errors.append(type(e).__name__)
 thread=threading.Thread(target=feed,daemon=True);thread.start()
 found={}
 try:
  with tarfile.open(fileobj=process.stdout,mode='r|') as tar:
   for member in tar:
    name=member.name.removeprefix('./')
    if name in EXPECTED:
     assert member.isfile(),'unexpected archive artifact type'
     found[name]=digest(tar.extractfile(member))
  # Drain tar padding/trailing frames so decompression validates the whole file.
  while process.stdout.read(4*1024*1024):pass
  thread.join(timeout=30)
  assert not thread.is_alive() and not errors and process.wait(timeout=30)==0
 finally:
  if process.poll() is None:process.terminate();process.wait(timeout=30)
  process.stdout.close()
 assert found==EXPECTED,'accepted recovery files missing or different'
 proof={'archive':str(ARCHIVE),'bytes':ARCHIVE.stat().st_size,'sha256':checksum.hexdigest(),
        'accepted_files_verified':found,'compressed_integrity_passed':True,
        'completed_at':datetime.now(timezone.utc).isoformat()}
 path=PROOF
 with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as f:
  json.dump(proof,f,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
 print(json.dumps(proof,sort_keys=True))
if __name__=='__main__':main()
