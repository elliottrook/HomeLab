"""Remove common channel bias while retaining mirrored lateral movement cues."""
import argparse,hashlib,io,json,math,wave
from pathlib import Path
from types import SimpleNamespace
try:
    from .canonical_sound_compat import promote
    from .tools.deploy_canonical_clicks import configure
except ImportError:
    from canonical_sound_compat import promote
    from tools.deploy_canonical_clicks import configure

def samples(data):
    with wave.open(io.BytesIO(data),'rb') as w:
        if w.getparams()[:3]!=(2,3,48000):raise ValueError('pinned-pcm24-required')
        n=w.getnframes();raw=w.readframes(n)
    return [int.from_bytes(raw[i:i+3],'little',signed=True) for i in range(0,len(raw),3)]
def ratio(s):return math.sqrt(sum(v*v for v in s[::2])/sum(v*v for v in s[1::2]))
def build(source,output):
    source,output=Path(source),Path(output)
    if output.exists():raise ValueError('immutable-balanced-output')
    config=SimpleNamespace(EXPECTED={});configure(config)
    originals={n:(source/n).read_bytes() for n in config.MASTER_EXPECTED}
    if any(hashlib.sha256(d).hexdigest()!=config.MASTER_EXPECTED[n] for n,d in originals.items()):raise ValueError('canonical-source-drift')
    gain=1/math.sqrt(ratio(samples(originals['nav-left.wav']))*ratio(samples(originals['nav-right.wav'])))
    if not .5<gain<1:raise ValueError('unexpected-bias-no-boost')
    for folder in ('original-masters','masters','resources'):(output/folder).mkdir(parents=True)
    rows=[]
    for name,original in originals.items():
        s=samples(original);balanced=[round(v*gain) if i%2==0 else v for i,v in enumerate(s)]
        raw=b''.join(v.to_bytes(3,'little',signed=True) for v in balanced)
        stream=io.BytesIO()
        with wave.open(stream,'wb') as w:w.setnchannels(2);w.setsampwidth(3);w.setframerate(48000);w.writeframes(raw)
        master=stream.getvalue();runtime=promote(master)
        for folder,data in (('original-masters',original),('masters',master),('resources',runtime)):(output/folder/name).write_bytes(data)
        rows.append(dict(file=name,source_sha256=hashlib.sha256(original).hexdigest(),master_sha256=hashlib.sha256(master).hexdigest(),
            runtime_sha256=hashlib.sha256(runtime).hexdigest(),lr_db=round(20*math.log10(ratio(balanced)),5)))
    result=dict(kind='aster-balanced-clicks.v1',source_commit=config.SOURCE_COMMIT,left_gain=gain,right_gain=1,
        left_attenuation_db=20*math.log10(gain),timing_unchanged=True,no_boost=True,normalization=False,files=rows)
    (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(json.dumps(build(a.source,a.output),indent=2))
