"""Private immutable manual Network page, not an installed settings replacement."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def layout():
    root=ET.Element('window');ET.SubElement(root,'defaultcontrol',always='true').text='200'
    ET.SubElement(root,'backgroundcolor').text='ff171c19';controls=ET.SubElement(root,'controls')
    group=ET.SubElement(controls,'control',type='group',id='600')
    ET.SubElement(group,'animation',effect='fade',start='100',end='100',time='50',
        condition='String.IsEqual(Window.Property(NetworkPreview.Paint),odd)').text='Conditional'
    def control(kind,n,x,y,w,h,**values):
        node=ET.SubElement(group,'control',dict(type=kind,**({'id':str(n)} if n else {})))
        for key,value in dict(left=x,top=y,width=w,height=h,**values).items():ET.SubElement(node,key).text=str(value)
        return node
    def label(n,x,y,w,h,text,font='font24',colour='fff3eee5'):
        return control('label',n,x,y,w,h,label=text,font=font,textcolor=colour,truncate='true')
    control('image',None,80,30,180,150,texture='special://skin/media/aster-compass-128.png',aspectratio='keep')
    label(None,310,52,1100,60,'Network status','font40')
    label(504,310,122,1110,38,'Read-only local configuration','font20','ffadccad')
    for n,x,w,text,left,right in ((200,1190,250,'Refresh local status',201,203),
                                (203,1460,250,'Check media services',200,201),(201,1740,110,'Back',203,200)):
        node=control('button',n,x,60,w,52,label=text,font='font20',textcolor='fff3eee5',focusedcolor='fff3eee5',
            align='center',aligny='center',onleft=left,onright=right,onup='noop',ondown='noop')
        ET.SubElement(node,'texturefocus',border='20',colordiffuse='ffd8b778').text='special://skin/media/ui-button-ring.png'
        ET.SubElement(node,'texturenofocus',border='20',colordiffuse='60000000').text='special://skin/media/ui-panel.png'
    label(501,100,235,1720,60,'','font28','ffadccad')
    label(502,100,310,1720,45,'','font24')
    label(None,100,395,780,40,'IPv4 addresses','font24','ffadccad')
    label(None,1000,395,820,40,'Default gateway','font24','ffadccad')
    label(None,1000,570,820,40,'Configured DNS servers','font24','ffadccad')
    label(None,100,690,780,40,'Media endpoint checks','font24','ffadccad')
    for n,x,y,w,h in ((511,100,455,780,215),(512,1000,455,820,100),(513,1000,630,820,180),
                       (514,100,860,1720,145),(516,100,745,780,100)):
        control('textbox',n,x,y,w,h,font='font20' if n in (514,516) else 'font24',textcolor='fff3eee5')
    label(505,100,1020,1720,35,'','font20','ffadccad')
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n'


def menu_layout():
    root=ET.Element('window',type='dialog')
    ET.SubElement(root,'defaultcontrol',always='true').text='1421'
    controls=ET.SubElement(root,'controls')
    def node(kind,n,x,y,w,h,**values):
        c=ET.SubElement(controls,'control',dict(type=kind,**({'id':str(n)} if n else {})))
        for k,v in dict(left=x,top=y,width=w,height=h,**values).items():ET.SubElement(c,k).text=str(v)
        return c
    panel=node('image',None,1300,91,330,146)
    ET.SubElement(panel,'texture',border='18',colordiffuse='b0000000').text='special://skin/media/ui-panel.png'
    for n,y,label,other in ((1421,101,'Network status',1422),(1422,163,'View Kodi log',1421)):
        c=node('button',n,1312,y,306,62,label=label,font='font24',textcolor='fff3eee5',
            focusedcolor='fff3eee5',disabledcolor='ff96988f',align='left',aligny='center',
            textoffsetx='20',onup=other,ondown=other,onleft='noop',onright='noop')
        ET.SubElement(c,'texturefocus',border='18',colordiffuse='ff005c46').text='special://skin/media/ui-panel.png'
        ET.SubElement(c,'texturenofocus',border='18',colordiffuse='40000000').text='special://skin/media/ui-panel.png'
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n'


def build(output):
    here=Path(__file__).resolve().parent;root=Path(output);root.mkdir(mode=0o700)
    files={'default.py':(here/'network_preview/default.py').read_bytes(),
        'network_diagnostics.py':(here/'network_diagnostics.py').read_bytes(),
        'network_service_checks.py':(here/'network_service_checks.py').read_bytes(),
        'resources/skins/Default/1080i/NetworkPreview.xml':layout(),
        'resources/skins/Default/1080i/DiagnosticsMenu.xml':menu_layout()}
    rows=[]
    for name,raw in sorted(files.items()):
        path=root/name;path.parent.mkdir(mode=0o700,parents=True,exist_ok=True);path.write_bytes(raw);path.chmod(0o600)
        rows.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    value=dict(kind='hp-network-preview.v5',normal_entry=False,network_probes=True,
        explicit_service_checks=True,diagnostics_menu=True,network_changes=False,files=rows)
    path=root/'manifest.json';path.write_text(json.dumps(value,indent=2)+'\n');path.chmod(0o600)
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    print(build(parser.parse_args().output))
