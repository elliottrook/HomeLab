"""Code-native Home visual trial: floating jewel-toned surfaces and brush arc."""
import math
import xml.etree.ElementTree as ET
from review2_ui import field,encoded

MEDIA='special://skin/media/aster-home-layered-v1/'
PALETTES=(('#233d3b','#152927','#a9d6be'),('#304254','#1c2b40','#a8c9e6'),
          ('#463c51','#2b273a','#c8b4da'),('#514536','#302c25','#d8b77e'))

def background_svg():
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080"><defs>
    <linearGradient id="base" x2=".9" y2="1"><stop stop-color="#27333d"/><stop offset=".5" stop-color="#121c29"/><stop offset="1" stop-color="#0c1420"/></linearGradient>
    <radialGradient id="gold"><stop stop-color="#c8a46a" stop-opacity=".16"/><stop offset="1" stop-color="#c8a46a" stop-opacity="0"/></radialGradient>
    <radialGradient id="teal"><stop stop-color="#589e90" stop-opacity=".12"/><stop offset="1" stop-color="#589e90" stop-opacity="0"/></radialGradient>
    </defs><rect width="1920" height="1080" fill="url(#base)"/><ellipse cx="240" cy="70" rx="900" ry="700" fill="url(#gold)"/>
    <ellipse cx="1600" cy="730" rx="800" ry="750" fill="url(#teal)"/></svg>'''

def panel_svg(width,height,colours,radius=28):
    first,last,accent=colours
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><defs>
    <linearGradient id="body" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{first}"/><stop offset="1" stop-color="{last}"/></linearGradient>
    <linearGradient id="edge" x1="0" y1="0" x2=".7" y2="1"><stop stop-color="{accent}" stop-opacity=".6"/><stop offset=".5" stop-color="{accent}" stop-opacity=".12"/><stop offset="1" stop-color="{accent}" stop-opacity=".3"/></linearGradient>
    </defs><rect x="2" y="5" width="{width-4}" height="{height-6}" rx="{radius}" fill="#000" fill-opacity=".25"/>
    <rect x=".8" y=".8" width="{width-1.6}" height="{height-5}" rx="{radius}" fill="url(#body)" stroke="url(#edge)" stroke-width="1.3"/>
    <path d="M{radius+10} 2 H{width-radius-10}" stroke="{accent}" stroke-opacity=".25" stroke-width="1"/></svg>'''

def brush_svg(seconds):
    if type(seconds) is not int or not 0<=seconds<=60:raise ValueError('home-brush-seconds')
    start=-math.pi/2;sweep=2*math.pi*seconds/60
    def point(angle,radius):return f'{256+math.cos(angle)*radius:.3f},{256+math.sin(angle)*radius:.3f}'
    ink=''
    if seconds:
        steps=max(12,seconds*8)
        angles=[start+sweep*i/steps for i in range(steps+1)]
        outer=[];inner=[]
        for i,a in enumerate(angles):
            t=i/steps
            taper=min(1,.22+t*14,.16+(1-t)*18)
            width=(6.5+1.3*math.sin(a*11)+.6*math.sin(a*29))*taper
            radius=226+.8*math.sin(a*17)+.45*math.sin(a*37)
            outer.append(point(a,radius+width));inner.append(point(a,radius-width))
        ink='<polygon points="'+' '.join(outer+inner[::-1])+'" fill="url(#ink)"/>'
        # Separate fine bristles create a dry brushed edge without random
        # animation/noise. Every frame is a deterministic clipped prefix.
        for j,(offset,opacity) in enumerate(((-6,.33),(-3,.25),(1.8,.52),(5,.30),(7.2,.18))):
            points=[point(a,226+offset+.65*math.sin(a*(19+j*2)+j)+.25*math.sin(a*43)) for a in angles]
            ink+='<polyline points="'+' '.join(points)+f'" fill="none" stroke="#d1ead4" stroke-opacity="{opacity}" stroke-width="{.5 if j%2 else .8}"/>'
        # Warm glint at the outer edge, not another competing countdown.
        glint=[point(a,237+.35*math.sin(a*9)) for a in angles[::2]]
        ink+='<polyline points="'+' '.join(glint)+'" fill="none" stroke="#c7ab73" stroke-opacity=".35" stroke-width=".6"/>'
    return ('''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512"><defs>
    <linearGradient id="ink" x1=".1" y1="1" x2=".9" y2="0"><stop stop-color="#4e9e89"/><stop offset=".45" stop-color="#85cba9"/><stop offset="1" stop-color="#c2e1ba"/></linearGradient>
    </defs><circle cx="256" cy="256" r="226" fill="none" stroke="#97b4ab" stroke-opacity=".18" stroke-width="8"/>
    <circle cx="256" cy="256" r="211" fill="none" stroke="#b7a27a" stroke-opacity=".2" stroke-width=".7"/>'''+ink+'</svg>\n')

def build(data):
    root=ET.fromstring(data)
    if root.get('id')!='1112' or 'aster-home-status1/default.py' not in root.findtext('onload',''):
        raise ValueError('home-layered-predecessor')
    field(root,'backgroundcolor','ff101a26')
    for node in root.iter('control'):
        kind=node.get('type');left=node.findtext('left');top=node.findtext('top');width=node.findtext('width');height=node.findtext('height')
        texture=node.find('texture')
        if kind=='image' and texture is not None:
            if (left,top,width,height)==('0','0','1920','1080'):
                texture.text=MEDIA+'background.png';texture.attrib.clear();field(node,'colordiffuse','ffffffff')
            elif top=='282' and width=='395':
                index=('145','560','975','1390').index(left)
                texture.text=MEDIA+f'metric-{index}.png';texture.attrib.clear()
            elif (left,top,width,height)==('655','490','560','510'):
                texture.text=MEDIA+'camera-panel.png';texture.attrib.clear()
            elif (left,top,width,height)==('1240','490','550','510'):
                texture.text=MEDIA+'timer-panel.png';texture.attrib.clear()
            elif 'aster-home-timer-v2/arc-' in (texture.text or ''):
                texture.text=texture.text.replace('aster-home-timer-v2/','aster-home-layered-v1/')
                if 'fallback' in texture.attrib:texture.set('fallback',MEDIA+'arc-0.png')
        if kind=='label' and node.findtext('textcolor') in ('asterInk','asterMuted'):
            field(node,'textcolor','fff3eee5' if node.findtext('textcolor')=='asterInk' else 'ffb7c1cb')
    listing=root.find('.//control[@id="500"]')
    for layout in listing:
        if layout.tag not in ('itemlayout','focusedlayout'):continue
        for node in layout.findall('control[@type="image"]'):
            texture=node.find('texture')
            if texture is not None and 'ui-panel.png' in (texture.text or ''):
                texture.text=MEDIA+('row-focus.png' if layout.tag=='focusedlayout' else 'row.png');texture.attrib.clear()
    # Quiet metadata accents distinguish the floating summary pills.
    for index,left in enumerate((169,584,999,1414)):
        for label in root.iter('control'):
            if label.get('type')=='label' and label.findtext('left')==str(left) and label.findtext('top')=='296':
                field(label,'textcolor','ff'+PALETTES[index][2].lstrip('#'))
    return encoded(root)
