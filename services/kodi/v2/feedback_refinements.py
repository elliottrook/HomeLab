"""Pure, bounded visual transforms for the first household v2 review."""
from copy import deepcopy
from pathlib import Path
import xml.etree.ElementTree as ET

ROUTES=(9001,9002,9003,9004,9007,9005)
DESTINATIONS=((9001,'Media','media-128.png'),(9002,'Books','21-books-app.png'),
    (9003,'News','news-digest-128.png'),(9004,'Home','home-hub-128.png'),
    (9007,'Music','20-music-app.png'),(9005,'Settings','31-settings-app.png'))

def field(node,key,value):
    child=node.find(key)
    if child is None:child=ET.SubElement(node,key)
    child.text=str(value)

def video_osd(data):
    root=ET.fromstring(data)
    group=root.find('./controls/control[@type="group"]')
    background=next(c for c in group.findall("control[@type='image']")
                    if (c.findtext('texture') or '').endswith('/ui-hero-bottom-fade.png'))
    field(background,'top',-170);field(background,'height',640)
    background.find('texture').attrib.pop('flipy',None)
    field(background,'colordiffuse','7a000000')
    for label in group.findall("control[@type='label']"):
        field(label,'shadowcolor','cc000000')
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def media_header(data):
    root=ET.fromstring(data)
    group=next(g for g in root.iter('control') if g.find("control[@id='134']") is not None)
    old_positions={i:int(group.find(f"control[@id='{i}']/left").text) for i in range(130,135)}
    template=deepcopy(group.find("control[@id='134']"))
    includes=ET.parse(Path(__file__).resolve().parent.parent/'skin.asterhome/1080i/Includes.xml').getroot()
    style=includes.find("include[@name='AsterTopCategoryButton']")
    for identity in range(130,135):
        button=group.find(f"control[@id='{identity}']");position=385+(identity-130)*192
        for include in list(button.findall('include')):button.remove(include)
        for node in style:
            if button.find(node.tag) is None:button.append(deepcopy(node))
        field(button,'left',position);field(button,'width',180);field(button,'textoffsetx',24)
        field(button,'onright',identity+1 if identity<134 else 136)
        for image in group.findall("control[@type='image']"):
            old=image.findtext('left')
            if old==str(old_positions[identity]+12):field(image,'left',position+8)
            elif old==str(old_positions[identity]) and image.find('visible') is not None:
                field(image,'left',position);field(image,'width',180)
    back=next(c for c in group.findall("control[@type='image']") if c.findtext('left')=='405')
    field(back,'left',375);field(back,'width',1290)
    template.set('id','136')
    for include in list(template.findall('include')):template.remove(include)
    for node in style:
        if template.find(node.tag) is None:template.append(deepcopy(node))
    for key,value in dict(left=1345,width=180,label='YouTube',textoffsetx=24,onleft=134,onright=135,
        onup=136,ondown=121,onclick='ActivateWindow(Videos,"plugin://plugin.video.youtube/",return)').items():field(template,key,value)
    group.append(template)
    image=ET.SubElement(group,'control',dict(type='image'))
    for key,value in dict(left=1353,top=40,width=28,height=28,
        texture='special://home/addons/plugin.video.youtube/resources/media/icon.png',aspectratio='keep').items():field(image,key,value)
    search=group.find("control[@id='135']")
    field(search,'left',1540);field(search,'onleft',136);field(search,'onright',130)
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def browser_rail(data):
    root=ET.fromstring(data);controls=root.find('controls')
    group=next(g for g in controls.findall('control') if g.find("control[@id='9007']") is not None)
    # Remove only this legacy rail's decorative marks (not page artwork).
    for image in list(controls.findall("control[@type='image']")):
        if image.findtext('left')=='36' and image.findtext('width')=='44':controls.remove(image)
    for child in list(group):
        if child.tag=='control' and (child.get('type')=='button' or child.findtext('aspectratio')=='keep'):group.remove(child)
    field(group,'width',250)
    backgrounds=group.findall("control[@type='image']")
    for image in backgrounds:
        field(image,'width',250 if image.findtext('left')=='0' else 248)
    for index,(identity,title,icon) in enumerate(DESTINATIONS):
        top=119+index*64
        closed=ET.SubElement(controls,'control',dict(type='image'))
        for k,v in dict(left=36,top=230+top+9,width=44,height=44,
            texture='special://home/addons/skin.asterhome/media/'+icon,aspectratio='keep',
            visible='!String.IsEqual(Window.Property(Lab.Rail),true)').items():field(closed,k,v)
        button=ET.SubElement(group,'control',dict(type='button',id=str(identity)))
        for k,v in dict(left=62,top=top,width=178,height=62,label=title,font='font20',textcolor='fff3eee5',
            focusedcolor='ff91c6a2',align='left',aligny='center',texturefocus='',texturenofocus='',
            onleft=identity,onright=identity,onup=identity,ondown=identity).items():field(button,k,v)
        image=ET.SubElement(group,'control',dict(type='image'))
        for k,v in dict(left=14,top=top+13,width=36,height=36,texture='special://home/addons/skin.asterhome/media/'+icon,
            aspectratio='keep').items():field(image,k,v)
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def search_hero(data):
    root=ET.fromstring(data);controls=root.find('controls')
    template=ET.parse(Path(__file__).resolve().parent/'search_native/overlay/custom_1128_searchdetails.xml')
    for index,image in enumerate(template.getroot().find('controls').findall('control')[1:4],start=1):
        controls.insert(index,deepcopy(image))
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)
