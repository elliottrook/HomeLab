#!/usr/bin/env python3
"""Fit the Aster YouTube synopsis and all three rows inside 1080 pixels."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path('/storage')
NAV = ROOT / '.kodi/addons/skin.asterhome/1080i/MyVideoNav.xml'
FAMILY = ROOT / '.kodi/addons/script.asterruntime/family-manifest.json'
CHECKPOINT = ROOT / '.aster-checkpoints/aster-youtube-production-compact1'
NAV_BEFORE = '4a6ae6fe83c8fdf03486446df0bb9a43377042a6bcbe9e2831b2cd4ed15e2079'
FAMILY_BEFORE = 'e20160b1b46783b879d80e9b7b677e5d3868df4b6f0bcd5dca44eaaefa8e5a44'
FOCUS = 'AlarmClock(AsterYouTubeLandingFocus,SetFocus(9530),00:03,silent)'

def sha(raw): return hashlib.sha256(raw).hexdigest()

def field(node, name, value):
    child = node.find(name)
    if child is None: raise RuntimeError('youtube-compact-missing-' + name)
    child.text = str(value)

def compact(raw):
    root = ET.fromstring(raw)
    loads = root.findall('onload')
    if (len(loads) != 1 or loads[0].text != FOCUS or
            loads[0].get('condition') !=
            'String.IsEqual(Container.FolderPath,plugin://plugin.video.youtube/)'):
        raise RuntimeError('youtube-compact-focus-predecessor')
    landing = root.find(".//control[@id='9891']")
    if landing is None: raise RuntimeError('youtube-compact-landing')
    headings = {'New from subscriptions': '390', 'Recommended': '590',
                'Watch later': '790'}
    seen = set()
    for label in landing.findall("control[@type='label']"):
        name = label.findtext('label')
        if name in headings and label.findtext('left') == '125':
            field(label, 'top', headings[name]); seen.add(name)
    if seen != set(headings): raise RuntimeError('youtube-compact-headings')
    positions = {'9530': '425', '9531': '625', '9532': '825'}
    for identity, top in positions.items():
        panel = landing.find(f"control[@id='{identity}']")
        if panel is None or panel.findtext('height') != '182':
            raise RuntimeError('youtube-compact-panel-' + identity)
        field(panel, 'top', top); field(panel, 'height', 160)
        for layout in (panel.find('itemlayout'), panel.find('focusedlayout')):
            if layout is None or layout.get('height') != '182':
                raise RuntimeError('youtube-compact-layout-' + identity)
            layout.set('height', '160')
            focused = layout.tag == 'focusedlayout'
            for image in layout.findall("control[@type='image']"):
                texture = image.findtext('texture') or ''
                if texture == '$INFO[ListItem.Art(thumb)]':
                    field(image, 'height', 124 if focused else 116)
                elif 'ui-compact-card-ring.png' in texture:
                    field(image, 'height', 136 if image.findtext('left') == '0' else 132)
            title = next((node for node in layout.findall("control[@type='label']")
                          if node.findtext('label') == '$INFO[ListItem.Label]'), None)
            if title is None: raise RuntimeError('youtube-compact-title-' + identity)
            field(title, 'top', 126); field(title, 'height', 30)
    plot = landing.find("control[@type='textbox']")
    if plot is None or plot.findtext('top') != '210' or plot.findtext('height') != '105':
        raise RuntimeError('youtube-compact-synopsis')
    field(plot, 'height', 120)
    meta = next((node for node in landing.findall("control[@type='label']")
                 if node.findtext('label') == '$VAR[AsterYouTubeHeroMeta]'), None)
    if meta is None or meta.findtext('top') != '326':
        raise RuntimeError('youtube-compact-meta')
    field(meta, 'top', 345)
    after = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    check = ET.fromstring(after)
    if check.findtext('onload') != FOCUS:
        raise RuntimeError('youtube-compact-focus-preservation')
    return after

def atomic(path, raw):
    descriptor, temporary = tempfile.mkstemp(prefix='.aster-youtube-compact-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, 0o644); os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)

def main():
    if os.uname().nodename != 'AsterTVProd' or CHECKPOINT.exists():
        raise RuntimeError('youtube-compact-boundary')
    nav_before, family_before = NAV.read_bytes(), FAMILY.read_bytes()
    if sha(nav_before) != NAV_BEFORE or sha(family_before) != FAMILY_BEFORE:
        raise RuntimeError('youtube-compact-predecessor')
    nav_after = compact(nav_before)
    family = json.loads(family_before)
    if family['skin']['1080i/MyVideoNav.xml'] != NAV_BEFORE:
        raise RuntimeError('youtube-compact-family')
    family['skin']['1080i/MyVideoNav.xml'] = sha(nav_after)
    family_after = (json.dumps(family, indent=2, sort_keys=True) + '\n').encode()
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    (CHECKPOINT / 'MyVideoNav-before.xml').write_bytes(nav_before)
    (CHECKPOINT / 'family-before.json').write_bytes(family_before)
    (CHECKPOINT / 'state').write_text('prepared\n')
    try:
        atomic(NAV, nav_after); atomic(FAMILY, family_after)
        if NAV.read_bytes() != nav_after or FAMILY.read_bytes() != family_after:
            raise RuntimeError('youtube-compact-install')
        (CHECKPOINT / 'state').write_text('installed\n')
    except Exception:
        atomic(NAV, nav_before); atomic(FAMILY, family_before)
        (CHECKPOINT / 'state').write_text('rolled-back\n')
        raise
    print(json.dumps({'installed': True, 'nav_sha256': sha(nav_after),
                      'family_sha256': sha(family_after)}))

if __name__ == '__main__': main()
