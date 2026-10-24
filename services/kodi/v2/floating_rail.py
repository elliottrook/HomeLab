"""Generate a small reversible shared-rail overlay; v1 sources stay untouched."""
import argparse,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET

SOURCE=Path(__file__).resolve().parent.parent/'skin.asterhome/1080i/IncludesHub.xml'
ROUTES=(9001,9002,9003,9004,9007,9008,9005)


def transform(data):
    root=ET.fromstring(data)
    definition=root.find("include[@name='AsterNavigationRail']/definition")
    expanded=definition.find("control[@id='9000']")
    collapsed=definition.find("control[@id='9006']")
    def field(node,name,value):
        child=node.find(name)
        if child is None:child=ET.SubElement(node,name)
        child.text=str(value)
    for group,width in ((expanded,250),(collapsed,72)):
        for key,value in dict(left=22,top=230,width=width,height=620).items():field(group,key,value)
    animation=expanded.find('animation');animation.set('start','-12,0');animation.set('time','150')
    for group,width in ((expanded,250),(collapsed,72)):
        background=next(c for c in group.findall('control') if (c.findtext('texture') or '').endswith('/rail-background.png'))
        for key,value in dict(left=0,top=0,width=width,height=620).items():field(background,key,value)
        texture=background.find('texture');texture.text='special://skin/media/ui-panel.png';texture.set('border','24');texture.set('colordiffuse','ffad8a4d')
        inner=ET.Element('control',dict(type='image'))
        if background.find('visible') is not None:field(inner,'visible',background.findtext('visible'))
        for key,value in dict(left=1,top=1,width=width-2,height=618).items():field(inner,key,value)
        ET.SubElement(inner,'texture',dict(border='24',colordiffuse='f23b3a32')).text='special://skin/media/ui-panel.png'
        group.insert(list(group).index(background)+1,inner)
    # Retain routes/actions; correct only the Books landing page's hidden target.
    for index,identity in enumerate(ROUTES):
        button=expanded.find(f"control[@id='{identity}']")
        old=int(button.findtext('top'));new=134+index*64
        icon=next(c for c in expanded.findall("control[@type='image']") if c.findtext('top')==str(old+16))
        field(button,'top',new);field(button,'left',62)
        field(icon,'top',new+13);field(icon,'left',14)
        right=button.find('onright');right.set('condition','!Window.IsActive(11110)')
        right.text='SetFocus('+right.text+')'
        position=list(button).index(right)
        books=ET.Element('onright',dict(condition='Window.IsActive(11110)'));books.text='SetFocus(501)'
        button.insert(position,books)
    logo=next(c for c in expanded.findall("control[@type='image']") if (c.findtext('texture') or '').endswith('/aster-home-logo-512.png'))
    field(logo,'top',24)
    compass=collapsed.find("control[@id='8997']");field(compass,'left',14);field(compass,'top',24)
    # Match by original position: the XML source does not store Music in visual order.
    original=(150,214,278,342,406,470,534)
    images=[c for c in collapsed.findall("control[@type='image']") if c.findtext('top') in tuple(map(str,original))]
    positions={old:143+index*64 for index,old in enumerate(original)}
    for icon in images:
        old=int(icon.findtext('top'))
        for key,value in dict(left=14,top=positions[old],width=44,height=44).items():field(icon,key,value)
    opener=collapsed.find("control[@id='8999']")
    for key,value in dict(left=0,top=0,width=72,height=620,label='').items():field(opener,key,value)
    # Keep the invisible focus-entry proxy: removing its ID breaks Left entry.
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)


def build(destination,previous=None):
    destination=Path(destination)
    if destination.exists():raise ValueError('immutable-destination-exists')
    before=SOURCE.read_bytes();after=transform(before)
    destination.mkdir(parents=True)
    (destination/'IncludesHub.xml').write_bytes(after)
    manifest=dict(schema=1,kind='hp-floating-rail',path='1080i/IncludesHub.xml',
        before_sha256=hashlib.sha256(before).hexdigest(),sha256=hashlib.sha256(after).hexdigest())
    if previous:
        raw=Path(previous).read_bytes();prior=json.loads(raw)
        if prior.get('kind')!='hp-floating-rail' or prior.get('path')!=manifest['path']:raise ValueError('invalid-predecessor')
        manifest['before_sha256']=prior['sha256'];manifest['previous_manifest_sha256']=hashlib.sha256(raw).hexdigest()
    data=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode()
    (destination/'manifest.json').write_bytes(data)
    return hashlib.sha256(data).hexdigest()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--previous')
    args=parser.parse_args();print(build(args.output,args.previous))
