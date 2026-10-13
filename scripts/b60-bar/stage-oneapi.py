#!/usr/bin/env python3
"""Hash-check and extract Intel oneAPI user-space libraries into disposable tmpfs."""
import gzip
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path

base=Path('/dev/shm/b60-oneapi-trial-20261010')
base.mkdir(exist_ok=False)
packages=base/'packages'
packages.mkdir()
root=base/'root'
root.mkdir()
url='https://apt.repos.intel.com/oneapi/'
with urllib.request.urlopen(url+'dists/all/main/binary-amd64/Packages.gz',timeout=60) as f:
    index=gzip.decompress(f.read()).decode()
entries={}
for block in index.split('\n\n'):
    d={line.split(': ',1)[0]:line.split(': ',1)[1] for line in block.splitlines() if ': ' in line and not line.startswith(' ')}
    if 'Package' in d:
        entries.setdefault(d['Package'],[]).append(d)
names=['intel-oneapi-compiler-dpcpp-cpp-runtime-2026.1',
       'intel-oneapi-compiler-shared-runtime-2026.1',
       'intel-oneapi-openmp-2026.1','intel-oneapi-tbb-2023.1',
       'intel-oneapi-umf-1.1','intel-oneapi-dnnl-2026.0',
       'intel-oneapi-mkl-core-2026.1','intel-oneapi-mkl-sycl-blas-2026.1']
chosen=[entries[n][-1] for n in names]
installed=sum(int(d['Installed-Size'])*1024 for d in chosen)
download=sum(int(d['Size']) for d in chosen)
assert installed+download < 4*1024**3, 'staging exceeds memory budget'
print('Budget:',installed,'extracted bytes;',download,'download bytes',flush=True)
manifest=[]
for d in chosen:
    name=d['Filename'].split('/')[-1]
    path=packages/name
    print('Download',d['Package'],d['Version'],flush=True)
    with urllib.request.urlopen(url+d['Filename'].lstrip('./'),timeout=90) as src,path.open('xb') as dst:
        while chunk:=src.read(1024*1024): dst.write(chunk)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==d['SHA256']
    subprocess.run(['dpkg-deb','-x',str(path),str(root)],check=True)
    manifest.append({k:d[k] for k in ('Package','Version','SHA256','Filename','Size','Installed-Size')})
(base/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Extracted privately. No system packages or linker configuration changed.')
