"""User's second visual review: quiet menus and unambiguous focus.

Pure transforms of pinned HP sources; the accepted side rail is not touched.
"""
import xml.etree.ElementTree as ET

def field(node,key,value):
    child=node.find(key)
    if child is None:child=ET.SubElement(node,key)
    child.text=str(value)
def encoded(root):return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def quiet_buttons(data):
    root=ET.fromstring(data)
    for node in root.iter():
        if node.tag in ('texturefocus','texturenofocus') and 'limestone' in (node.text or ''):
            node.text='special://skin/media/ui-panel.png';node.set('border','20')
            node.set('colordiffuse','ff91c6a2' if node.tag=='texturefocus' else 'e8f3eee5')
    return encoded(root)

def search_focus(data):
    root=ET.fromstring(data)
    for identity in (20,30):
        layout=root.find(f'.//control[@id="{identity}"]/focusedlayout')
        if layout is None:continue
        for image in layout.findall('control[@type="image"]'):
            field(image,'visible',f'Control.HasFocus({identity})')
        marker=ET.SubElement(layout,'control',dict(type='image'))
        for k,v in dict(left=4,top=12,width=5,height=46 if identity==20 else 74,
                        texture='special://skin/media/ui-solid.png',visible=f'Control.HasFocus({identity})').items():field(marker,k,v)
        marker.find('texture').set('colordiffuse','asterGreen')
    return encoded(root)

def header(data):
    root=ET.fromstring(data)
    group=next(g for g in root.iter('control') if g.find('control[@id="136"]') is not None)
    order=(135,130,131,132,133,134,136)
    old={i:int(group.find(f'control[@id="{i}"]/left').text) for i in order}
    for image in group.findall('control[@type="image"]'):
        left=image.findtext('left')
        for index,identity in enumerate(order):
            if left in (str(old[identity]),str(old[identity]+8),str(old[identity]+12)):
                field(image,'left',375+index*192+int(left)-old[identity]);break
    for index,identity in enumerate(order):
        button=group.find(f'control[@id="{identity}"]')
        for k,v in dict(left=375+index*192,width=180,onleft=order[index-1],
            onright=order[(index+1)%len(order)],align='center',aligny='center',
            textoffsetx=0 if identity==135 else 24).items():field(button,k,v)
    return encoded(root)

def osd(data):
    root=ET.fromstring(data)
    for identity,kind in ((7100,'audio'),(7101,'subtitles'),(7102,'quality')):
        button=root.find(f'.//control[@id="{identity}"]')
        for click in list(button.findall('onclick')):button.remove(click)
        field(button,'onclick','RunScript(special://skin/tools/osd_choices.py,'+kind+')')
    return encoded(root)

def keyboard(data):
    root=ET.fromstring(quiet_buttons(data));controls=root.find('controls')
    # The keyboard needs its key grid, but not a screen-covering dimmer.
    for image in list(controls.findall('control[@type="image"]')):
        if image.findtext('width')=='1920':controls.remove(image)
        else:
            image.find('texture').text='special://skin/media/ui-solid.png'
            field(image,'colordiffuse','df000000')
    for node in root.iter():
        if node.tag in ('textcolor','focusedcolor'):
            node.text='ff91c6a2' if node.tag=='focusedcolor' else 'fff3eee5'
        elif node.tag=='texturenofocus' and node.text not in (None,'none',''):
            node.text='special://skin/media/ui-panel.png';node.set('colordiffuse','402f3831')
        elif node.tag=='texturefocus':
            node.text='special://skin/media/ui-compact-card-ring.png';node.set('colordiffuse','ff91c6a2')
    return encoded(root)

def select_dialog(data):
    root=ET.fromstring(data);controls=root.find('controls')
    for image in list(controls.findall('control[@type="image"]')):controls.remove(image)
    group=controls.find('control[@type="group"]')
    for tag in ('centerleft','centertop'):
        node=group.find(tag)
        if node is not None:group.remove(node)
    for k,v in dict(left=1100,top=300,width=620,height=470).items():field(group,k,v)
    images=group.findall('control[@type="image"]')
    for image in images[1:]:group.remove(image)
    for k,v in dict(width=620,height=470,colordiffuse='df000000',texture='special://skin/media/ui-solid.png').items():field(images[0],k,v)
    label=group.find('control[@id="1"]')
    for k,v in dict(left=22,top=12,width=576,height=42,font='font20',textcolor='ffd2ab68').items():field(label,k,v)
    listing=group.find('control[@id="3"]')
    for k,v in dict(left=12,top=64,width=586,height=336).items():field(listing,k,v)
    for layout in (listing.find('itemlayout'),listing.find('focusedlayout')):
        layout.set('width','586');layout.set('height','48')
        for c in layout.findall('control'):
            check=c.findtext('label')=='✓'
            for k,v in dict(left=540 if check else 12,top=0,width=34 if check else 518,height=48).items():field(c,k,v)
            if c.get('type')=='image':
                field(c,'left',0);field(c,'width',580)
                c.find('texture').text='special://skin/media/ui-compact-card-ring.png';c.find('texture').set('colordiffuse','ff91c6a2')
            else:field(c,'textcolor','ff91c6a2' if layout.tag=='focusedlayout' or check else 'fff3eee5')
    scrollbar=group.find('control[@id="60"]')
    for k,v in dict(left=600,top=64,height=336).items():field(scrollbar,k,v)
    button=group.find('control[@id="5"]')
    for k,v in dict(left=180,top=410,width=260,height=48,textcolor='fff3eee5',focusedcolor='ff91c6a2',texturenofocus='',texturefocus='').items():field(button,k,v)
    return encoded(root)
