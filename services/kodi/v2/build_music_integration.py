"""Generate a pinned HP-only normal-Music overlay, preserving v1 source files."""
import argparse,ast,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'skin.asterhome'
BEFORE={
 'tools/music_data.py':'e32c021ad6c854d81ec2258d7b415268828d6c6fed8bcdbbe0849951df49e292',
 '1080i/IncludesMusic.xml':'bbfe06825051519d4b29f58ff1090cdb509c1800e1367bfbca8c34a8eb35bdec',
 '1080i/custom_1113_music.xml':'c8845cec9fce7e5300ba8c7595008e30d9f299449b212f3043f206b3556d3c8c',
 '1080i/custom_1114_albums.xml':'7a528f2a581e5652e2124421bde632448cc5593ec46d6d247fb1aff8171301ce',
 '1080i/custom_1115_artists.xml':'2b26b925c550973ba862ae3fc15833a0e8b3cdc2610037c25a1ddd11e2bc5e79',
 '1080i/custom_1116_songs.xml':'1fb31f22290d37a27687f698477bf07133adb5eac85af5df864b8130671f5077',
 '1080i/custom_1117_playlists.xml':'ec3cf25106684619520dead8a430fb62b0b33c14f20998e9dabbc0b5a33249ed',
}


def transformed():
    files={}
    for name,expected in BEFORE.items():
        data=(BASE/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('base-source-drift:'+name)
        files[name]=data
    text=files['tools/music_data.py'].decode()
    text=text.replace('import sys\n','import sys\nimport time\n')
    text=text.replace('from hub_data import kodi_rpc','from hub_data import kodi_rpc\nfrom aster_v2_music import handoff, restore_focus')
    anchor='                pending = xbmcgui.Window(10000)\n'
    if text.count(anchor)!=1:raise ValueError('handoff-anchor')
    insert='''                source_path = (selected.getProperty('AsterMusic.File') if selected else
                               xbmc.getInfoLabel('Container(500).ListItem.Property(AsterMusic.File)'))
                if handoff(xbmc, xbmcgui, page, identifier_text, source_path):
                    return
'''
    text=text.replace(anchor,insert+anchor)
    text=text.replace("    elif action in ('play', 'open'):\n", "    elif action in ('play', 'open'):\n        if window.getProperty('AsterMusic.LoadReady') != 'true':\n            return\n")
    request="    request = str(time.monotonic_ns())\n    window.setProperty('AsterMusic.LoadRequest', request)\n    window.setProperty('AsterMusic.LoadReady', 'false')\n"
    text=text.replace("    window.setProperty('AsterMusic.Section',",request+"    window.setProperty('AsterMusic.Section',",1)
    text=text.replace('    listing = window.getControl(500)\n',"    if window.getProperty('AsterMusic.LoadRequest') != request:\n        return\n    listing = window.getControl(500)\n",1)
    text=text.replace('\n    listing.reset()\n', '\n', 1)
    text=text.replace('\n    listing.addItems(items)\n', "\n    if window.getProperty('AsterMusic.LoadRequest') != request:\n        return\n    listing.reset()\n    listing.addItems(items)\n", 1)
    files['tools/music_data.py']=text.encode()
    focus="    if action == 'load' and items:\n        xbmc.executebuiltin('Control.SetFocus(500,0,absolute)')"
    replacement=""
    if files['tools/music_data.py'].decode().count(focus)!=1:raise ValueError('restore-focus-anchor')
    files['tools/music_data.py']=files['tools/music_data.py'].decode().replace(focus,replacement).encode()
    text=files['tools/music_data.py'].decode()
    end="    window.setProperty('AsterMusic.SearchLabel', 'Search: ' + query if query else 'Search ' + page)"
    completion="""
    window.setProperty('AsterMusic.LoadReady', 'true')
    if action == 'load' and items and xbmcgui.getCurrentWindowId() == PAGES[page]:
        if not restore_focus(xbmc, window, page, rows):
            xbmc.executebuiltin('Control.SetFocus(500,0,absolute)')
    window.setProperty('AsterMusic.LoadGeneration', request)
"""
    if text.count(end)!=1:raise ValueError('load-completion-anchor')
    files['tools/music_data.py']=text.replace(end,end+completion).encode()
    files['tools/aster_v2_music.py']=(HERE/'integration_handoff.py').read_bytes()
    root=ET.fromstring(files['1080i/IncludesMusic.xml'])
    template=root.find("include[@name='AsterMusicPage']")
    template.insert(0,ET.Element('param',dict(name='gridup',default='111')))
    pill=root.find("include[@name='AsterMusicPillButton']")
    for field,value in dict(width='200',height='50',textoffsetx='50').items():pill.find(field).text=value
    definition=root.find("include[@name='AsterMusicPage']/definition")
    group=next(group for group in definition.findall('control') if group.find("control[@id='110']") is not None)
    bar=ET.Element('control',dict(type='image'))
    for field,value in dict(left='0',top='0',width='1920',height='160',texture='special://skin/media/ui-solid.png',colordiffuse='ff3b3a32').items():ET.SubElement(bar,field).text=value
    group.insert(0,bar)
    positions={110:385,111:597,112:809,113:1021,114:1233,115:1445}
    for identity in (110,111,112,113):
        control=group.find(f"control[@id='{identity}']")
        control.find('left').text=str(positions[identity])
        control.find('onright').text=str(identity+1)
    for identity,title,route in ((114,'Genres','genres'),):
        control=ET.SubElement(group,'control',dict(type='button',id=str(identity)))
        for field,value in dict(left=str(positions[identity]),top='28',label=title,include='AsterMusicPillButton',
                onclick=f'RunScript(special://skin/tools/aster_v2_music.py,{route},$PARAM[page])',onleft=str(identity-1),
                onright='500',ondown='500').items():ET.SubElement(control,field).text=value
        icon=ET.SubElement(group,'control',dict(type='image'))
        for field,value in dict(left=str(positions[identity]+10),top='35',width='36',height='36',
                texture='special://skin/media/13-music.png' if identity==114 else
                    'special://home/addons/script.astermusic.v2lab/resources/controls/shuffle.png',aspectratio='keep').items():ET.SubElement(icon,field).text=value
    hero=ET.SubElement(group,'control',dict(type='button',id='115'))
    for field,value in dict(left='1050',top='455',width='320',height='56',label='Shuffle all',font='font24',align='center',aligny='center',
        textcolor='asterIvory',focusedcolor='asterIvory',onleft='110',onright='500',onup='112',ondown='500',
        visible='Window.IsActive(11113)',
        onclick='RunScript(special://skin/tools/aster_v2_music.py,shuffle,home)').items():ET.SubElement(hero,field).text=value
    for field,colour in (('texturefocus','asterGreen'),('texturenofocus','c929302b')):
        ET.SubElement(hero,field,dict(border='20',colordiffuse=colour)).text='special://skin/media/ui-panel.png'
    group.find("control[@id='500']/onup").text='$PARAM[gridup]'
    for image in group.findall("control[@type='image']"):
        texture=image.findtext('texture') or ''
        for identity,filename in ((110,'23-music-album.png'),(111,'24-music-artist.png'),(112,'25-music-song.png'),(113,'26-music-playlist.png')):
            if texture.endswith('/'+filename):image.find('left').text=str(positions[identity]+10);image.find('top').text='35'
        if image.findtext('left')=='$PARAM[activeleft]':image.find('width').text='200'
    for control in group.findall('control'):
        if control.get('id') in ('110','111','112','113','114','115','500'):
            ET.SubElement(control,'enable').text='String.IsEqual(Window.Property(AsterMusic.LoadReady),true)'
    files['1080i/IncludesMusic.xml']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    for name in list(files):
        if not name.startswith('1080i/custom_'):continue
        root=ET.fromstring(files[name]);page=root.find(".//param[@name='page']").get('value')
        identity={'home':110,'albums':110,'artists':111,'songs':112,'playlists':113}[page]
        root.find(".//param[@name='activeleft']").set('value',str(positions[identity]))
        include=root.find(".//include[@content='AsterMusicPage']")
        ET.SubElement(include,'param',dict(name='gridup',value='115' if page=='home' else '111'))
        window_id={'home':11113,'albums':11114,'artists':11115,'songs':11116,'playlists':11117}[page]
        position=list(root).index(root.find('onload'))
        for offset,command in enumerate((f'ClearProperty(AsterMusic.LoadReady,{window_id})',
                f'ClearProperty(AsterMusic.LoadRequest,{window_id})',
                f'SetProperty(AsterMusic.Status,Loading music…,{window_id})')):
            node=ET.Element('onload');node.text=command;root.insert(position+offset,node)
        files[name]=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    return files


def build(destination,player_sha,previous=None):
    if len(player_sha)!=64 or any(c not in '0123456789abcdef' for c in player_sha):raise ValueError('player-hash')
    destination=Path(destination)
    if destination.exists():raise ValueError('immutable-destination-exists')
    files=transformed()
    for name,data in files.items():
        if name.endswith('.py'):ast.parse(data)
        elif name.endswith('.xml'):ET.fromstring(data)
    destination.mkdir(parents=True)
    rows=[];prior=None
    if previous:
        data=Path(previous).read_bytes();prior=json.loads(data)
        if prior.get('kind')!='hp-normal-music-integration':raise ValueError('previous-kind')
        old_hashes={row['path']:row['sha256'] for row in prior['files']}
    for name,data in sorted(files.items()):
        target=destination/'files'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        rows.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),before_sha256=old_hashes[name] if prior else BEFORE.get(name)))
    manifest=dict(schema=1,kind='hp-normal-music-integration',player_sha_at_deploy=player_sha,files=rows)
    if prior:manifest['previous_manifest_sha256']=hashlib.sha256(Path(previous).read_bytes()).hexdigest()
    data=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode()
    (destination/'manifest.json').write_bytes(data)
    return hashlib.sha256(data).hexdigest()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--player-sha',required=True);parser.add_argument('--previous')
    args=parser.parse_args();print(build(args.output,args.player_sha,args.previous))
