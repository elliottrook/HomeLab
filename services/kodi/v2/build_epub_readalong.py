"""Build the private HP narrated-EPUB stage; audio is relayed separately."""
import argparse,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
from epub_fixture import build_readalong

AUDIO='d10997803ee99ae85f06545ab5b0bad71e91906735f4811c2119a632399de02b'
FRAMES=1540176
MEASUREMENTS=[
 [0,0,87360],[1,87360,211320],[2,298680,80160],[3,378840,113520],
 [4,492360,111696],[5,604056,148320],[6,752376,68160],[7,820536,207120],
 [8,1027656,63960],[9,1091616,141120],[10,1232736,87360],[11,1320096,54360],
 [12,1374456,68760],[13,1443216,96960]]

def layout():
    root=ET.Element('window');ET.SubElement(root,'defaultcontrol',always='true').text='201';ET.SubElement(root,'backgroundcolor').text='ffe6dac8'
    controls=ET.SubElement(root,'controls')
    def c(kind,i,x,y,w,h,**fields):
        node=ET.SubElement(controls,'control',type=kind,id=str(i))
        for key,value in dict(left=x,top=y,width=w,height=h,**fields).items():ET.SubElement(node,key).text=str(value)
        return node
    c('image',10,95,35,170,120,texture='special://skin/media/28-aster-books-logo.png',aspectratio='keep')
    c('label',11,340,60,1250,55,label='The Lantern House · Read along',font='font40',textcolor='ff1e241f')
    c('label',12,340,125,1250,42,label='Original synthetic EPUB · Sentence-level Aster narration',font='font20',textcolor='ff65675d')
    c('label',13,340,190,1240,42,label='Chapter one',font='font24',textcolor='ff1f513b')
    for size,identity in ((24,501),(30,502),(40,503)):
        c('textbox',identity,340,245,1240,650,label='',font='font'+str(size),textcolor='ff1e241f',
          visible='String.IsEqual(Window.Property(EpubRead.Size'+str(size)+'),true)')
    c('label',520,340,900,1240,42,label='$INFO[Window.Property(EpubRead.Status)]',font='font24',textcolor='ff1f513b')
    items=((201,680,80,'play','Play or pause'),(202,790,80,'stop','Stop'),(203,900,80,'previous','Restart'))
    for identity,x,width,icon,label in items:
        button=c('button',identity,x,960,width,78,label=label,font='font20',textcolor='00000000',focusedcolor='00000000',texturenofocus='',
                 onleft=205 if identity==201 else identity-1,onright=204 if identity==203 else identity+1,onup='noop',ondown='noop')
        ET.SubElement(button,'texturefocus',border='18',colordiffuse='ffc2a06b').text='special://skin/media/ui-button-ring.png'
        names=('play','pause') if icon=='play' else (icon,)
        for name in names:
            fields=dict(texture=name+'.png',aspectratio='keep',colordiffuse='ff1f513b')
            if icon=='play':fields['visible']='String.IsEqual(Window.Property(EpubRead.State),Reading)' if name=='pause' else '!String.IsEqual(Window.Property(EpubRead.State),Reading)'
            c('image',identity+100+(10 if name=='pause' else 0),x+16,975,48,48,**fields)
    for identity,x,width,label,left,right in ((204,1010,250,'Clear test progress',203,205),(205,1290,180,'Text 30',204,201)):
        b=c('button',identity,x,965,width,64,label=label,font='font20',textcolor='ff1e241f',focusedcolor='fff3eee5',align='center',aligny='center',
            texturenofocus='',onleft=left,onright=right,onup='noop',ondown='noop')
        ET.SubElement(b,'texturefocus',border='18',colordiffuse='ff1f513b').text='special://skin/media/ui-panel.png'
    c('label',530,340,1045,1240,35,label='Back stops and saves this private test · Green marks the current sentence, not individual words',font='font20',textcolor='ff65675d')
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n'

def build(output):
    root=Path(output);root.mkdir(mode=0o700,parents=True,exist_ok=False);here=Path(__file__).parent
    port=(here/'digest_kodi_port.py').read_text().replace("self.path.suffix != '.mp3'","self.path.suffix != '.wav'")
    names=('epub_chapter.py','epub_fixture.py','epub_pages.py','chapter_narration.py','epub_readalong_state.py','digest_playback_state.py','digest_timeline.py')
    files={name:(here/name).read_bytes() for name in names}
    files.update({'default.py':(here/'epub_readalong/default.py').read_bytes(),'digest_kodi_port.py':port.encode(),
                  'sample.epub':build_readalong(),'resources/skins/Default/1080i/EpubReadAlong.xml':layout()})
    for name in ('play','pause','stop','previous'):
        source=(here/'player-control-assets/previous.png' if name=='previous' else here/'script.astermusic.v2lab/resources/controls'/(name+'.png'))
        files['resources/skins/Default/media/'+name+'.png']=source.read_bytes()
    config=dict(spoken_sha256='70801db5b3f53de7badb7250fcc77664a7221af33f4b304d788b0c3f3b87bab9',
                measurements=[dict(index=i,start_sample=start,frames=frames,sample_rate=24000) for i,start,frames in MEASUREMENTS])
    files['sample.json']=(json.dumps(config,sort_keys=True)+'\n').encode()
    for name,raw in files.items():
        path=root/name;path.parent.mkdir(mode=0o700,parents=True,exist_ok=True);path.write_bytes(raw);path.chmod(0o600)
    manifest=dict(kind='hp-epub-readalong.v1',synthetic=True,network=False,shared_progress=False,normal_entry=False,
                  word_timestamps=False,audio_sha256=AUDIO,audio_bytes=3080396,audio_frames=FRAMES,
                  files={name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()})
    raw=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode();(root/'manifest.json').write_bytes(raw);(root/'manifest.json').chmod(0o600)
    return hashlib.sha256(raw).hexdigest()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);print(build(parser.parse_args().output))
