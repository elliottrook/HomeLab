"""Immutable standalone HP scrub stage plus one unactivated OSD candidate."""
import argparse,hashlib,json,re
from pathlib import Path
import xml.etree.ElementTree as ET
from player_controls import page,SKIN
HERE=Path(__file__).resolve().parent
BASE='7fe65ddc4e2e33931a771bd57de349ae7a1d47e4d1983534a83e02a5a6ed03c6'
def build(output,name,native=False):
    if not re.fullmatch(r'aster-video-scrub[1-9][0-9]*',name):raise ValueError('invalid-stage')
    output=Path(output)
    if output.exists() and any(output.iterdir()):raise ValueError('nonempty-stage')
    baseline=page('VideoOSD.xml',(SKIN/'1080i/VideoOSD.xml').read_bytes())
    if hashlib.sha256(baseline).hexdigest()!=BASE:raise ValueError('osd-source-drift')
    root=ET.fromstring(baseline)
    group=root.find('./controls/control[@type="group"]')
    entry=ET.SubElement(group,'control',dict(type='button',id='7200'))
    for key,value in dict(left=60,top=184,width=1800,height=54,label='Seek position',font='font20',textcolor='00000000',
        focusedcolor='00000000',texturefocus='',texturenofocus='',visible='Player.SeekEnabled',
        onleft='7200',onright='7200',onup='7100',ondown='602').items():ET.SubElement(entry,key).text=str(value)
    ET.SubElement(entry,'onclick').text='Dialog.Close(VideoOSD)'
    ET.SubElement(entry,'onclick').text='RunScript(/storage/.aster-staging/'+name+'/default.py)'
    for identity in ('600','601','602','605','606','607','603','70043'):
        button=group.find('control[@id="'+identity+'"]');old=button.find('onup')
        old.set('condition','!Player.SeekEnabled')
        new=ET.Element('onup',dict(condition='Player.SeekEnabled'));new.text='7200'
        button.insert(list(button).index(old),new)
    focus=ET.SubElement(group,'control',dict(type='label'))
    for key,value in dict(left=70,top=228,width=1780,height=30,label='OK to seek · preview first',font='font16',
        textcolor='asterSage',align='center',visible='Control.HasFocus(7200)').items():ET.SubElement(focus,key).text=str(value)
    ET.indent(root,space='  ')
    source=HERE/('video_scrub_native' if native else 'video_scrub_dialog')
    files={p.relative_to(source).as_posix():p.read_bytes()
        for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    files['resources/lib/video_scrub.py']=(HERE/'video_scrub.py').read_bytes()
    files['overlay/VideoOSD.xml']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    rows=[]
    for path,data in sorted(files.items()):
        target=output/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        rows.append(dict(path=path,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    manifest=dict(schema=1,kind='hp-video-scrub-native' if native else 'hp-video-scrub',stage=name,before_sha256=BASE,files=rows)
    raw=(json.dumps(manifest,indent=2)+'\n').encode();(output/'manifest.json').write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--stage',required=True);parser.add_argument('--native',action='store_true',required=True)
    args=parser.parse_args();print(build(args.output,args.stage,args.native))
