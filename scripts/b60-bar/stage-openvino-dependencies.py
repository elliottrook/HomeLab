#!/usr/bin/env python3
"""Download pinned native trial dependencies only; never install or load GPU."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT=Path('/var/lib/b60-inference/openvino-trial-20261011')
SPECS=[
 ('numpy','2.4.4','numpy-2.4.4-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl','c901b15172510173f5cb310eae652908340f8dede90fff9e3bf6c0d8dfd92f83'),
 ('openvino-telemetry','2025.2.0','openvino_telemetry-2025.2.0-py3-none-any.whl','bcb667e83a44f202ecf4cfa49281715c6d7e21499daec04ff853b7f964833599'),
]
DEBS=[
 ('https://github.com/intel/compute-runtime/releases/download/26.35.39758.10/intel-opencl-icd_26.35.39758.10-0_amd64.deb','61712caaddeba3d38e4f79e2a0fb23fea25596ca2d72c3144c6eea2331ec4301'),
 ('https://deb.debian.org/debian/pool/main/o/ocl-icd/ocl-icd-libopencl1_2.3.3-1_amd64.deb','99dfd409ae92505ee56742feea4e82a1e052818c5b0036ee618a371b5e28c9d1'),
]
def fetch(url,path,sha,size=None):
 if not path.exists():
  with urllib.request.urlopen(url,timeout=90) as src,path.open('xb') as dst:
   total=0
   for chunk in iter(lambda:src.read(1024*1024),b''):
    total+=len(chunk);assert total<=128*1024**2;dst.write(chunk)
 assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
 assert size is None or path.stat().st_size==size
 return {'name':path.name,'url':url,'sha256':sha,'bytes':path.stat().st_size}
def main():
 assert (ROOT/'publisher-manifest.json').is_file()
 out=[]
 for package,version,name,sha in SPECS:
  with urllib.request.urlopen(f'https://pypi.org/pypi/{package}/{version}/json',timeout=60) as r:d=json.load(r)
  a=next(a for a in d['urls'] if a['filename']==name)
  assert a['digests']['sha256']==sha and not d['info']['requires_dist']
  out.append(fetch(a['url'],ROOT/'wheels'/name,sha,a['size']))
 packages=ROOT/'packages';packages.mkdir(exist_ok=True)
 for url,sha in DEBS:out.append(fetch(url,packages/url.rsplit('/',1)[1],sha))
 proof={'artifacts':out,'installed':False,'gpu_executed':False}
 path=ROOT/'dependencies-manifest.json'
 if path.exists():assert json.loads(path.read_text())==proof
 else:
  with path.open('x') as f:json.dump(proof,f,sort_keys=True);f.write('\n')
 print(json.dumps(proof,sort_keys=True))
if __name__=='__main__':main()
