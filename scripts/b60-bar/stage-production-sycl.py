#!/usr/bin/env python3
"""LXC 110 only: persist verified private runtime and prepare an atomic unit.

No GPU execution, package/global linker change or credential disclosure.
Activation is a separate host-controlled operation with independent rollback.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat

BASE = Path('/opt/aster-sycl-b11429')
UNIT = Path('/etc/systemd/system/aster-llama.service')
ROLLBACK = Path('/etc/systemd/system/aster-llama.service.pre-sycl-20261011')
OLD_UNIT_SHA = '6b09f4580ef49b1c61532d22f48cc5091ec95a0e823f73893db7a83f5c1a461e'
SERVER_SHA = '0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5'
BACKEND_SHA = '58757946256db139bab7ddab56dbe6e8d5503bb41518eb25bfc734c175c68591'
TREES = {
    'llama-sycl-fp16': Path('/dev/shm/b60-sycl-assets-20261010/llama-sycl-fp16'),
    'driver': Path('/dev/shm/b60-driver-assets-20261010/root'),
    'loader': Path('/dev/shm/b60-loader-1331-trial-20261010/root'),
    'oneapi': Path('/dev/shm/b60-oneapi-trial-20261010/root'),
}
READINESS = '''#!/usr/bin/env python3
import json,time,urllib.request
deadline=time.monotonic()+300
while time.monotonic()<deadline:
    try:
        with urllib.request.urlopen('http://192.168.70.12:11435/health',timeout=3) as r:
            if json.load(r).get('status')=='ok':
                print('Aster inference ready'); raise SystemExit(0)
    except (OSError,ValueError): pass
    time.sleep(2)
raise SystemExit('Aster inference readiness deadline; no automatic retry')
'''

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def tree_manifest(root):
    result={}
    for p in sorted(root.rglob('*')):
        mode=p.lstat().st_mode
        rel=str(p.relative_to(root))
        if stat.S_ISLNK(mode):
            target=os.readlink(p)
            assert not os.path.isabs(target), 'absolute runtime link'
            assert (p.parent/target).resolve().is_relative_to(root.resolve()), 'escaping runtime link'
            result[rel]={'link':target,'mode':stat.S_IMODE(mode)}
        elif stat.S_ISREG(mode):
            result[rel]={'sha256':digest(p),'bytes':p.stat().st_size,'mode':stat.S_IMODE(mode)}
        elif stat.S_ISDIR(mode):
            result[rel]={'directory':True,'mode':stat.S_IMODE(mode)}
        else: raise ValueError('special runtime file')
    return result

def candidate_unit(old,base,libs):
    assert hashlib.sha256(old.encode()).hexdigest()==OLD_UNIT_SHA, 'accepted unit drift'
    assert old.count('ExecStart=')==1 and old.count('ExecStartPost=')==1
    old=old.replace('Description=Aster llama.cpp Vulkan Inference','Description=Aster llama.cpp SYCL FP16 Inference')
    old=old.replace('/opt/llama.cpp-b11429/llama-server',str(base/'llama-sycl-fp16/llama-b11429/llama-server'),1)
    old=old.replace(' --metrics\n',' --metrics --log-verbosity 4\n',1)
    old=old.replace('ExecStartPost=/usr/local/libexec/aster-llama-warmup',f'ExecStartPost=/usr/bin/python3 {base}/wait-ready.py')
    # Fail closed rather than repeatedly executing a failed GPU initialization.
    old=old.replace('Restart=on-failure','Restart=no')
    old=old.replace('TimeoutStartSec=5min','TimeoutStartSec=330s')
    env=f'Environment="LD_LIBRARY_PATH={libs}"\nEnvironment=ONEAPI_DEVICE_SELECTOR=level_zero:gpu\nEnvironment=GGML_SYCL_ENABLE_FUSION=1\n'
    old=old.replace('[Service]\n','[Service]\n'+env,1)
    assert ' --metrics --log-verbosity 4\n' in old
    return old

def write_once(path,raw,mode=0o600):
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,mode),'wb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    assert args.execute and os.geteuid()==0
    assert digest(UNIT)==OLD_UNIT_SHA
    assert not BASE.exists() and not ROLLBACK.exists(), 'already staged or unexpected partial state'
    # Names only are examined; no environment value is emitted or copied.
    keys={l.split('=',1)[0].strip() for l in Path('/etc/aster-llama.env').read_text().splitlines() if '=' in l and not l.startswith('#')}
    assert not keys & {'LD_LIBRARY_PATH','ONEAPI_DEVICE_SELECTOR','GGML_SYCL_ENABLE_FUSION'}
    for p in TREES.values(): assert p.is_dir()
    assert digest(TREES['llama-sycl-fp16']/'llama-b11429/llama-server')==SERVER_SHA
    assert digest(TREES['llama-sycl-fp16']/'llama-b11429/libggml-sycl.so.0.26.0')==BACKEND_SHA
    assert digest(TREES['loader']/'usr/lib/x86_64-linux-gnu/libze_loader.so.1.33.1')=='a4859c17183add6412c48d44d0f356f8ef5d7b43ae35ed253074f670a6879d23'
    manifests={name:tree_manifest(p) for name,p in TREES.items()}
    size=sum(v.get('bytes',0) for m in manifests.values() for v in m.values())
    assert shutil.disk_usage('/').free-size>=20*1024**3, 'post-copy disk floor'
    scratch=BASE.with_name(BASE.name+'.staging')
    assert not scratch.exists()
    scratch.mkdir(mode=0o755)
    for name,p in TREES.items():
        shutil.copytree(p,scratch/name,symlinks=True)
        assert tree_manifest(scratch/name)==manifests[name], 'copy hash/link/mode mismatch'
        for item in (scratch/name).rglob('*'):
            if not item.is_symlink(): os.chown(item,0,0)
    os.rename(scratch,BASE)
    libdirs=sorted({str(p.parent) for p in (BASE/'oneapi').rglob('*.so*') if p.is_file()})
    libs=':'.join([str(BASE/'loader/usr/lib/x86_64-linux-gnu'),str(BASE/'driver/usr/local/lib'),str(BASE/'driver/usr/lib/x86_64-linux-gnu'),*libdirs])
    old=UNIT.read_bytes()
    write_once(ROLLBACK,old,0o644)
    write_once(BASE/'wait-ready.py',READINESS.encode(),0o755)
    new=candidate_unit(old.decode(),BASE,libs).encode()
    write_once(BASE/'aster-llama.service',new,0o644)
    manifest={'schema':1,'server_sha256':SERVER_SHA,'backend_sha256':BACKEND_SHA,
              'unit_sha256':hashlib.sha256(new).hexdigest(),'rollback_unit_sha256':OLD_UNIT_SHA,
              'runtime_bytes':size,'trees':manifests,'library_path':libs,
              'volatile_dependencies':False,'automatic_gpu_retry':False}
    raw=(json.dumps(manifest,sort_keys=True)+'\n').encode()
    write_once(BASE/'manifest.json',raw)
    print(json.dumps({k:v for k,v in manifest.items() if k!='trees'}))

if __name__=='__main__': main()
