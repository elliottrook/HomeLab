#!/usr/bin/env python3
"""After SYCL acceptance: private native runtime/model staging, no GPU load."""
import hashlib
import json
from pathlib import Path
import subprocess

SOURCE=Path('/var/lib/b60-inference/openvino-trial-20261011')
DISK='/opt/b60-openvino-trial-20261011'
RAM='/dev/shm/b60-openvino-runtime-20261011'
RAM_BLOBS={'openvino_vision_embeddings_merger_model.bin','openvino_text_embeddings_model.bin'}
def run(*args):return subprocess.check_output(args,text=True,timeout=300)
def guest(*args):return run('pct','exec','110','--',*args)
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 m=json.loads(guest('python3','-c','import json; print(json.dumps(json.load(open("/opt/aster-sycl-b11429/manifest.json"))))'))
 assert guest('sha256sum','/etc/systemd/system/aster-llama.service').split()[0]==m['unit_sha256']
 assert guest('systemctl','is-active','aster-llama.service').strip()=='active'
 assert json.loads(guest('curl','-fsS','--max-time','10','http://192.168.70.12:11435/health'))['status']=='ok'
 pub=json.loads((SOURCE/'publisher-manifest.json').read_text());dep=json.loads((SOURCE/'dependencies-manifest.json').read_text())
 assert pub['model_revision']=='ee5a3761d4524966dd6c1f1037694ebc581cb196'
 artifacts=[]
 for a in pub['artifacts']+dep['artifacts']:
  sub='wheels' if a['name'].endswith('.whl') else 'packages' if a['name'].endswith('.deb') else 'model'
  src=SOURCE/sub/a['name'];assert src.stat().st_size==a['bytes'] and sha(src)==a['sha256']
  dst=(RAM+'/model-parts/'+a['name']) if a['name'] in RAM_BLOBS else (DISK+'/model/'+a['name']) if sub=='model' else RAM+'/'+sub+'/'+a['name']
  artifacts.append({**a,'source':str(src),'destination':dst})
 disk_bytes=sum(a['bytes'] for a in artifacts if a['destination'].startswith(DISK))
 guest('python3','-c','import pathlib,shutil,sys; d=pathlib.Path(sys.argv[1]); r=pathlib.Path(sys.argv[2]); assert not d.exists() and not r.exists(); assert shutil.disk_usage("/").free-int(sys.argv[3])>=20*1024**3; m=dict(l.split(":",1) for l in open("/proc/meminfo")); assert int(m["MemAvailable"].split()[0])*1024>=6*1024**3; [(p.mkdir(parents=True,mode=0o755)) for p in [d/"model",r/"wheels",r/"packages",r/"model-parts",r/"site",r/"opencl",r/"consent"/"intel"]]; (r/"consent"/"intel"/"openvino_telemetry").write_text("0")',DISK,RAM,str(disk_bytes))
 for a in artifacts:
  run('pct','push','110',a['source'],a['destination'],'--perms','0644')
  assert guest('sha256sum',a['destination']).split()[0]==a['sha256']
 for name in sorted(RAM_BLOBS):
  guest('python3','-c','import pathlib,sys; p=pathlib.Path(sys.argv[1])/"model"/sys.argv[3]; assert not p.exists(); p.symlink_to(pathlib.Path(sys.argv[2])/"model-parts"/sys.argv[3])',DISK,RAM,name)
 # Publisher SHA-256 covers every wheel member. Reject paths/symlinks before extraction.
 guest('python3','-c','''import pathlib,zipfile,stat,sys
r=pathlib.Path(sys.argv[1]); dest=r/"site"
for w in sorted((r/"wheels").glob("*.whl")):
 with zipfile.ZipFile(w) as z:
  for i in z.infolist():
   p=pathlib.PurePosixPath(i.filename);assert not p.is_absolute() and ".." not in p.parts
   assert not stat.S_ISLNK(i.external_attr>>16)
  z.extractall(dest)
''',RAM)
 for a in artifacts:
  if a['name'].endswith('.deb'):guest('dpkg-deb','-x',a['destination'],RAM+'/opencl')
 guest('python3','-c','import pathlib,sys; r=pathlib.Path(sys.argv[1]); (r/"vendors").mkdir(); libs=list((r/"opencl").rglob("libigdrcl.so")); assert len(libs)==1; (r/"vendors"/"intel.icd").write_text(str(libs[0])+"\\n")',RAM)
 proof={'artifacts':[{k:v for k,v in a.items() if k!='source'} for a in artifacts],'model_revision':pub['model_revision'],'system_packages_changed':False,'global_driver_changed':False,'gpu_executed':False,'disk_model':DISK+'/model','ram_runtime':RAM,'ram_model_symlinks':sorted(RAM_BLOBS),'telemetry_consent':False,'recovery_unit_sha256':m['unit_sha256']}
 target=SOURCE/'guest-staging-proof.json'
 with target.open('x') as f:json.dump(proof,f,sort_keys=True);f.write('\n')
 print(json.dumps({'proof':str(target),'sha256':sha(target),'artifacts':len(artifacts),'gpu_executed':False,'disk_bytes':disk_bytes}))
if __name__=='__main__':main()
