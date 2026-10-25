"""Lossless PCM24→PCM32 container promotion for Kodi's GUI-sound loader."""
import argparse,hashlib,io,json,struct,wave
from pathlib import Path

def promote(data):
    with wave.open(io.BytesIO(data),'rb') as source:
        if source.getparams()[:3]!=(2,3,48000):raise ValueError('canonical-pcm24-required')
        count=source.getnframes();raw=source.readframes(count)
    if len(raw)!=count*6 or not 0<count<24000:raise ValueError('invalid-canonical-length')
    samples=[int.from_bytes(raw[i:i+3],'little',signed=True)<<8 for i in range(0,len(raw),3)]
    output=io.BytesIO()
    with wave.open(output,'wb') as target:
        target.setnchannels(2);target.setsampwidth(4);target.setframerate(48000)
        target.writeframes(struct.pack('<%di'%len(samples),*samples))
    return output.getvalue()

def build(source,output):
    source,output=Path(source),Path(output)
    if output.exists():raise ValueError('immutable-compatibility-output')
    (output/'resources').mkdir(parents=True);(output/'masters').mkdir()
    rows=[]
    for path in sorted(source.glob('*.wav')):
        original=path.read_bytes();converted=promote(original)
        (output/'masters'/path.name).write_bytes(original)
        (output/'resources'/path.name).write_bytes(converted)
        rows.append(dict(file=path.name,master_sha256=hashlib.sha256(original).hexdigest(),
            runtime_sha256=hashlib.sha256(converted).hexdigest()))
    if len(rows)!=7:raise ValueError('seven-canonical-files-required')
    result=dict(kind='aster-canonical-pcm32.v1',encoding='PCM32-lossless-from-PCM24',
        sample_rate=48000,channels=2,normalization=False,resampling=False,files=rows)
    (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();print(json.dumps(build(args.source,args.output),indent=2))
