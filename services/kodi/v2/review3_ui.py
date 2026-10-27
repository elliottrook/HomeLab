"""Third household visual pass: fitted rails, lighter glass and tactile keys."""
from copy import deepcopy
import xml.etree.ElementTree as ET
from review2_ui import field,encoded

PANEL='special://skin/media/ui-panel.png'
RING='special://skin/media/ui-compact-card-ring.png'
def image(parent,x,y,w,h,colour,*,ring=False,visible=None):
    node=ET.SubElement(parent,'control',dict(type='image'))
    for k,v in dict(left=x,top=y,width=w,height=h).items():field(node,k,v)
    tex=ET.SubElement(node,'texture',dict(border='18',colordiffuse=colour));tex.text=RING if ring else PANEL
    if visible:field(node,'visible',visible)
    return node
def button_style(node):
    for k,v in dict(textcolor='fff3eee5',focusedcolor='fff3eee5',aligny='center').items():field(node,k,v)
    for tag,colour in (('texturefocus','ff005c46'),('texturenofocus','99000000')):
        field(node,tag,PANEL);node.find(tag).attrib.update(border='18',colordiffuse=colour)
def top_pills(data):
    root=ET.fromstring(data)
    for include in root.findall('include'):
        if include.get('name') in ('AsterTopCategoryButton','AsterMusicPillButton'):
            button_style(include)
    for parent in list(root.iter()):
        buttons=[]
        for c in parent.findall('control[@type="button"]'):
            top=c.findtext('top','');left=c.findtext('left','')
            if top.isdecimal() and int(top)<=100 and left.isdecimal() and int(left)>=300:
                buttons.append(c)
        if not buttons:continue
        positions={(str(int(b.findtext('left'))+dx),str(int(b.findtext('top'))+dy))
                   for b in buttons for dx,dy in ((0,0),(-3,-3))}
        # Retire old decorative focus/active fills that would cover the new
        # focus border or duplicate a label. Icons and clocks are retained.
        for c in list(parent.findall('control')):
            if c in buttons:continue
            if c.get('type') in ('image','label') and (c.findtext('left'),c.findtext('top')) in positions:
                if c.find('visible') is not None and (c.get('type')=='label' or any(t in (c.findtext('texture') or '') for t in ('ui-panel.png','ui-top-button-ring.png','ui-button-ring.png','ui-compact-card-ring.png'))):parent.remove(c)
        for b in buttons:
            for inc in list(b.findall('include')):
                if inc.text in ('AsterMusicPillButton','AsterTopCategoryButton'):
                    defaults=next((n for n in root.findall('include') if n.get('name')==inc.text),None)
                    if defaults is None:
                        defaults=ET.Element('defaults')
                        for k,v in dict(width=200 if inc.text=='AsterMusicPillButton' else 210,height=50 if inc.text=='AsterMusicPillButton' else 46,font='font20',ondown=120).items():field(defaults,k,v)
                    for n in defaults:
                        if b.find(n.tag) is None:b.append(deepcopy(n))
                    b.remove(inc)
            button_style(b)
            width=b.findtext('width') or ('200' if b.findtext('include')=='AsterMusicPillButton' else '180')
            height=b.findtext('height') or ('50' if b.findtext('include')=='AsterMusicPillButton' else '46')
            if not width.isdecimal() or not height.isdecimal():continue
            x,y,w,h=int(b.findtext('left')),int(b.findtext('top')),int(width),int(height)
            icon=any(c.get('type')=='image' and c.findtext('left') in (str(x+8),str(x+10),str(x+12))
                and c.findtext('width') in ('28','36') for c in parent.findall('control'))
            # Kodi reserves textoffsetx on BOTH sides. Draw icon captions in
            # their own explicit column instead of spending two icon insets.
            field(b,'textoffsetx',0);field(b,'align','center')
            if icon:
                field(b,'textcolor','00000000');field(b,'focusedcolor','00000000')
                label=ET.SubElement(parent,'control',dict(type='label'))
                for k,v in dict(left=x+48,top=y,width=w-58,height=h,label=b.findtext('label'),font=b.findtext('font') or 'font20',
                    textcolor='fff3eee5',align='left',aligny='center',truncate='true',visible='Control.IsVisible('+b.get('id')+')').items():field(label,k,v)
            image(parent,int(b.findtext('left'))-1,int(b.findtext('top'))-1,int(width)+2,int(height)+2,
                  'fff3eee5',ring=True,visible='Control.HasFocus('+b.get('id')+')')
    return encoded(root)

def media_header(data):
    root=ET.fromstring(data);group=next(g for g in root.iter('control') if g.find('control[@id="136"]') is not None)
    # Replace the shared slab with a correctly fitted navigation capsule;
    # Search has the clock's restrained gold-edged capsule and a deliberate
    # 30px separation from the category rail.
    buttons={i:group.find(f'control[@id="{i}"]') for i in (135,130,131,132,133,134,136)}
    for c in list(group.findall('control[@type="image"]')):
        texture=c.findtext('texture') or ''
        if any(n in texture for n in ('ui-panel.png','ui-compact-card-ring.png','ui-button-ring.png','ui-top-button-ring.png')) and c.findtext('top') not in ('0',):group.remove(c)
    widths=(170,150,180,220,180,180);left=550
    icons={}
    for i in (130,131,132,133,134,136):
        old=int(buttons[i].findtext('left'))
        candidates=[c for c in group.findall('control[@type="image"]') if c.findtext('left') in (str(old+8),str(old+12))]
        if len(candidates)!=1:raise ValueError('one-header-icon:'+str(i))
        icons[i]=candidates[0]
    for i,width in zip((130,131,132,133,134,136),widths):
        b=buttons[i]
        for k,v in dict(left=left,top=31,width=width,height=46,align='left',textoffsetx=48,font='font20').items():field(b,k,v)
        if i==133:field(b,'label','Archive Movies')
        for k,v in dict(left=left+10,top=40,width=28,height=28).items():field(icons[i],k,v)
        left+=width+12
    search=buttons[135]
    for k,v in dict(left=350,top=31,width=170,height=46,align='center',textoffsetx=0).items():field(search,k,v)
    # Insert backplates before controls so they never overlay text/icons.
    wrapper=ET.Element('holder')
    image(wrapper,542,23,left-12-542+8,62,'52000000')
    image(wrapper,348,29,174,50,'75cbb991',ring=True)
    for n in reversed(list(wrapper)):group.insert(0,n)
    return top_pills(encoded(root))

def shorter_rail(data):
    root=ET.fromstring(data)
    definition=root.find('include[@name="AsterNavigationRail"]/definition')
    for identity in ('9000','9006'):
        group=definition.find('control[@id="'+identity+'"]')
        # Six 64px rows plus 16px padding at each end; centred on the screen.
        field(group,'top',332);field(group,'height',416)
        for c in group.findall('control'):
            if c.get('type')=='button':
                if c.get('id')=='8999':field(c,'height',416)
                elif c.findtext('top','').isdecimal():field(c,'top',int(c.findtext('top'))-103)
            elif c.findtext('height') in ('620','618'):
                field(c,'height',416 if c.findtext('height')=='620' else 414)
            elif c.get('type')=='image' and c.findtext('top','').isdecimal() and int(c.findtext('top'))>100:
                field(c,'top',int(c.findtext('top'))-103)
    return encoded(root)

def shorter_browser_rail(data):
    root=ET.fromstring(data);controls=root.find('controls')
    group=next(g for g in controls.findall('control') if g.find('control[@id="9007"]') is not None)
    field(group,'top',332);field(group,'height',416)
    for c in group.findall('control'):
        if c.findtext('height') in ('620','618'):field(c,'height',416 if c.findtext('height')=='620' else 414)
        elif c.findtext('top','').isdecimal() and int(c.findtext('top'))>=119:field(c,'top',int(c.findtext('top'))-103)
    for c in controls.findall('control[@type="image"]'):
        if c.findtext('left')=='36' and c.findtext('width')=='44':field(c,'top',int(c.findtext('top'))-1)
    return encoded(root)

def lighter_menus(data):
    root=ET.fromstring(data)
    for c in root.iter('control'):
        tex=c.find('texture')
        if tex is not None and tex.get('colordiffuse')=='df000000':tex.set('colordiffuse','98000000')
        if c.findtext('colordiffuse')=='df000000':field(c,'colordiffuse','98000000')
    return encoded(root)

def books_clock(data):
    root=ET.fromstring(data)
    for c in root.iter('control'):
        if c.findtext('label') in ('$INFO[Player.Time(hh:mm:ss)]','$INFO[Player.Duration(hh:mm:ss)]'):
            field(c,'textcolor','asterGreen')
    return encoded(root)

def keyboard(data):
    root=ET.fromstring(lighter_menus(data));parents={c:p for p in root.iter() for c in p}
    for b in list(root.iter('control')):
        if b.get('type')!='button':continue
        if not all((b.findtext(k) or '').isdecimal() for k in ('left','top')):continue
        x,y=int(b.findtext('left')),int(b.findtext('top'))
        w,h=int(b.findtext('width') or '190'),int(b.findtext('height') or '56')
        for include in list(b.findall('include')):
            if include.text=='AsterKeyboardActionButton':
                b.remove(include)
                for k,v in dict(width=w,height=h,font='font24',aligny='center').items():field(b,k,v)
        button_style(b)
        b.find('texturenofocus').set('colordiffuse','bd353e37')
        field(b,'align','center');field(b,'textoffsetx',0)
        parent=parents[b];at=list(parent).index(b);holder=ET.Element('holder')
        image(holder,x,y+3,w,h+2,'65000000')
        image(holder,x-1,y-1,w+2,h+2,'35f3eee5',ring=True)
        image(holder,x-1,y-1,w+2,h+2,'fff3eee5',ring=True,visible='Control.HasFocus('+b.get('id')+')')
        for offset,c in enumerate(list(holder)):parent.insert(at+offset,c)
    return encoded(root)
