#!/usr/bin/env python3
"""Host-only approved native OpenVINO artifacts; no install/import/GPU load."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import urllib.request

ROOT=Path('/var/lib/b60-inference/openvino-trial-20261011')
REVISION='ee5a3761d4524966dd6c1f1037694ebc581cb196'
REPO='OpenVINO/Qwen3.5-9B-int4-ov'
PINNED={
 'openvino-genai':('2026.4.0.0','openvino_genai-2026.4.0.0-2635-cp313-cp313-manylinux_2_28_x86_64.whl','9e8e07bc7cd6992d42979bed4174939aeecf17aca8a2e804d50d8fea4c27fcf3'),
 'openvino':('2026.4.0','openvino-2026.4.0-22959-cp313-cp313-manylinux_2_28_x86_64.whl','186abfe5f355c33f19b50fe48340f9af0110e92fd279b7358a023fcbd225c380'),
 'openvino-tokenizers':('2026.4.0.0','openvino_tokenizers-2026.4.0.0-py3-none-manylinux_2_28_x86_64.whl','3a44cbc3d5f0004f3d17e9facfc268955bdfb7c4a676646dc49a65d19e95227c'),
}

def metadata(url):
 with urllib.request.urlopen(url,timeout=60) as r:return json.load(r)
def checksum(path,git_blob=False):
 h=hashlib.sha1() if git_blob else hashlib.sha256()
 if git_blob:h.update(f'blob {path.stat().st_size}\0'.encode())
 with path.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def download(url,path,size,expected,git_blob=False):
 if not path.exists():
  with urllib.request.urlopen(url,timeout=90) as source,path.open('xb') as dest:
   total=0
   for chunk in iter(lambda:source.read(4*1024*1024),b''):
    total+=len(chunk);assert total<=size,'oversized publisher artifact';dest.write(chunk)
 assert path.stat().st_size==size and checksum(path,git_blob)==expected,'incomplete or changed artifact; no overwrite'
 return {'name':path.name,'bytes':size,'sha256':checksum(path),'url':url}
def main():
 assert shutil.disk_usage('/var/lib/b60-inference').free>=28*1024**3
 ROOT.mkdir(mode=0o700,exist_ok=True)
 model=ROOT/'model';model.mkdir(exist_ok=True)
 wheels=ROOT/'wheels';wheels.mkdir(exist_ok=True)
 data=metadata(f'https://huggingface.co/api/models/{REPO}/revision/{REVISION}?blobs=true')
 assert data['sha']==REVISION
 selected=[s for s in data['siblings'] if re.fullmatch(r'(?:openvino_[a-z_]+\.(?:xml|bin)|[a-z_]+\.json|chat_template\.jinja)',s['rfilename'])]
 assert len(selected)==24 and sum(s['size'] for s in selected)<=6280231708
 manifest={'model_revision':REVISION,'repo':REPO,'artifacts':[],'runtime_dependencies':{},'gpu_executed':False}
 for s in selected:
  name=s['rfilename'];print('Download model',name,flush=True)
  lfs=s.get('lfs');expected=lfs['sha256'] if lfs else s['blobId']
  manifest['artifacts'].append(download(f'https://huggingface.co/{REPO}/resolve/{REVISION}/{name}',model/name,s['size'],expected,not bool(lfs)))
 for package,(version,name,expected) in PINNED.items():
  info=metadata(f'https://pypi.org/pypi/{package}/{version}/json')
  asset=next(a for a in info['urls'] if a['filename']==name)
  assert asset['digests']['sha256']==expected
  print('Download runtime',name,flush=True)
  manifest['artifacts'].append(download(asset['url'],wheels/name,asset['size'],expected))
  manifest['runtime_dependencies'][package]=info['info']['requires_dist']
 proof=ROOT/'publisher-manifest.json'
 if proof.exists():assert json.loads(proof.read_text())==manifest
 else:
  with proof.open('x') as f:json.dump(manifest,f,sort_keys=True);f.write('\n')
 print(json.dumps({'root':str(ROOT),'model_revision':REVISION,'verified_artifacts':len(manifest['artifacts']),
                   'bytes':sum(a['bytes'] for a in manifest['artifacts']),
                   'manifest_sha256':checksum(proof),'runtime_dependencies':manifest['runtime_dependencies'],
                   'installed':False,'gpu_executed':False}),flush=True)
if __name__=='__main__':main()
