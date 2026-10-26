"""New immutable, manual HP Home view; no active skin installation."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def layout():
    root=ET.Element('window')
    ET.SubElement(root,'defaultcontrol',always='true').text='301'
    ET.SubElement(root,'backgroundcolor').text='ff171c19'
    controls=ET.SubElement(root,'controls')
    group=ET.SubElement(controls,'control',type='group',id='600')
    ET.SubElement(group,'width').text='1920';ET.SubElement(group,'height').text='1080'
    ET.SubElement(group,'animation',effect='fade',start='100',end='100',time='50',
        condition='String.IsEqual(Window.Property(HomePreview.Revision),odd)').text='Conditional'
    def control(kind,identity,x,y,w,h,**values):
        node=ET.SubElement(group,'control',type=kind,**({'id':str(identity)} if identity else {}))
        for key,value in dict(left=x,top=y,width=w,height=h,**values).items():
            ET.SubElement(node,key).text=str(value)
        return node
    def button(identity,x,y,w,h,label,left,right,up,down,card=False):
        node=control('button',identity,x,y,w,h,label=label,font='font20',
            textcolor='00000000' if card else 'fff3eee5',
            focusedcolor='00000000' if card else 'fff3eee5',align='center',aligny='center',
            onleft=left,onright=right,onup=up,ondown=down)
        ET.SubElement(node,'texturefocus',border='20',colordiffuse='dd005c46' if card else 'ffd8b778').text=(
            'special://skin/media/ui-panel.png' if card else 'special://skin/media/ui-button-ring.png')
        ET.SubElement(node,'texturenofocus',border='20',colordiffuse='60000000').text='special://skin/media/ui-panel.png'
    control('image',None,95,30,220,120,texture='special://skin/media/aster-home-horizontal-512.png',aspectratio='keep')
    control('label',None,350,48,1050,55,label='Home at a glance',font='font40',textcolor='fff3eee5')
    control('label',None,350,110,1100,34,label='HP preview · exported status only · no device controls',font='font20',textcolor='ffadccad')
    button(201,1510,60,205,52,'Reload local feed',301,200,201,302)
    button(200,1740,60,110,52,'Back',201,301,200,302)
    control('label',501,100,180,1720,42,label='',font='font24',textcolor='ffadccad')
    navigation=((201,302,201,303),(301,200,201,304),(201,304,301,'noop'),(303,200,302,'noop'))
    for index,name in enumerate(('Lighting','Comfort','Cameras','Timers')):
        x=100 if index%2==0 else 995;y=255 if index<2 else 580
        identity=301+index
        button(identity,x,y,825,280,name+' · read-only',*navigation[index],card=True)
        ring=control('image',None,x,y,825,280,visible='Control.HasFocus('+str(identity)+')')
        ET.SubElement(ring,'texture',border='20',colordiffuse='fff3eee5').text='special://skin/media/ui-compact-card-ring.png'
        control('label',None,x+30,y+20,760,45,label=name,font='font28',textcolor='fff3eee5')
        control('label',401+index,x+30,y+80,760,40,label='',font='font24',textcolor='ffadccad')
        control('textbox',411+index,x+30,y+135,760,130,label='',font='font20',textcolor='fff3eee5')
    control('label',502,100,905,1720,34,label='',font='font20',textcolor='ffbfc6bb')
    control('label',503,100,957,1720,34,label='',font='font20',textcolor='ffadccad')
    control('label',None,100,1009,1720,34,label='Local-file preview · no camera images, timer actions, live control or network refresh',font='font20',textcolor='ffbfc6bb')
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n'


def build(output):
    here=Path(__file__).resolve().parent;output=Path(output)
    if output.exists():raise ValueError('immutable-home-preview-output')
    files={'default.py':(here/'home_preview/default.py').read_bytes(),
        'resources/skins/Default/1080i/HomePreview.xml':layout()}
    for name in ('home_freshness.py','home_dashboard_model.py','home_preview_source.py'):
        files['resources/lib/'+name]=(here/name).read_bytes()
    rows=[]
    for name,data in sorted(files.items()):
        target=output/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        rows.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    manifest=dict(kind='hp-home-preview.v1',normal_entry=False,device_actions=False,network=False,files=rows)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return hashlib.sha256((output/'manifest.json').read_bytes()).hexdigest()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    print(build(parser.parse_args().output))
