"""Generated synthetic bootstrap canary; no external inputs."""
import base64,hashlib,json,pathlib
RUN_ID = 'bootstrap-canary-002'
MANIFEST = '56da5b4614220bfc8e51e5b625e8b6bdd87ba30177696a89df6dc66b45fc7f56'
PREFIX = b'ASTER_S0_V1'
CHUNK = 3072
value = {'authorization':'not-granted','corpus_evaluated':False,
         'fixture':True,'interfaces':sorted(p.name for p in pathlib.Path('/sys/class/net').iterdir()),
         'result':'bootstrap-canary'}
raw = json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
if len(raw) > 2*1024*1024: raise SystemExit('result-size')
digest = hashlib.sha256(raw).hexdigest()
parts = [raw[i:i+CHUNK] for i in range(0,len(raw),CHUNK)]
lines = [b' '.join((PREFIX,b'BEGIN',RUN_ID.encode(),MANIFEST.encode(),str(len(raw)).encode(),digest.encode(),str(len(parts)).encode()))]
for sequence,part in enumerate(parts):
    lines.append(b' '.join((PREFIX,b'CHUNK',RUN_ID.encode(),str(sequence).encode(),base64.b64encode(part))))
lines.append(b' '.join((PREFIX,b'END',RUN_ID.encode(),str(len(raw)).encode(),digest.encode())))
out = pathlib.Path('/var/lib/aster-s0/output')
(out/'result.json').write_bytes(raw)
(out/'protocol.txt').write_bytes(b'\n'.join(lines)+b'\n')
