"""Eight-file successor for asynchronous header focus; no player changes."""
import argparse,json
from pathlib import Path
import xml.etree.ElementTree as ET
from build_review3 import raw,sha,SKIN
from review2_ui import field,encoded
PREVIOUS='70c5661d2305e332655ef10ebf19cce883c4d221c60001b54ff19b2d0c34ae78'
def build(previous,output):
    previous,output=Path(previous),Path(output)
    if output.exists() or sha((previous/'manifest.json').read_bytes())!=PREVIOUS:raise ValueError('immutable-exact-predecessor')
    parent=json.loads((previous/'manifest.json').read_text());payload={};records=[]
    integration_name='.aster-checkpoints/aster-music-integration-20261024/active-manifest.json'
    for r in parent['files']:
        if not r['path'].startswith(SKIN+'1080i/'):continue
        data=(previous/'payload'/r['path']).read_bytes();root=ET.fromstring(data);button=root.find('.//control[@id="139"]')
        if button is not None:
            field(button,'onclick','RunScript(special://skin/tools/header_search.py)');payload[r['path']]=(encoded(root),r['sha256'])
    old=(previous/'payload'/integration_name).read_bytes();integration=json.loads(old)
    for r in integration['files']:
        n=SKIN+r['path']
        if n in payload:r.update(sha256=sha(payload[n][0]),bytes=len(payload[n][0]))
    payload[integration_name]=(raw(integration),sha(old))
    payload[SKIN+'tools/header_search.py']=((Path(__file__).parent/'tools/header_search.py').read_bytes(),None)
    output.mkdir()
    for n,(data,before) in sorted(payload.items()):
        p=output/'payload'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        records.append(dict(path=n,sha256=sha(data),before_sha256=before))
    manifest=dict(kind='hp-review10',name='aster-review10',previous_manifest_sha256=PREVIOUS,files=records,music_integration=sha(raw(integration)))
    (output/'manifest.json').write_bytes(raw(manifest));return sha(raw(manifest))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--previous',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(build(a.previous,a.output))
