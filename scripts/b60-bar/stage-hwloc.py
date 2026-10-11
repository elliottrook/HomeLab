#!/usr/bin/env python3
"""Supply missing private SYCL-adapter dependency; no package installation."""
import hashlib
import subprocess
import urllib.request
from pathlib import Path

base=Path('/dev/shm/b60-oneapi-trial-20261010')
package=base/'packages/libhwloc15_2.12.0-4_amd64.deb'
url='https://deb.debian.org/debian/pool/main/h/hwloc/'+package.name
with urllib.request.urlopen(url,timeout=60) as src, package.open('xb') as dst:
    dst.write(src.read())
assert hashlib.sha256(package.read_bytes()).hexdigest()=='aa53c4a1878475e7309f2c265c54d9a8a4602dec95564cf84d471d7376ff616c'
subprocess.run(['dpkg-deb','-x',str(package),str(base/'root')],check=True)
print('Private hwloc library extracted and checksum verified.')
