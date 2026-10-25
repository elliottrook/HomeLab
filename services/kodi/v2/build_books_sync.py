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
FOURTH_SHA='d332a979018d92add2999909e4cf272190624c54bf4db5e0f1fb12c281f85af6'
FIFTH_SHA='010e23df40c70e1eaeeb478e359b9da7cb56223549701a3795aea2defa676ff8'
SIXTH_SHA='dd502b6770ec6c0f76e4c2fb4182c54c4b84e4c5162a70e0c0dd2a205a643dd7'
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
        'aster-books-sync3':(THIRD_SHA,'aster-books-sync4'),'aster-books-sync4':(FOURTH_SHA,'aster-books-sync5'),
        'aster-books-sync5':(FIFTH_SHA,'aster-books-sync6'),'aster-books-sync6':(SIXTH_SHA,'aster-books-sync7')}
    if old.get('stage') not in predecessors or sha(raw)!=predecessors[old['stage']][0]:raise ValueError('exact-books-predecessor-required')
    previous,new_name=predecessors[old['stage']]
    files={r['path']:(snapshot/'payload'/r['path']).read_bytes() for r in old['files']}
    if any(sha(files[r['path']])!=r['sha256'] for r in old['files']):raise ValueError('books-sync1-drift')
    files[PLUGIN+'service.py']=(HERE/'books_sync_service.py').read_bytes()
    files[PLUGIN+'resources/lib/books_sync.py']=(HERE/'books_sync.py').read_bytes()
    if new_name in ('aster-books-sync3','aster-books-sync4','aster-books-sync5','aster-books-sync7'):
        files[PLUGIN+'resources/lib/books_sync_bridge.py']=(HERE/'books_sync_bridge.py').read_bytes()
    if new_name=='aster-books-sync7':
        files[PLUGIN+'resources/lib/books_sleep.py']=(HERE/'books_sleep.py').read_bytes()
        # Keep duration for playback metadata; the Resume row displays the
        # authoritative whole-book position, never current-file remainder.
        data=files[PLUGIN+'default.py'];needle=b"        item.setProperty('AsterBooks.ParentTitle', title)"
        if data.count(needle)!=1:raise ValueError('resume-label-anchor')
        files[PLUGIN+'default.py']=data.replace(needle,
            b"        if entry.get('number') == 'R' and isinstance(entry.get('resume_position'), (int, float)):\n"
            b"            position = int(entry['resume_position'])\n"
            b"            item.setProperty('AsterBooks.Length', f'{position // 3600}:{position // 60 % 60:02d}:{position % 60:02d}')\n"+needle)
    if new_name=='aster-books-sync3':
        data=files[PLUGIN+'default.py'];needle=b"        item.setProperty('AsterBooks.Kind', kind)"
        if data.count(needle)!=1:raise ValueError('books-source-identity-anchor')
        files[PLUGIN+'default.py']=data.replace(needle,needle+b"\n        item.setProperty('AsterBooks.Episode', entry.get('episode_id', ''))")
    if new_name=='aster-books-sync6':
        for name in ('books_sleep.py','books_sleep_ui.py'):files[PLUGIN+'resources/lib/'+name]=(HERE/name).read_bytes()
        for suffix in ('svg','png'):
            name='sleep.'+suffix
            files['.kodi/addons/skin.asterhome/media/player-controls/'+name]=(HERE/'player-control-assets'/name).read_bytes()
        root=ET.fromstring(files[SKIN]);controls=root.find('controls')
        for node in controls:
            identity=node.get('id');left=node.find('left')
            if left is not None and ((node.get('type')=='button' and identity in ('9101','9102','9103','9104','9105'))
                or (node.get('type')=='image' and any('('+str(i)+')' in (node.findtext('visible') or '') for i in (9101,9102,9103,9104)))):
                left.text=str(int(left.text)-56)
            if identity=='9104':node.find('onright').text='9106'
        def add(kind,values,identity=None):
            node=ET.SubElement(controls,'control',dict(type=kind,**({'id':str(identity)} if identity else {})))
            for key,value in values.items():ET.SubElement(node,key).text=str(value)
            return node
        add('button',dict(left=676,top=890,width=76,height=64,label='Sleep timer',font='font20',textcolor='00000000',
            focusedcolor='00000000',texturefocus='',texturenofocus='',onleft=9104,onright=50,onup=9000,ondown=50,
            onclick='RunScript(special://home/addons/plugin.audio.asterbooks/resources/lib/books_sleep_ui.py)',
            visible='Player.HasAudio + !String.IsEmpty(Window(Home).Property(AsterBooks.SleepToken))'),9106)
        for focused,size,left,top,color in ((False,44,692,900,'asterInk'),(True,48,690,898,'asterGreen')):
            node=add('image',dict(left=left,top=top,width=size,height=size,aspectratio='keep',
                visible='Control.IsVisible(9106) + '+('' if focused else '!')+'Control.HasFocus(9106)'))
            ET.SubElement(node,'texture',dict(colordiffuse=color)).text='special://skin/media/player-controls/sleep.png'
        node=add('image',dict(left=704,top=953,width=20,height=2,visible='Control.IsVisible(9106) + Control.HasFocus(9106)'))
        ET.SubElement(node,'texture',dict(colordiffuse='asterGold')).text='special://skin/media/ui-solid.png'
        add('label',dict(left=150,top=959,width=680,height=28,label='Sleep timer',font='font16',textcolor='asterInk',
            align='center',aligny='center',visible='Control.IsVisible(9106) + Control.HasFocus(9106)'))
        add('label',dict(left=150,top=986,width=680,height=24,label='$INFO[Window(Home).Property(AsterBooks.SleepStatus)]',
            font='font16',textcolor='asterMuted',align='center',truncate='true'))
        files[SKIN]=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    before={r['path']:r['sha256'] for r in old['files']}
    manifest=dict(old,stage=new_name,previous_manifest_sha256=previous,
        files=[dict(path=n,sha256=sha(d),before_sha256=before.get(n)) for n,d in sorted(files.items())])
    output.mkdir(parents=True)
    for name,data in files.items():
        path=output/'payload'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    raw=(json.dumps(manifest,indent=2)+'\n').encode();(output/'manifest.json').write_bytes(raw);return sha(raw)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--snapshot',required=True);p.add_argument('--output',required=True)
    p.add_argument('--successor',action='store_true')
    args=p.parse_args();print((successor if args.successor else build)(args.snapshot,args.output))
