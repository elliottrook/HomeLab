"""Generated exact S0 corpus entry point; no external inputs."""
import base64,hashlib,json,os,pathlib,platform,sys
RUN_ID='corpus-descriptive-002'
PAYLOAD_SHA256='dc2a9274ae01c6c56c2216f6ae151f96eecd748103e57dce5638d661879165c0'
FILES={'s0_descriptive.py': '77d6e6a1604c0b32edac531663c6dfa2180add4288f5814568be01f0e6060fd3', 's0_vm_corpus_worker.py': '7d2c4091900019ea4249e8f8ebc2ff37813979cbea6c3235e9792b87ad112666', 'routing_smoke.py': '3e52c69f25dcf22100c521aeaa5b68b83e334ddf8ce9469d14d79822c8aa5864', 'validate_label_batch.py': '2d7ec8286b80dad0b6322f1ed2dc76f4ec372a88e6bfcbd796f752061eba614c', 'batch-1/reviewed-proposal.json': '64459d47a6a48bb7e67f6aad766a623ba4fae2f6c0bad0c309f55c880c7e7288', 'batch-1/acceptance.json': '5e5c498bea895e50a1279b2e89c128b92ac7e7fa3b0e42ed250ec8be45a71437', 'batch-1/effort.json': '2c8e795f2f3b2d76639269d0df7f876c949a832844044b8d2669480f04cf4d8d', 'batch-2/reviewed-proposal.json': '0731464ba0d7ea3db596f48d920a7f8492004c34c45600f0efcc15c9aaec5308', 'batch-2/acceptance.json': '9524eb1e737f553c71db782efafa2a8fde4c6a233bc39ac7e7a765ae75295520', 'batch-2/effort.json': '1401158fb3e63fed350aafff2056090f544f9543e3ae9d51439e408d53da6ef4', 'batch-3/reviewed-proposal.json': '962bf5f1c2adaefe4dbbedc92116640019b77c7e4580bc2c2d6b3462750f7a95', 'batch-3/acceptance.json': 'd165a0bb2927674fe742628d36e8b843acc4b381b328da16af84035cab48a268', 'batch-3/effort.json': 'b2f62ea4843a5927f71f65d8594ef968798f80f8071e91a8b6e2c540e18e3f5c'}
CORPUS_MANIFEST={'batch-1/reviewed-proposal.json': '64459d47a6a48bb7e67f6aad766a623ba4fae2f6c0bad0c309f55c880c7e7288', 'batch-1/acceptance.json': '5e5c498bea895e50a1279b2e89c128b92ac7e7fa3b0e42ed250ec8be45a71437', 'batch-1/effort.json': '2c8e795f2f3b2d76639269d0df7f876c949a832844044b8d2669480f04cf4d8d', 'batch-2/reviewed-proposal.json': '0731464ba0d7ea3db596f48d920a7f8492004c34c45600f0efcc15c9aaec5308', 'batch-2/acceptance.json': '9524eb1e737f553c71db782efafa2a8fde4c6a233bc39ac7e7a765ae75295520', 'batch-2/effort.json': '1401158fb3e63fed350aafff2056090f544f9543e3ae9d51439e408d53da6ef4', 'batch-3/reviewed-proposal.json': '962bf5f1c2adaefe4dbbedc92116640019b77c7e4580bc2c2d6b3462750f7a95', 'batch-3/acceptance.json': 'd165a0bb2927674fe742628d36e8b843acc4b381b328da16af84035cab48a268', 'batch-3/effort.json': 'b2f62ea4843a5927f71f65d8594ef968798f80f8071e91a8b6e2c540e18e3f5c'}
PREFIX=b'ASTER_S0_V1'
CHUNK=3072
LIB=pathlib.Path('/usr/local/lib/aster-s0')
CORPUS=pathlib.Path('/usr/local/share/aster-s0/corpus')
for name,expected in FILES.items():
    path=(CORPUS/name) if name.startswith('batch-') else (LIB/name)
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:raise SystemExit('artifact-hash')
sys.path.insert(0,str(LIB))
import s0_descriptive as descriptive
import s0_vm_corpus_worker as worker
blobs={name:(CORPUS/name).read_bytes() for name in CORPUS_MANIFEST}
rows=descriptive.adapt(blobs,CORPUS_MANIFEST)
engine=worker.load_engine_source(LIB/'routing_smoke.py')
value=worker.compare_accepted(rows,engine)
value.update({
    'run_id':RUN_ID,
    'payload_manifest_sha256':PAYLOAD_SHA256,
    'dataset_manifest_sha256':hashlib.sha256(descriptive.canonical(CORPUS_MANIFEST)).hexdigest(),
    'development_family_ids':sorted(row['family_id'] for row in rows if row['labels']['split']=='dev'),
    'runtime':{'python':platform.python_version(),'system':platform.system(),'machine':platform.machine()},
})
raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
if not raw or len(raw)>2097152:raise SystemExit('result-size')
digest=hashlib.sha256(raw).hexdigest()
parts=[raw[i:i+CHUNK] for i in range(0,len(raw),CHUNK)]
lines=[b' '.join((PREFIX,b'BEGIN',RUN_ID.encode(),PAYLOAD_SHA256.encode(),str(len(raw)).encode(),digest.encode(),str(len(parts)).encode()))]
for sequence,part in enumerate(parts):
    lines.append(b' '.join((PREFIX,b'CHUNK',RUN_ID.encode(),str(sequence).encode(),base64.b64encode(part))))
lines.append(b' '.join((PREFIX,b'END',RUN_ID.encode(),str(len(raw)).encode(),digest.encode())))
out=pathlib.Path('/var/lib/aster-s0/output')
(out/'result.json').write_bytes(raw)
(out/'protocol.txt').write_bytes(b'\n'.join(lines)+b'\n')
