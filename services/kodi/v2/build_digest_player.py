"""Immutable staged player; no normal News installation or profile changes."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def xml(here):
    root = ET.parse(here / 'digest_preview/resources/skins/Default/1080i/DigestPreview.xml').getroot()
    controls = root.find('controls')
    for control in list(controls):
        if control.get('id') in ('201', '202') or control.findtext('texture') in ('previous.png', 'next.png'):
            controls.remove(control)
    for control in controls.findall('control'):
        if control.findtext('label') == 'Briefing timeline': control.find('label').text = 'Briefing stories'
    for identity, left, label, icon, previous, following in (
            ('201', 265, 'Previous story', 'previous', '300', '203'),
            ('203', 365, 'Play or pause briefing', 'play', '201', '202'),
            ('202', 465, 'Next story', 'next', '203', '204'),
            ('204', 565, 'Stop briefing', 'stop', '202', '300')):
        control = ET.SubElement(controls, 'control', type='button', id=identity)
        for key, value in dict(left=str(left), top='950', width='64', height='64', label=label,
                textcolor='00000000', focusedcolor='00000000', texturenofocus='', onleft=previous,
                onright=following, onup='300').items(): ET.SubElement(control, key).text = value
        ET.SubElement(control, 'texturefocus', border='18', colordiffuse='ffd8b778').text = 'special://skin/media/ui-button-ring.png'
        if identity in ('201', '202'):
            flag = 'First' if identity == '201' else 'Last'
            ET.SubElement(control, 'enable').text = '!String.IsEqual(Window.Property(Digest.'+flag+'),true)'
        for name in (('play', 'pause') if icon == 'play' else (icon,)):
            image = ET.SubElement(controls, 'control', type='image')
            for key, value in dict(left=str(left+8), top='958', width='48', height='48',
                    texture=name+'.png', aspectratio='keep', colordiffuse='fff3eee5').items():
                ET.SubElement(image, key).text = value
            if icon == 'play':
                condition = 'String.IsEqual(Window.Property(Digest.Playing),true) + !String.IsEqual(Window.Property(Digest.Paused),true)'
                ET.SubElement(image, 'visible').text = condition if name == 'pause' else '!['+condition+']'
    listing = root.find(".//control[@id='300']")
    listing.find('onleft').text = '203'
    layout = listing.find('itemlayout')
    active = ET.Element('control', type='image')
    for key, value in dict(left='2', top='3', width='940', height='100',
            visible='String.IsEqual(ListItem.Property(Active),true)').items(): ET.SubElement(active, key).text = value
    ET.SubElement(active, 'texture', border='20', colordiffuse='b0005c46').text = 'special://skin/media/ui-panel.png'
    layout.insert(1, active)
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def build(output):
    here = Path(__file__).resolve().parent
    output = Path(output)
    if output.exists(): raise ValueError('immutable-player-output')
    files = {'default.py':(here / 'digest_player/default.py').read_bytes(),
        'resources/skins/Default/1080i/DigestPlayer.xml':xml(here)}
    for name in ('digest_timeline', 'digest_playback_state', 'digest_player_adapter', 'digest_kodi_port',
            'digest_player_model', 'digest_preview_model', 'digest_news_contract'):
        files['resources/lib/'+name+'.py'] = (here / (name+'.py')).read_bytes()
    files['resources/lib/digest_data.py'] = (here.parent / 'skin.asterhome/tools/digest_data.py').read_bytes()
    files['resources/lib/digest_preview_source.py'] = (here / 'digest_preview/default.py').read_bytes()
    files['resources/lib/deploy_startup.py'] = (here / 'tools/deploy_startup.py').read_bytes()
    for name in ('play', 'pause', 'stop', 'previous', 'next'):
        source = (here / 'player-control-assets/previous.png' if name == 'previous' else
            here / 'script.astermusic.v2lab/resources/controls' / ('page-next.png' if name == 'next' else name+'.png'))
        files['resources/skins/Default/media/'+name+'.png'] = source.read_bytes()
    records = []
    for name, data in sorted(files.items()):
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        records.append(dict(path=name, sha256=hashlib.sha256(data).hexdigest()))
    raw = (json.dumps(dict(kind='hp-digest-player.v1', normal_news=False, files=records), indent=2)+'\n').encode()
    (output / 'manifest.json').write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    print(build(parser.parse_args().output))
