#!/usr/bin/env python3
"""Extract official, digest-verified runtime packages without system installation."""
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path

base = Path('/opt/b60-level-zero-trial-20261010')
base.mkdir(mode=0o755, exist_ok=True)
packages = base / 'packages'
packages.mkdir(exist_ok=True)
root = base / 'root'
root.mkdir(exist_ok=True)
specs = [
 ('https://github.com/intel/compute-runtime/releases/download/26.35.39758.10/', 'libze-intel-gpu1_26.35.39758.10-0_amd64.deb', 'c19a641b953d55aebbf1d51bec364a84bf629f985e02fbbe6dc70224c0e88470'),
 ('https://github.com/intel/compute-runtime/releases/download/26.35.39758.10/', 'libigdgmm12_22.10.0_amd64.deb', '6031a63d6e8a12ce61c14efc15f2c8e727061286e3820b8594e6d00615e04d54'),
 ('https://github.com/intel/intel-graphics-compiler/releases/download/v2.41.5/', 'intel-igc-core-2_2.41.5+22716_amd64.deb', '0a6e64a663ae65a0fa02d6912ae3b6b37cf85b90c21cc423fd9fef70aaf4f628'),
 ('https://github.com/intel/intel-graphics-compiler/releases/download/v2.41.5/', 'intel-igc-opencl-2_2.41.5+22716_amd64.deb', '779e1b9e88098eb25711e9a8f67c2752665bad22f134aa40ed5649f6e1b87058'),
 ('https://deb.debian.org/debian/pool/main/l/level-zero/', 'libze1_1.20.6-1_amd64.deb', 'a901ee6a081bfd1037b6e91fa46bb1f3e37dfd6503946032fb6866956106feb7'),
 ('https://deb.debian.org/debian/pool/main/l/level-zero/', 'libze-dev_1.20.6-1_amd64.deb', '7119f3a3a8ca46ce7891515188e61f5e694af154699a016569f2bd12ab725255'),
]
manifest = []
for urlbase, name, expected in specs:
    url = urlbase + name.replace('+', '%2B')
    path = packages / name
    print('Downloading', path.name, flush=True)
    if not path.exists():
        with urllib.request.urlopen(url, timeout=60) as src, path.open('xb') as dst:
            while chunk := src.read(1024 * 1024):
                dst.write(chunk)
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    assert expected == actual
    depends = subprocess.check_output(['dpkg-deb', '-f', str(path), 'Depends'], text=True).strip()
    print(path.name, actual, 'Depends:', depends, flush=True)
    subprocess.run(['dpkg-deb', '-x', str(path), str(root)], check=True)
    manifest.append({'url': url, 'sha256': actual, 'depends': depends})
(base / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Staged', str(base), 'without dpkg installation or global linker changes.')
