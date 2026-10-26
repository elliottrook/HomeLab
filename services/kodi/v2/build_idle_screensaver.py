"""Prepare an immutable native HP idle add-on. Does not install or select it."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
IDENTITY='screensaver.asterhome.v2lab'
MARK_SHA='147bed555587f8c932a860deab48ba64c2e5b6204f0840627d7669a29a34c4f7'
SOLID_SHA='60ffd2c283635d9875ee649d4dd294fb97af2443ff05508d968c858b011dbea0'

def xml(node):return ET.tostring(node,encoding='utf-8',xml_declaration=True)+b'\n'
def addon():
    root=ET.Element('addon',id=IDENTITY,name='Aster TV idle lab',version='0.1.0',**{'provider-name':'Aster'})
    requires=ET.SubElement(root,'requires');ET.SubElement(requires,'import',addon='xbmc.python',version='3.0.0')
    ET.SubElement(root,'extension',point='xbmc.ui.screensaver',library='default.py')
    metadata=ET.SubElement(root,'extension',point='xbmc.addon.metadata')
    ET.SubElement(metadata,'summary',lang='en_GB').text='Private black or restrained Aster idle presentation'
    ET.SubElement(metadata,'description',lang='en_GB').text='HP lab only. No media, cameras, clock, household content, network or sound.'
    ET.SubElement(metadata,'platform').text='all'
    return xml(root)
def layout():
    root=ET.Element('window',type='dialog');ET.SubElement(root,'backgroundcolor').text='ff000000'
    controls=ET.SubElement(root,'controls')
    for n,x,y,w,h,texture,tint in ((1,0,0,1920,1080,'resources/solid.png','ff000000'),
        (10,100,90,320,206,'resources/mark.png','b8ffffff')):
        c=ET.SubElement(controls,'control',type='image',id=str(n))
        for key,value in dict(left=x,top=y,width=w,height=h).items():ET.SubElement(c,key).text=str(value)
        ET.SubElement(c,'texture',colordiffuse=tint).text='special://home/addons/'+IDENTITY+'/'+texture
        ET.SubElement(c,'aspectratio').text='stretch' if n==1 else 'keep'
        if n==10:ET.SubElement(c,'animation',effect='fade',start='0',end='100',time='900').text='VisibleChange'
    return xml(root)
def settings():
    root=ET.Element('settings')
    ET.SubElement(root,'setting',id='presentation',type='labelenum',label='Idle presentation',
        values='black|aster',default='black')
    return xml(root)
def build(output):
    here=Path(__file__).resolve().parent;root=Path(output);root.mkdir(mode=0o700)
    media=here.parent/'skin.asterhome/media'
    mark=(media/'32-aster-tv-logo.png').read_bytes();solid=(media/'ui-solid.png').read_bytes()
    if hashlib.sha256(mark).hexdigest()!=MARK_SHA or hashlib.sha256(solid).hexdigest()!=SOLID_SHA:
        raise ValueError('idle-approved-asset-drift')
    files={'addon.xml':addon(),'default.py':(here/'idle_screensaver/default.py').read_bytes(),
        'idle_presentation.py':(here/'idle_presentation.py').read_bytes(),
        'resources/settings.xml':settings(),'resources/skins/Default/1080i/AsterIdle.xml':layout(),
        'resources/mark.png':mark,'resources/solid.png':solid}
    rows=[];archive=root/(IDENTITY+'-0.1.0.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as package:
        for name,raw in sorted(files.items()):
            path=root/'payload'/IDENTITY/name;path.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
            path.write_bytes(raw);path.chmod(0o600)
            rows.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
            info=zipfile.ZipInfo(IDENTITY+'/'+name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100600<<16;package.writestr(info,raw)
    archive.chmod(0o600)
    helpers={}
    for name in ('idle_screensaver_install.py','deploy_idle_screensaver.py'):
        data=(here/name if name=='idle_screensaver_install.py' else here/'tools'/name).read_bytes()
        (root/name).write_bytes(data);(root/name).chmod(0o600);helpers[name]=hashlib.sha256(data).hexdigest()
    m=dict(kind='hp-idle-presentation.v2',addon_id=IDENTITY,normal_entry=False,default_mode='black',
        network=False,speech=False,settings_changes=False,files=rows,
        archive=archive.name,archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),helpers=helpers)
    path=root/'manifest.json';path.write_text(json.dumps(m,indent=2)+'\n');path.chmod(0o600)
    return hashlib.sha256(path.read_bytes()).hexdigest()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);print(build(p.parse_args().output))
