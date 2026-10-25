"""Build a private exact-predecessor HP Books observer overlay; v1 stays frozen."""
import argparse,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
from books_sync import ACCOUNT
HERE=Path(__file__).resolve().parent
BEFORE={'service.py':'a3eb7f1e1224e9920385b7ee2525f2a4cb8f5df4c3d3e430da1b0ade10ff28f8',
 'default.py':'abaaa03fd5c3cce7e4b111965ccd82ca6314000707f4c4b7a40694005f082d4b',
 'MyMusicNav.xml':'6ee9620806a65f6e0b7e8fb393ee30dde592ddf477a52726ed91d8900d107864'}
PLUGIN='.kodi/addons/plugin.audio.asterbooks/'
SKIN='.kodi/addons/skin.asterhome/1080i/MyMusicNav.xml'
FLAG='.kodi/userdata/addon_data/plugin.audio.asterbooks/progress-enabled.json'
LIBRARIES=('books_progress.py','books_progress_reader.py','books_progress_trial.py','books_sync.py','books_sync_bridge.py')
FIRST_SHA='252f182781531cb9e54aaaeeb58a9ddc1bbb0e1eb08985a94908a1c16d62e89a'
SECOND_SHA='fce7bf41f64e7617a62a26af322ae98460eafd6ec87efc681ed812d15ef5485f'
THIRD_SHA='7bc5c6ec96c8c0bfb0a18272e8da54ecd4bb647622e150864dc229aa41576de9'
def sha(data):return hashlib.sha256(data).hexdigest()
def build(snapshot,output):
    snapshot,output=Path(snapshot),Path(output)
    if output.exists():raise ValueError('immutable-books-sync-stage')
    for name,digest in BEFORE.items():
        if sha((snapshot/name).read_bytes())!=digest:raise ValueError('books-predecessor-drift:'+name)
    default=(snapshot/'default.py').read_bytes()
    needle=b"        item.setProperty('AsterBooks.Kind', kind)"
    if default.count(needle)!=1:raise ValueError('books-plugin-anchor')
    default=default.replace(needle,needle+b"\n        item.setProperty('AsterBooks.ProgressSync', entry.get('progress_sync', 'Playback only'))\n        item.setProperty('AsterBooks.Resume', 'true' if entry.get('number') == 'R' else 'false')")
    default=default.replace(b'xbmcplugin.endOfDirectory(handle)',b'xbmcplugin.endOfDirectory(handle, cacheToDisc=False)')
    root=ET.fromstring((snapshot/'MyMusicNav.xml').read_bytes());controls=root.find('controls')
    for condition,label in (('Player.HasAudio','$INFO[Window(Home).Property(AsterBooks.SyncStatus)]'),
        ('!Player.HasAudio','$INFO[Container(50).ListItem.Property(AsterBooks.ProgressSync)]')):
        node=ET.SubElement(controls,'control',dict(type='label'))
        for key,value in dict(left=150,top=1012,width=680,height=34,font='font20',textcolor='asterMuted',
            label=label,visible=condition,truncate='true').items():ET.SubElement(node,key).text=str(value)
    files={PLUGIN+'service.py':(HERE/'books_sync_service.py').read_bytes(),PLUGIN+'default.py':default,
        SKIN:ET.tostring(root,encoding='utf-8',xml_declaration=True),
        FLAG:(json.dumps(dict(enabled=True,host='AsterTV',account_sha256=ACCOUNT,kind='aster-books-sync-pilot.v1'),indent=2)+'\n').encode()}
    for name in LIBRARIES:files[PLUGIN+'resources/lib/'+name]=(HERE/name).read_bytes()
    old={PLUGIN+'service.py':BEFORE['service.py'],PLUGIN+'default.py':BEFORE['default.py'],SKIN:BEFORE['MyMusicNav.xml']}
    output.mkdir(parents=True)
    for name,data in files.items():
        path=output/'payload'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    manifest=dict(kind='hp-books-shared-progress.v1',stage='aster-books-sync1',account_sha256=ACCOUNT,
        bridge_sha256='f37d51aec0bb8b48c1d31e9f9c442e4476130630b67a5bdc070af18dfd1a5c67',
        files=[dict(path=name,sha256=sha(data),before_sha256=old.get(name)) for name,data in sorted(files.items())])
    raw=(json.dumps(manifest,indent=2)+'\n').encode();(output/'manifest.json').write_bytes(raw)
    return sha(raw)
def successor(snapshot,output):
    snapshot,output=Path(snapshot),Path(output)
    if output.exists():raise ValueError('immutable-books-sync-stage')
    raw=(snapshot/'manifest.json').read_bytes()
    old=json.loads(raw)
    predecessors={'aster-books-sync1':(FIRST_SHA,'aster-books-sync2'),'aster-books-sync2':(SECOND_SHA,'aster-books-sync3'),
        'aster-books-sync3':(THIRD_SHA,'aster-books-sync4')}
    if old.get('stage') not in predecessors or sha(raw)!=predecessors[old['stage']][0]:raise ValueError('exact-books-predecessor-required')
    previous,new_name=predecessors[old['stage']]
    files={r['path']:(snapshot/'payload'/r['path']).read_bytes() for r in old['files']}
    if any(sha(files[r['path']])!=r['sha256'] for r in old['files']):raise ValueError('books-sync1-drift')
    files[PLUGIN+'service.py']=(HERE/'books_sync_service.py').read_bytes()
    files[PLUGIN+'resources/lib/books_sync.py']=(HERE/'books_sync.py').read_bytes()
    if new_name in ('aster-books-sync3','aster-books-sync4'):
        files[PLUGIN+'resources/lib/books_sync_bridge.py']=(HERE/'books_sync_bridge.py').read_bytes()
    if new_name=='aster-books-sync3':
        data=files[PLUGIN+'default.py'];needle=b"        item.setProperty('AsterBooks.Kind', kind)"
        if data.count(needle)!=1:raise ValueError('books-source-identity-anchor')
        files[PLUGIN+'default.py']=data.replace(needle,needle+b"\n        item.setProperty('AsterBooks.Episode', entry.get('episode_id', ''))")
    before={r['path']:r['sha256'] for r in old['files']}
    manifest=dict(old,stage=new_name,previous_manifest_sha256=previous,
        files=[dict(path=n,sha256=sha(d),before_sha256=before[n]) for n,d in sorted(files.items())])
    output.mkdir(parents=True)
    for name,data in files.items():
        path=output/'payload'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    raw=(json.dumps(manifest,indent=2)+'\n').encode();(output/'manifest.json').write_bytes(raw);return sha(raw)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--snapshot',required=True);p.add_argument('--output',required=True)
    p.add_argument('--successor',action='store_true')
    args=p.parse_args();print((successor if args.successor else build)(args.snapshot,args.output))
