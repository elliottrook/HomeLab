"""Separate HP-only synthetic playback proof; private audio is never bundled."""
import hashlib
import json
from pathlib import Path
import argparse
import xml.etree.ElementTree as ET

AUDIO='99ae9edd408aa2fc6258d300c9d655cd4d81b88114f90fd609089a2541a5e039'
SENTENCES=('Mara reached the lantern house just before the rain.',
           'From the road it had looked small, almost an afterthought beside the hill.')

def layout():
    root=ET.Element('window');ET.SubElement(root,'defaultcontrol',always='true').text='201'
    ET.SubElement(root,'backgroundcolor').text='ffe6dac8'
    controls=ET.SubElement(root,'controls')
    def c(kind,i,x,y,w,h,**kw):
        node=ET.SubElement(controls,'control',type=kind,id=str(i))
        for k,v in dict(left=x,top=y,width=w,height=h,**kw).items():ET.SubElement(node,k).text=str(v)
        return node
    c('image',10,95,35,170,120,texture='special://skin/media/28-aster-books-logo.png',aspectratio='keep')
    c('label',11,340,65,1250,60,label='The Lantern House · Read along',font='font40',textcolor='ff1e241f')
    c('label',12,340,145,1250,50,label='Synthetic sentence-timing proof · No word timing or saved progress',font='font24',textcolor='ff65675d')
    for i,y in ((0,310),(1,505)):
        c('textbox',501+i,340,y,1220,175,label=SENTENCES[i],font='font40',textcolor='ff1e241f',
          visible='!String.IsEqual(Window.Property(ReadAlong.Active),'+str(i)+')')
        c('textbox',511+i,340,y,1220,175,label=SENTENCES[i],font='font40',textcolor='ff1f513b',
          visible='String.IsEqual(Window.Property(ReadAlong.Active),'+str(i)+')')
    c('label',520,340,780,1220,50,label='$INFO[Window.Property(ReadAlong.Status)]',font='font24',textcolor='ff1f513b')
    for identity,x,icon,label in ((201,805,'play','Play / pause'),(202,925,'stop','Stop'),(203,1045,'previous','Restart')):
        b=c('button',identity,x,880,80,80,label=label,font='font20',textcolor='00000000',focusedcolor='00000000',
            texturenofocus='',onleft=203 if identity==201 else identity-1,onright=201 if identity==203 else identity+1,onup='noop',ondown='noop')
        ET.SubElement(b,'texturefocus',border='18',colordiffuse='ffc2a06b').text='special://skin/media/ui-button-ring.png'
        for name in (('play','pause') if icon=='play' else (icon,)):
            fields=dict(texture=name+'.png',aspectratio='keep',colordiffuse='ff1f513b')
            if icon=='play':fields['visible']=('String.IsEqual(Window.Property(ReadAlong.State),Playing)' if name=='pause' else '!String.IsEqual(Window.Property(ReadAlong.State),Playing)')
            c('image',identity+100+(10 if name=='pause' else 0),x+16,896,48,48,**fields)
    c('label',530,340,995,1240,40,label='Back stops this preview · Existing 9-second Aster voice sample',font='font20',textcolor='ff65675d')
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n'

def build(output):
    root=Path(output);root.mkdir(mode=0o700,parents=True,exist_ok=False);here=Path(__file__).parent
    # Retain the accepted callback/file-identity guard unchanged except for the
    # explicitly local PCM container extension. No normal Digest runtime edit.
    port=(here/'digest_kodi_port.py').read_text().replace("self.path.suffix != '.mp3'","self.path.suffix != '.wav'")
    files={name:(here/name).read_bytes() for name in ('narration_frames.py','narration_timeline.py','digest_playback_state.py','digest_timeline.py')}
    for name in ('play','pause','stop','previous'):
        source=(here/'player-control-assets/previous.png' if name=='previous' else here/'script.astermusic.v2lab/resources/controls'/(name+'.png'))
        files['resources/skins/Default/media/'+name+'.png']=source.read_bytes()
    files.update({'default.py':(here/'readalong/default.py').read_bytes(),'digest_kodi_port.py':port.encode(),
                  'resources/skins/Default/1080i/ReadAlong.xml':layout()})
    config=dict(sentences=SENTENCES,frames=[87360,132720],text_sha256=hashlib.sha256(' '.join(SENTENCES).encode()).hexdigest())
    files['sample.json']=(json.dumps(config,sort_keys=True)+'\n').encode()
    for name,raw in files.items():
        p=root/name;p.parent.mkdir(mode=0o700,parents=True,exist_ok=True);p.write_bytes(raw);p.chmod(0o600)
    manifest=dict(kind='hp-readalong.v1',synthetic=True,network=False,progress=False,normal_entry=False,
                  audio_sha256=AUDIO,audio_bytes=440204,files={n:hashlib.sha256(v).hexdigest() for n,v in files.items()})
    raw=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode();(root/'manifest.json').write_bytes(raw);(root/'manifest.json').chmod(0o600)
    return hashlib.sha256(raw).hexdigest()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);print(build(p.parse_args().output))
