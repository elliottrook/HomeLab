"""Shared v2 floating transport overlay; never edits or activates the v1 skin.

Build a reviewable ZIP of four replacement XML pages and their glyph assets.
Original button IDs, labels, actions, conditions, navigation and window hooks
are retained. Deployment/activation is a separate milestone, not this builder.
"""
import argparse
import hashlib
import json
from pathlib import Path
import stat
import xml.etree.ElementTree as ET
import zipfile

HERE=Path(__file__).resolve().parent
SKIN=HERE.parent/'skin.asterhome'
ICONS=HERE/'script.astermusic.v2lab/resources/controls'
EXTRA=HERE/'player-control-assets'
# Each tuple is one visual slot; mutually exclusive Play/Pause retain one slot.
PAGES={
 'VideoOSD.xml':dict(dark=True,frame=(70,1780),top=267,slots=((600,),(601,),(602,605),(606,),(607,),(603,),(70043,),(7100,),(7101,),(7102,)),
     icons={600:'previous',601:'back',602:'pause',605:'play',606:'forward',607:'play-next',603:'stop',70043:'info',7100:'audio',7101:'subtitles',7102:'quality'}),
 'custom_1121_albumplayer.xml':dict(dark=False,frame=(150,680),top=890,slots=((9100,),(9101,),(9102,9105),(9103,),(9104,)),
     icons={9100:'play',9101:'previous',9102:'pause',9105:'play',9103:'play-next',9104:'stop',9000:'return'}),
 'MyMusicNav.xml':dict(dark=False,frame=(150,680),top=890,slots=((9101,),(9102,9105),(9103,),(9104,)),
     icons={9101:'back',9102:'pause',9105:'play',9103:'forward',9104:'stop',9000:'return'}),
 'custom_1111_digest.xml':dict(dark=False,frame=(150,710),top=916,slots=((305,),(300,),(302,304),(303,)),
     icons={305:'full-digest',300:'play',302:'pause',304:'play',303:'stop'}),
}

def set_value(control,key,value):
    for old in list(control.findall(key)):control.remove(old)
    ET.SubElement(control,key).text=str(value) if value is not None else None

def page(name,source):
    config=PAGES[name];root=ET.fromstring(source)
    buttons={int(c.get('id')):c for c in root.findall('.//control[@type="button"]') if c.get('id')}
    parents={child:parent for parent in root.iter() for child in parent}
    left,width=config['frame'];slots=config['slots'];target=76;gap=36
    span=len(slots)*target+(len(slots)-1)*gap
    if span>width:raise ValueError('control-row-exceeds-frame')
    start=left+(width-span)//2
    positions={identity:(start+index*(target+gap),config['top']) for index,slot in enumerate(slots) for identity in slot}
    pairs={slot[0]:slot[1] for slot in slots if len(slot)==2}
    aliases=set(pairs.values())
    if 9000 in config['icons']:positions[9000]=(1702,62)
    for identity,glyph in config['icons'].items():
        control=buttons[identity];parent=parents[control]
        x,y=positions[identity];back=identity==9000
        dark=config['dark'] or back
        caption=control.findtext('label')
        if not caption:raise ValueError('missing-accessible-label')
        for include in list(control.findall('include')):control.remove(include)
        for key,value in dict(left=x,top=y,width=target,height=64,font='font20',textcolor='00000000',focusedcolor='00000000',texturefocus=None,texturenofocus=None).items():set_value(control,key,value)
        if identity in aliases:
            # Kodi retains the focused ID when a Pause button becomes hidden.
            # Keep the legacy Play alias/action but never swap focus targets.
            set_value(control,'visible','false')
            continue
        variants=[(glyph,None,caption)]
        if identity in pairs:
            other=buttons[pairs[identity]]
            old_visible=control.findtext('visible') or 'true'
            other_visible=other.findtext('visible') or 'true'
            set_value(control,'visible',f'[{old_visible}] | [{other_visible}]')
            set_value(control,'label','Play / Pause')
            variants=[('pause','!Player.Paused','Pause'),('play','Player.Paused','Play')]
        for variant,state,_ in variants:
            for focused,size,color in ((False,44,'asterRailText' if dark else 'asterInk'),(True,48,'asterSage' if dark else 'asterGreen')):
                image=ET.SubElement(parent,'control',type='image')
                for key,value in dict(left=x+(target-size)//2,top=y+(64-size)//2,width=size,height=size).items():set_value(image,key,value)
                ET.SubElement(image,'texture',colordiffuse=color).text=f'special://skin/media/player-controls/{variant}.png'
                set_value(image,'aspectratio','keep')
                set_value(image,'visible',f'Control.IsVisible({identity}) + '+('' if focused else '!')+f'Control.HasFocus({identity})'+(' + '+state if state else ''))
        line=ET.SubElement(parent,'control',type='image')
        for key,value in dict(left=x+28,top=y+63,width=20,height=2,visible=f'Control.IsVisible({identity}) + Control.HasFocus({identity})').items():set_value(line,key,value)
        ET.SubElement(line,'texture',colordiffuse='asterGold').text='special://skin/media/ui-solid.png'
        caption_left,caption_width=(1540,300) if back else (left,width)
        for _,state,text in variants:
            label=ET.SubElement(parent,'control',type='label')
            for key,value in dict(left=caption_left,top=y+69,width=caption_width,height=28,label=text,font='font16',textcolor='asterRailText' if dark else 'asterInk',align='center',aligny='center',truncate='true',visible=f'Control.IsVisible({identity}) + Control.HasFocus({identity})'+(' + '+state if state else '')).items():set_value(label,key,value)
    ET.indent(root,space='  ')
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def build(output):
    output=Path(output)
    if output.exists() and any(output.iterdir()):raise ValueError('nonempty-output')
    output.mkdir(parents=True,exist_ok=True)
    data={};sources={}
    for name in PAGES:
        source=(SKIN/'1080i'/name).read_bytes();sources[name]=hashlib.sha256(source).hexdigest()
        data['1080i/'+name]=page(name,source)
    needed={glyph for config in PAGES.values() for glyph in config['icons'].values()}
    for name in sorted(needed):
        directory=ICONS if (ICONS/(name+'.png')).exists() else EXTRA
        for extension in ('.svg','.png'):data['media/player-controls/'+name+extension]=(directory/(name+extension)).read_bytes()
    archive=output/'aster-v2-floating-player-overlay.zip';records=[]
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as package:
        for name,value in sorted(data.items()):
            entry=zipfile.ZipInfo(name,(2026,10,24,0,0,0));entry.create_system=3;entry.external_attr=(stat.S_IFREG|0o644)<<16
            package.writestr(entry,value,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
            records.append(dict(path=name,sha256=hashlib.sha256(value).hexdigest()))
    manifest=dict(status='local-v2-candidate-not-installed',archive=archive.name,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),source_sha256=sources,files=records,
                  boundary='Four v2 player page candidates only; no v1 source edit, native activation, service change or production rollout')
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    print(json.dumps(build(parser.parse_args().output),indent=2))
