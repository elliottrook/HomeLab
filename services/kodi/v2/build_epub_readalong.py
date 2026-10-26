"""Build the private HP narrated-EPUB stage from versioned synthetic fixtures."""
import argparse,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
from epub_fixture import build_readalong

AUDIO='1da10ad89f095d2c619cff92760564d701401c8a50261b40c98eda228d001466'
FIXTURE='aa47b3d5891110ca18ba77cde167f181a9b91ccc8f2f16a1a1ad4874f779c8ec'
FRAMES=252399

def layout():
    root=ET.Element('window');ET.SubElement(root,'defaultcontrol',always='true').text='500';ET.SubElement(root,'backgroundcolor').text='ffe6dac8'
    controls=ET.SubElement(root,'controls')
    def c(kind,i,x,y,w,h,**fields):
        node=ET.SubElement(controls,'control',type=kind,id=str(i))
        for key,value in dict(left=x,top=y,width=w,height=h,**fields).items():ET.SubElement(node,key).text=str(value)
        return node
    c('image',10,95,35,170,120,texture='special://skin/media/28-aster-books-logo.png',aspectratio='keep')
    c('label',11,340,60,1250,55,label='The Lantern House · Read along',font='font40',textcolor='ff1e241f')
    c('label',12,340,125,1250,42,label='Original synthetic EPUB · Native Aster word timing',font='font20',textcolor='ff65675d')
    c('label',13,340,190,1240,42,label='Chapter one',font='font24',textcolor='ff1f513b')
    for size,identity in ((24,501),(30,502),(40,503)):
        c('textbox',identity,340,245,1240,650,label='',font='font'+str(size),textcolor='ff1e241f',
          visible='String.IsEqual(Window.Property(EpubRead.Size'+str(size)+'),true)')
    c('button',500,340,245,1240,650,label='',textcolor='00000000',focusedcolor='00000000',
      texturefocus='',texturenofocus='',onleft='noop',onright='noop',onup=201,ondown=201)
    c('label',520,340,900,1240,42,label='$INFO[Window.Property(EpubRead.Status)]',font='font24',textcolor='ff1f513b')
    items=((201,680,80,'play','Play or pause'),(202,790,80,'stop','Stop'),(203,900,80,'previous','Restart'))
    for identity,x,width,icon,label in items:
        button=c('button',identity,x,960,width,78,label=label,font='font20',textcolor='00000000',focusedcolor='00000000',texturenofocus='',
                 onleft=205 if identity==201 else identity-1,onright=204 if identity==203 else identity+1,onup=500,ondown=500)
        ET.SubElement(button,'texturefocus',border='18',colordiffuse='ffc2a06b').text='special://skin/media/ui-button-ring.png'
        names=('play','pause') if icon=='play' else (icon,)
        for name in names:
            fields=dict(texture=name+'.png',aspectratio='keep',colordiffuse='ff1f513b')
            if icon=='play':fields['visible']='String.IsEqual(Window.Property(EpubRead.State),Reading)' if name=='pause' else '!String.IsEqual(Window.Property(EpubRead.State),Reading)'
            c('image',identity+100+(10 if name=='pause' else 0),x+16,975,48,48,**fields)
    for identity,x,width,label,left,right in ((204,1010,250,'Clear test progress',203,205),(205,1290,180,'Text 30',204,201)):
        b=c('button',identity,x,965,width,64,label=label,font='font20',textcolor='ff1e241f',focusedcolor='fff3eee5',align='center',aligny='center',
            texturenofocus='',onleft=left,onright=right,onup=500,ondown=500)
        ET.SubElement(b,'texturefocus',border='18',colordiffuse='ff1f513b').text='special://skin/media/ui-panel.png'
    c('label',530,340,1045,1240,35,label='Back stops and saves this private test · Green marks the current word or connected phrase',font='font20',textcolor='ff65675d')
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n'

def build(output):
    root=Path(output);root.mkdir(mode=0o700,parents=True,exist_ok=False);here=Path(__file__).parent
    port=(here/'digest_kodi_port.py').read_text().replace("self.path.suffix != '.mp3'","self.path.suffix != '.wav'")
    if port.count('deadline = time.monotonic()+.75') != 1:
        raise ValueError('epub-readalong-port-source-drift')
    port=port.replace('deadline = time.monotonic()+.75','deadline = time.monotonic()+5')
    names=('epub_chapter.py','epub_fixture.py','epub_pages.py','chapter_narration.py','word_alignment.py','word_group_narration.py','epub_readalong_state.py','digest_playback_state.py','digest_timeline.py')
    files={name:(here/name).read_bytes() for name in names}
    files.update({'default.py':(here/'epub_readalong/default.py').read_bytes(),'digest_kodi_port.py':port.encode(),
                  'sample.epub':build_readalong(),
                  'chapter.wav':(here/'fixtures/aster-epub-word-groups-synthetic.wav').read_bytes(),
                  'resources/skins/Default/1080i/EpubReadAlong.xml':layout()})
    if hashlib.sha256(files['chapter.wav']).hexdigest()!=AUDIO or len(files['chapter.wav'])!=504842:
        raise ValueError('epub-readalong-versioned-audio-drift')
    for name in ('play','pause','stop','previous'):
        source=(here/'player-control-assets/previous.png' if name=='previous' else here/'script.astermusic.v2lab/resources/controls'/(name+'.png'))
        files['resources/skins/Default/media/'+name+'.png']=source.read_bytes()
    fixture=(here/'fixtures/aster-epub-word-groups-synthetic.json').read_bytes()
    if hashlib.sha256(fixture).hexdigest()!=FIXTURE:
        raise ValueError('epub-readalong-versioned-fixture-drift')
    config=json.loads(fixture);files['sample.json']=fixture
    for name,raw in files.items():
        path=root/name;path.parent.mkdir(mode=0o700,parents=True,exist_ok=True);path.write_bytes(raw);path.chmod(0o600)
    manifest=dict(kind='hp-epub-readalong.v2',synthetic=True,network=False,shared_progress=False,normal_entry=False,
                  word_timestamps=True,connected_phrase_cues=True,audio_sha256=AUDIO,audio_bytes=504842,audio_frames=FRAMES,
                  source_timing=dict(method='kokoro-native-duration-v1',source_sha256=config['source_sha256'],
                                     spoken_group_count=config['spoken_group_count']),
                  eof_settlement=dict(active_player_seconds=5,queue_seconds=3),
                  files={name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()})
    raw=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode();(root/'manifest.json').write_bytes(raw);(root/'manifest.json').chmod(0o600)
    return hashlib.sha256(raw).hexdigest()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);print(build(parser.parse_args().output))
