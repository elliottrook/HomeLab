"""Home's presentation-only successor: existing HA reader, camera and timer.

The arc is explicitly a seconds sweep, matching HomeTimerSecond (0..60),
not a misleading claim about the fraction of the entire timer remaining.
"""
import math
import xml.etree.ElementTree as ET
from review2_ui import field, encoded
from review3_ui import image, button_style
from branding_rails import header

MEDIA = 'special://skin/media/aster-home-timer-v2/'


def arc_svg(seconds):
    if type(seconds) is not int or not 0 <= seconds <= 60:
        raise ValueError('home-arc-seconds')
    length = 2 * math.pi * 226
    arc = '' if seconds == 0 else (
        '<circle cx="256" cy="256" r="226" fill="none" stroke="#9bc9ac" '
        'stroke-width="5" stroke-linecap="round" '
        f'stroke-dasharray="{length * seconds / 60:.6f} {length:.6f}" '
        'transform="rotate(-90 256 256)"/>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" '
            'viewBox="0 0 512 512"><circle cx="256" cy="256" r="226" '
            'fill="none" stroke="#ffffff" stroke-opacity=".14" stroke-width="3"/>'
            + arc + '</svg>\n')


def control(parent, kind, x, y, w, h, **values):
    node = ET.SubElement(parent, 'control', {'type': kind})
    for key, value in dict(left=x, top=y, width=w, height=h, **values).items():
        field(node, key, value)
    return node


def label(parent, x, y, w, h, text, font='font20', colour='asterInk', **extra):
    return control(parent, 'label', x, y, w, h, label=text, font=font,
                   textcolor=colour, aligny='center', truncate='true', **extra)


def button(parent, identity, x, y, w, text, action, left, right, up, down):
    node = control(parent, 'button', x, y, w, 48, label=text, font='font20',
                   align='center', aligny='center', onclick=action,
                   onleft=left, onright=right, onup=up, ondown=down)
    node.set('id', str(identity))
    button_style(node)
    image(parent, x-1, y-1, w+2, 50, 'fff3eee5', ring=True,
          visible=f'Control.HasFocus({identity})')
    return node


def build(data):
    old = ET.fromstring(data)
    # Refuse a different page or an already transformed successor.
    if old.get('id') != '1112' or old.find('.//include[@content="AsterTimerRing"]') is None:
        raise ValueError('home-design-predecessor')
    root = ET.Element('window', old.attrib)
    field(root, 'defaultcontrol', 301)
    root.find('defaultcontrol').set('always', 'true')
    for tag in ('onload', 'onunload', 'backgroundcolor'):
        field(root, tag, old.findtext(tag))
    controls = ET.SubElement(root, 'controls')
    controls.append(old.find('controls/control[@type="image"]'))
    rail = old.find('controls/include[@content="AsterNavigationRail"]')
    rail.find('param[@name="content"]').set('value', '301')
    controls.append(rail)
    group = ET.SubElement(controls, 'control', {'type': 'group'})
    field(group, 'visible', old.findtext('controls/control[@type="group"]/visible'))
    group.append(old.find('.//control[texture="special://skin/media/aster-home-horizontal-512.png"]'))
    ET.SubElement(group, 'include', {'content': 'AsterClockPill'})
    ids = [301, 307, 308, 309, 300]
    names = ['Overview', 'Lighting', 'Cameras', 'Timers', 'Refresh']
    targets = [500, 500, 302, 304]
    for index, (identity, name) in enumerate(zip(ids, names)):
        action = (f'Control.SetFocus({targets[index]})' if index < 4 else
                  'RunScript(special://skin/tools/hub_data.py,home)')
        button(group, identity, 550+index*168, 31, 156, name, action, 139, 139, identity, 500)
    label(group, 145, 171, 1250, 58, 'Your home, at a glance.', 'font40')
    label(group, 145, 226, 1250, 32, 'Household status · Private cameras · Local timer', 'font20', 'asterMuted')
    metrics = [('LightLabel', 'LightValue'), ('TemperatureLabel', 'TemperatureValue'),
               ('CameraLabel', 'CameraStatus'), ('WeatherLabel', 'WeatherValue')]
    for index, (title, value) in enumerate(metrics):
        x = 145+415*index
        image(group, x, 282, 395, 116, '55f3eee5')
        label(group, x+24, 296, 347, 32, '$INFO[Window.Property(AsterHub.Home'+title+')]', colour='asterMuted')
        label(group, x+24, 332, 347, 50, '$INFO[Window.Property(AsterHub.Home'+value+')]', 'font28')
        if title == 'WeatherLabel':
            label(group,x+24,296,347,32,'Weather',colour='asterMuted',
                  visible='String.IsEmpty(Window.Property(AsterHub.HomeWeatherLabel))')
            label(group,x+24,332,347,50,'Unavailable','font28',
                  visible='String.IsEmpty(Window.Property(AsterHub.HomeWeatherValue))')
    for x, w, title in ((145,480,'Household'), (655,560,'Camera'), (1240,550,'Timer')):
        label(group, x, 425, w, 44, title, 'font28')
    # Existing read-only rows, now the natural first focus destination.
    listing = old.find('.//control[@id="500"]')
    for key, value in dict(left=145, top=490, width=480, height=432, onup=301,
                           onleft=8999, onright=302, onclick='noop').items():
        field(listing, key, value)
    for layout in listing:
        if layout.tag not in ('itemlayout', 'focusedlayout'):
            continue
        layout.set('width', '480'); layout.set('height', '108')
        focused = layout.tag == 'focusedlayout'
        for child in list(layout): layout.remove(child)
        image(layout, 0, 0, 480, 98, 'ff005c46' if focused else '35f3eee5')
        if focused: image(layout, 0, 0, 480, 98, 'fff3eee5', ring=True)
        label(layout, 24, 12, 432, 36, '$INFO[ListItem.Label]', colour='asterIvory' if focused else 'asterInk')
        label(layout, 24, 51, 432, 32, '$INFO[ListItem.Label2]', 'font20', 'asterIvory' if focused else 'asterMuted')
    group.append(listing)
    label(group, 145, 946, 480, 36, 'Read-only Home Assistant status', 'font20', 'asterMuted')
    image(group, 655, 490, 560, 510, 'ff1a211e')
    control(group, 'image', 680, 515, 510, 287,
            texture='special://skin/media/aster-compass-128.png', aspectratio='keep', colordiffuse='55ffffff',
            visible='!String.IsEqual(Window.Property(AsterHub.CameraPlaying),true)')
    control(group, 'image', 680, 515, 510, 287,
            texture='$INFO[Window.Property(AsterHub.CameraImage)]', aspectratio='keep',
            visible='String.IsEqual(Window.Property(AsterHub.CameraPlaying),true)').find('texture').set('background','true')
    label(group, 683, 826, 500, 42, '$INFO[Window.Property(AsterHub.HomeCameraLabel)]', 'font28', 'asterIvory')
    label(group, 683, 870, 500, 38, '$INFO[Window.Property(AsterHub.HomeCameraStatus)]', 'font20', 'asterSage')
    button(group, 302, 683, 932, 504, 'Live view',
           'RunScript(special://skin/tools/hub_data.py,home,camera)', 500, 303, 308, 302)
    image(group, 1240, 490, 550, 510, 'ff121815')
    active='String.IsEqual(Window.Property(AsterHub.HomeTimerActive),true)'
    control(group, 'image', 1315, 502, 400, 400,
            texture=MEDIA+'arc-$INFO[Window.Property(AsterHub.HomeTimerSecond)].png', aspectratio='keep',
            visible=active).find('texture').set('fallback',MEDIA+'arc-0.png')
    control(group,'image',1315,502,400,400,texture=MEDIA+'arc-0.png',aspectratio='keep',visible='!'+active)
    normal = '!String.IsEqual(Window.Property(AsterHub.HomeTimerExpired),true)'
    label(group, 1295, 617, 440, 116, '$INFO[Window.Property(AsterHub.HomeTimerDigital)]',
          'font80', 'asterIvory', align='center', visible=normal+' + '+active)
    label(group,1295,617,440,116,'--:--','font80','asterIvory',align='center',visible=normal+' + !'+active)
    label(group, 1315, 733, 400, 40, '$INFO[Window.Property(AsterHub.HomeTimerName)]',
          'font24', 'asterSage', align='center', visible=normal+' + '+active)
    label(group,1315,733,400,40,'Choose a duration','font24','asterSage',align='center',visible=normal+' + !'+active)
    label(group, 1315, 779, 400, 32, 'Seconds sweep', 'font16', 'ff89978e', align='center', visible=normal)
    done = 'String.IsEqual(Window.Property(AsterHub.HomeTimerExpired),true)'
    label(group, 1315, 617, 400, 100, '00:00', 'font80', 'asterSage', align='center', visible=done)
    label(group, 1315, 716, 400, 45, 'Timer complete', 'font24', 'asterIvory', align='center', visible=done)
    for index, (identity, name, action) in enumerate(((303,'1 minute','timer_1'),(304,'5 minutes','timer_5'),(305,'30 minutes','timer_30'))):
        button(group, identity, 1281+160*index, 932, 148, name,
               'RunScript(special://skin/tools/hub_data.py,home,'+action+')',
               identity-1, identity+1 if identity!=305 else 305, 306, identity)
    stop = button(group, 306, 1720, 506, 48, 'Stop timer',
                  'RunScript(special://skin/tools/hub_data.py,home,timer_stop)', 302, 306, 309, 304)
    field(stop, 'textcolor','00ffffff'); field(stop,'focusedcolor','00ffffff')
    stop.find('texturenofocus').set('colordiffuse','00ffffff')
    control(group,'image',1728,514,32,32,texture=MEDIA+'stop.png',aspectratio='keep')
    result = ET.fromstring(header(encoded(root), ids, [156]*5, 500))
    # Use the accepted normal-page search dispatcher, not a new parallel path.
    field(result.find('.//control[@id="139"]'),'onclick','RunScript(special://skin/tools/header_search.py)')
    # header() supplies its own focus rings; discard pre-header duplicates.
    seen = set()
    for parent in result.iter():
        for child in list(parent.findall('control[@type="image"]')):
            condition = child.findtext('visible')
            if condition in {f'Control.HasFocus({i})' for i in ids}:
                if condition in seen: parent.remove(child)
                else: seen.add(condition)
    return encoded(result)
