"""Compose only the current HP header/search/status successors from a snapshot."""
import argparse,hashlib,json
from pathlib import Path
from branding_rails import header,settings,extend_search
from build_review3 import raw,sha,rows,SKIN

SEARCH_SHA='d798961e64038a3a8ad3a955292a63356506a2fa36218f3e8801f0d64e1ae146'
REVIEW_SHA='1593f1f8982be294c19ec0ad3d51b7879428abc08a1fb6a6f78a5818f230155d'

def build(snapshot,output):
    snapshot,output=Path(snapshot),Path(output)
    if output.exists():raise ValueError('immutable-branding-output')
    source=snapshot/'aster-global-search-ui21'
    if sha((source/'manifest.json').read_bytes())!=SEARCH_SHA:raise ValueError('search-predecessor')
    meta=json.loads((source/'manifest.json').read_text());objects={}
    for r in meta['files']:
        data=(source/r['path']).read_bytes()
        if sha(data)!=r['sha256']:raise ValueError('search-payload-drift')
        if r['path'].endswith(('.py','.xml')):data=data.replace(b'aster-global-search-ui21',b'aster-global-search-ui22')
        objects[r['path']]=data
    objects['default.py']=extend_search(objects['default.py'])
    objects['overlay/custom_1127_search.xml']=objects['overlay/custom_1127_search.xml'].replace(b'<onclick>ActivateWindow(Home)</onclick>',b'<onclick>SetProperty(AsterSearch.Command,back,home)</onclick>')
    objects['resources/lib/movie_player.py']=objects['resources/lib/movie_player.py'].replace(meta['previous_manifest_sha256'].encode(),SEARCH_SHA.encode())
    changed={};before={}
    def skin(name,data):
        n=SKIN+'1080i/'+name
        old=(snapshot/'1080i'/name).read_bytes();before[n]=sha(old);changed[n]=data
    layouts=(('IncludesBooks.xml',(110,111,112),(180,220,180),'$PARAM[firsttile]'),
        ('IncludesMusic.xml',(110,111,112,113,114),(180,180,170,180,170),500),
        ('custom_1111_digest.xml',(310,311,301),(210,220,150),500),
        ('custom_1122_breaking.xml',(310,311,301),(210,220,150),500),
        ('custom_1112_home.xml',(300,301),(170,170),302))
    for name,ids,widths,down in layouts:
        skin(name,header((snapshot/'1080i'/name).read_bytes(),ids,widths,down))
    skin('Settings.xml',settings((snapshot/'1080i/Settings.xml').read_bytes()))
    skin('Home.xml',objects['overlay/Home.xml'])
    skin('custom_1127_search.xml',objects['overlay/custom_1127_search.xml'])
    if (snapshot/'1080i/Home.xml').read_bytes()!=(source/'overlay/Home.xml').read_bytes():raise ValueError('native-home-predecessor')
    integration=json.loads((snapshot/'music-integration.json').read_text())
    for r in integration['files']:
        n=SKIN+r['path']
        if n in changed:r.update(sha256=sha(changed[n]),bytes=len(changed[n]))
    n='.aster-checkpoints/aster-music-integration-20261024/active-manifest.json'
    changed[n]=raw(integration);before[n]=sha((snapshot/'music-integration.json').read_bytes())
    search_raw=raw(dict(meta,stage='aster-global-search-ui22',previous_manifest_sha256=SEARCH_SHA,files=rows(objects)))
    for name,data in dict(objects,**{'manifest.json':search_raw}).items():
        n='.aster-staging/aster-global-search-ui22/'+name;changed[n]=data;before[n]=None
    n='.aster-checkpoints/aster-global-search-20261024/active-manifest.json';changed[n]=search_raw;before[n]=SEARCH_SHA
    output.mkdir();records=[]
    for n,data in sorted(changed.items()):
        target=output/'payload'/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        records.append(dict(path=n,sha256=sha(data),before_sha256=before[n]))
    manifest=dict(kind='hp-review9',name='aster-review9',previous_manifest_sha256=REVIEW_SHA,files=records,
        search=sha(search_raw),music_integration=sha(raw(integration)))
    (output/'manifest.json').write_bytes(raw(manifest));return sha(raw(manifest))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--snapshot',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(build(a.snapshot,a.output))
