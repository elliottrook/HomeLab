"""One fitted floating header for all Aster landing pages; no service writes."""
import xml.etree.ElementTree as ET
from review2_ui import field,encoded
from review3_ui import image,button_style

SEARCH='RunScript(/storage/.aster-staging/aster-global-search-ui22/default.py)'

def header(data,ids,widths,down,*,compact=False):
    root=ET.fromstring(data)
    group=next(g for g in root.iter() if g.find('control[@id="'+str(ids[0])+'"]') is not None)
    buttons=[group.find('control[@id="'+str(i)+'"]') for i in ids]
    icons={}
    for b in buttons:
        x=int(b.findtext('left'));icons[b.get('id')]=next((c for c in group.findall('control[@type="image"]')
            if c.findtext('left') in (str(x+8),str(x+10),str(x+12)) and c.findtext('width') in ('28','36')),None)
    for parent in root.iter():
        for c in list(parent.findall('control')):
            x,y,w,h=(c.findtext(k,'') for k in ('left','top','width','height'))
            if c.get('type')=='image' and x=='110' and y=='0' and w=='240':field(c,'height',160)
            texture=c.findtext('texture','')
            slab=c.get('type')=='image' and w.isdecimal() and h.isdecimal() and y in ('0','') and int(w)>1500 and 100<=int(h)<=180
            decoration=parent is group and c not in buttons and c not in icons.values() and c.get('type') in ('image','label') and (
                y.isdecimal() and int(y)<=152 and (c.get('type')=='label' or 'ui-panel.png' in texture or 'ring.png' in texture or h=='4'))
            if slab or decoration:parent.remove(c)
    search=ET.SubElement(group,'control',dict(type='button',id='139'))
    for k,v in dict(left=350,top=31,width=170,height=46,label='Search',font='font20',align='center',aligny='center',
        onleft=8999,onright=ids[0],onup=139,ondown=down,enable='!Player.HasMedia',onclick=SEARCH).items():field(search,k,v)
    button_style(search)
    left=550
    for n,(b,width) in enumerate(zip(buttons,widths)):
        for inc in list(b.findall('include')):b.remove(inc)
        for k,v in dict(left=left,top=31,width=width,height=46,font='font20',
            onleft=ids[n-1] if n else 139,onright=ids[n+1] if n+1<len(ids) else 139,onup=ids[n],ondown=down,
            align='center',textoffsetx=0).items():field(b,k,v)
        button_style(b);icon=icons[b.get('id')]
        if icon is not None:
            for k,v in dict(left=left+10,top=40,width=28,height=28).items():field(icon,k,v)
            field(b,'textcolor','00000000');field(b,'focusedcolor','00000000')
            label=ET.SubElement(group,'control',dict(type='label'))
            for k,v in dict(left=left+48,top=31,width=width-58,height=46,label=b.findtext('label'),font='font20',align='left',aligny='center',
                textcolor='fff3eee5',truncate='true',visible='Control.IsVisible('+b.get('id')+')').items():field(label,k,v)
        image(group,left-1,30,width+2,48,'fff3eee5',ring=True,visible='Control.HasFocus('+b.get('id')+')')
        left+=width+12
    holder=ET.Element('holder')
    image(holder,542,23,left-12-542+8,62,'52000000')
    image(holder,348,29,174,50,'ffad8a4d',ring=True)
    image(group,349,30,172,48,'fff3eee5',ring=True,visible='Control.HasFocus(139)')
    for node in reversed(list(holder)):group.insert(0,node)
    return encoded(root)

def settings(data):
    old=ET.fromstring(data);items=old.findall('.//content/item')
    root=ET.Element('window',dict(id='4'));field(root,'defaultcontrol',200);field(root,'backgroundcolor','asterStone')
    controls=ET.SubElement(root,'controls')
    rail=ET.SubElement(controls,'include',dict(content='AsterNavigationRail'))
    ET.SubElement(rail,'param',dict(name='content',value='200'));ET.SubElement(rail,'param',dict(name='railfocus',value='9005'))
    group=ET.SubElement(controls,'control',dict(type='group'))
    field(group,'visible','!Control.HasFocus(8999) + !Control.HasFocus(9001) + !Control.HasFocus(9002) + !Control.HasFocus(9003) + !Control.HasFocus(9004) + !Control.HasFocus(9005) + !Control.HasFocus(9007)')
    logo=ET.SubElement(group,'control',dict(type='image'))
    for k,v in dict(left=110,top=0,width=240,height=160,texture='special://skin/media/aster-compass-128.png',aspectratio='keep').items():field(logo,k,v)
    for index,item in enumerate(items):
        button=ET.SubElement(group,'control',dict(type='button',id=str(200+index)))
        for k,v in dict(left=550+index*125,top=31,label=item.findtext('label'),onclick=item.findtext('onclick')).items():field(button,k,v)
        if item.find('visible') is not None:
            field(button,'enable',item.findtext('visible'));field(button,'disabledcolor','ff96988f')
    ET.SubElement(group,'include',dict(content='AsterClockPill'))
    def label(x,y,w,h,text,font='font24',colour='asterInk'):
        node=ET.SubElement(group,'control',dict(type='label'))
        for k,v in dict(left=x,top=y,width=w,height=h,label=text,font=font,textcolor=colour,truncate='true').items():field(node,k,v)
    label(145,220,1650,60,'Current status','font40')
    label(145,286,1650,40,'Live local information · read-only','font20','asterMuted')
    rows=(('Device','$INFO[System.FriendlyName]'),('Kodi','$INFO[System.BuildVersion]'),
        ('Display','$INFO[System.ScreenResolution]'),('Network address','$INFO[Network.IPAddress]'),
        ('Available memory','$INFO[System.FreeMemory]'),('Uptime','$INFO[System.Uptime]'))
    for i,(title,value) in enumerate(rows):
        x=145+(i%2)*830;y=390+(i//2)*175
        label(x,y,750,36,title,'font20','asterMuted');label(x,y+43,750,65,value,'font28')
    label(145,990,1650,34,'Choose a settings area above · Left opens the navigation rail','font20','asterMuted')
    return header(encoded(root),list(range(200,208)),[110,100,110,110,160,180,130,100],200,compact=True)

def extend_search(data):
    source=data.decode()
    needle="        require(xbmcgui.getCurrentWindowId()==10000 and not rpc('Player.GetActivePlayers'),'idle-home-required')\n        source_focus=home.getFocusId()"
    replacement="""        source_window=xbmcgui.getCurrentWindowId()
        require(source_window in (10000,10004,11110,11111,11112,11113,11114,11115,11116,11117,11118,11119,11120,11122) and not rpc('Player.GetActivePlayers'),'idle-known-page-required')
        source_target='Home' if source_window==10000 else str(source_window-10000)
        source_focus=xbmcgui.Window(source_window).getFocusId()"""
    if source.count(needle)!=1:raise ValueError('search-source-drift')
    source=source.replace(needle,replacement).replace("xbmc.executebuiltin('ActivateWindow(Home)')","xbmc.executebuiltin('ActivateWindow('+source_target+')')")
    source=source.replace('source_focus and xbmcgui.getCurrentWindowId()==10000','source_focus and xbmcgui.getCurrentWindowId()==source_window')
    return source.encode()
