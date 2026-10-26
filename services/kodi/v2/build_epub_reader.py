"""Immutable synthetic HP reading proof; no normal-route or add-on install."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from epub_fixture import build as fixture

def layout():
    root=ET.Element('window');ET.SubElement(root,'defaultcontrol',always='true').text='500'
    ET.SubElement(root,'backgroundcolor').text='ffe6dac8'
    controls=ET.SubElement(root,'controls');group=ET.SubElement(controls,'control',type='group')
    ET.SubElement(group,'animation',effect='fade',start='100',end='100',time='50',condition='String.IsEqual(Window.Property(Epub.Revision),1)').text='Conditional'
    def control(kind,identity,x,y,w,h,**fields):
        c=ET.SubElement(group,'control',type=kind,id=str(identity))
        for k,v in dict(left=x,top=y,width=w,height=h,**fields).items():ET.SubElement(c,k).text=str(v)
        return c
    control('image',10,95,35,170,120,texture='special://skin/media/28-aster-books-logo.png',aspectratio='keep')
    control('label',11,340,65,1250,55,label='The Lantern House',font='font40',textcolor='ff1e241f')
    control('label',12,340,130,1250,40,label='Synthetic chapter · Reading preview · No narration or saved progress',font='font20',textcolor='ff65675d')
    control('label',13,340,205,1240,42,label='Chapter one',font='font24',textcolor='ff1f513b')
    for size,identity in ((24,501),(30,502),(40,503)):
        control('textbox',identity,340,265,1240,640,label='',font='font'+str(size),textcolor='ff1e241f',
                visible='String.IsEqual(Window.Property(Epub.Size'+str(size)+'),true)')
    control('button',500,340,245,1240,660,label='',textcolor='00000000',focusedcolor='00000000',
            texturefocus='',texturenofocus='',onleft='noop',onright='noop',onup=201,ondown=201)
    control('label',504,340,965,250,40,label='',font='font20',textcolor='ff1f513b',aligny='center')
    for identity,x,width,label,left,right in ((201,670,190,'Previous',200,202),(202,880,190,'Next',201,203),(203,1090,250,'Text size',202,200),(200,1360,180,'Back',203,201)):
        c=control('button',identity,x,951,width,64,label=label,font='font24',textcolor='ff1e241f',focusedcolor='fff3eee5',align='center',aligny='center',onup=500,ondown=500,onleft=left,onright=right)
        ET.SubElement(c,'texturefocus',border='18',colordiffuse='ff1f513b').text='special://skin/media/ui-panel.png'
        ET.SubElement(c,'texturenofocus',border='18',colordiffuse='16000000').text='special://skin/media/ui-panel.png'
        control('image',identity+600,x-1,950,width+2,66,texture='special://skin/media/ui-compact-card-ring.png',colordiffuse='ffc2a06b',visible='Control.HasFocus('+str(identity)+')').find('texture').set('border','18')
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n'

def build(output):
    root=Path(output);root.mkdir(mode=0o700,parents=True,exist_ok=False);here=Path(__file__).parent
    files={'default.py':(here/'epub_reader/default.py').read_bytes(),'epub_chapter.py':(here/'epub_chapter.py').read_bytes(),
           'epub_pages.py':(here/'epub_pages.py').read_bytes(),'sample.epub':fixture(),
           'resources/skins/Default/1080i/EpubReader.xml':layout()}
    for name,raw in files.items():
        path=root/name;path.parent.mkdir(mode=0o700,parents=True,exist_ok=True);path.write_bytes(raw);path.chmod(0o600)
    manifest=dict(kind='hp-epub-reader.v1',synthetic=True,network=False,playback=False,progress=False,normal_entry=False,
                  files={name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()})
    raw=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode();(root/'manifest.json').write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);print(build(parser.parse_args().output))
