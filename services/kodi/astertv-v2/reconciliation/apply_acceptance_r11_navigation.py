#!/usr/bin/env python3
"""Checkpoint and apply the reviewed TV, Movie and Requests navigation repairs."""

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess

ADDONS = Path('/storage/.kodi/addons')
RUNTIME = ADDONS / 'script.asterruntime'
SKIN = ADDONS / 'skin.asterhome'
SERIES = RUNTIME / 'aster-series-preview24'
SEARCH = RUNTIME / 'aster-global-search-ui22'
CHECKPOINT = Path('/storage/.aster-checkpoints/astertv-v2-acceptance-r11-navigation-20261030')
PATHS = {
    'series_py': SERIES / 'default.py',
    'series_xml': SERIES / 'resources/skins/Default/1080i/SeriesPreview.xml',
    'series_manifest': SERIES / 'manifest.json',
    'movie_py': SEARCH / 'movie.py',
    'movie_overlay': SEARCH / 'overlay/custom_1130_movie.xml',
    'dispatch_overlay': SEARCH / 'overlay/select_dispatch.py',
    'search_manifest': SEARCH / 'manifest.json',
    'movie_live': SKIN / '1080i/custom_1130_movie.xml',
    'dispatch_live': SKIN / 'tools/select_dispatch.py',
    'requests_live': SKIN / '1080i/custom_1132_requests.xml',
    'family': RUNTIME / 'family-manifest.json',
}
EXPECTED = {
    'series_py': 'dbec4a032de0f78df01202c48261eadd12575e7c112895747ab417453046addc',
    'series_xml': 'ed656519e5d9b65ee54352c47901a53f48fdf726464c4ee50950e4b5c7fc5d02',
    'series_manifest': '1f1142545750c8bde616b698a7ea663006e818b31be9c75c67c589bc36d9d0db',
    'movie_py': 'ed5d989c2cf064a9dee15ea307ecb9bf1aaf622284a6c14b4f2da0744806896d',
    'movie_overlay': '61fbf75373b595bcebf3ae057f8c590fc418312c57b84379be529e81257efe3c',
    'dispatch_overlay': '1ec4095cb6915838c2a31a84998c27aeaf605ba6d9bdad436981ea2579dc895d',
    'search_manifest': '0e975885e0d08abf91a742860628d82037093660cc3cf50d080e72f017330847',
    'movie_live': '61fbf75373b595bcebf3ae057f8c590fc418312c57b84379be529e81257efe3c',
    'dispatch_live': 'a39820871ea5568d41254f03bb0caedbc51b6094175b4e939986a805af9803fd',
    'requests_live': 'b90ff06b256441f50fff9435bdb9def119030430103b770125cd2e57a518b137',
    'family': 'a3e1cd008c6b8f8c23261fd5933b94fb7cb4b42d6ec46b8c898a5660120572f2',
}


def sha(data): return hashlib.sha256(data).hexdigest()
def encode(value): return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def replace(text, old, new, label, count=1):
    if text.count(old) != count: raise RuntimeError(label + '-anchor')
    return text.replace(old, new, count)


def idle():
    request={'jsonrpc':'2.0','id':1,'method':'Player.GetActivePlayers'}
    with socket.create_connection(('127.0.0.1',9090),timeout=3) as client:
        client.sendall((json.dumps(request)+'\n').encode());answer=json.loads(client.recv(4096).decode())
    if answer.get('result') != []: raise RuntimeError('active-player')


def manifest_with(path, members):
    value=json.loads(path.read_text())
    for row in value['files']:
        if row['path'] in members:
            data=members[row['path']];row['bytes']=len(data);row['sha256']=sha(data)
    return encode(value)


def main():
    idle()
    original={name:path.read_bytes() for name,path in PATHS.items()}
    for name,expected in EXPECTED.items():
        if sha(original[name]) != expected: raise RuntimeError('unexpected-live-hash:'+name)

    series=original['series_py'].decode()
    series=replace(series,
        "item.setProperty('State',('Catalogue · not in your library' if row.catalogue else\n                'Watched' if row.watched else 'In progress' if row.progress_percent is not None else ''))",
        "item.setProperty('State',('Catalogue · not in your library' if row.catalogue else\n                'In progress' if row.progress_percent is not None and not row.watched else ''))\n            item.setProperty('Watched','true' if row.watched else 'false')",
        'series-watched')
    old="""        if control==300 and key in (3,4):self.pending_index=None
        if key in BACK:
"""
    new="""        if control==300 and key in (3,4):
            self.pending_index=None
            last=len(self.selection.group.episodes)-1 if self.selection.group else 0
            target=None
            if key==3 and self.selection.index==0 and self.selection.season>0:
                target=self.selection.season-1
            elif key==4 and self.selection.index==last and self.selection.season+1<len(self.snapshot.page.seasons):
                target=self.selection.season+1
            if target is not None:
                self.updating=True
                try:
                    self.selection.change_season(target)
                    self.selection.index=(len(self.selection.group.episodes)-1 if key==3 else 0)
                    self.populate();self.setFocusId(300)
                finally:self.updating=False
                self.publish();return
        if key in BACK:
"""
    series=replace(series,old,new,'series-cross-season')

    sx=original['series_xml'].decode()
    sx=replace(sx,'<defaultcontrol always="true">202</defaultcontrol>',
                  '<defaultcontrol always="true">300</defaultcontrol>','series-default-focus')
    sx=sx.replace('colordiffuse="eef3eee5"','colordiffuse="b8000000"')
    sx=sx.replace('colordiffuse="fff3eee5">special://home/addons/skin.asterhome/media/ui-panel.png</texture><visible>String.IsEqual(ListItem.Property(Selected),true)',
                  'colordiffuse="df000000">special://home/addons/skin.asterhome/media/ui-panel.png</texture><visible>String.IsEqual(ListItem.Property(Selected),true)')
    sx=sx.replace('<textcolor>ff202b25</textcolor>','<textcolor>fff3eee5</textcolor>')
    still='<control type="image"><left>12</left><top>40</top><width>198</width><height>118</height><texture>$INFO[ListItem.Property(Still)]</texture><aspectratio>scale</aspectratio></control>'
    tick=still+'<control type="label"><left>174</left><top>42</top><width>30</width><height>30</height><label>●</label><font>font24</font><textcolor>ff00a878</textcolor><align>center</align><visible>String.IsEqual(ListItem.Property(Watched),true)</visible></control>'
    sx=replace(sx,still,tick,'series-watched-marker',2)
    sx=sx.replace('<texturefocus/><texturenofocus/><align>left</align>',
        '<texturefocus border="20" colordiffuse="ff005c46">special://home/addons/skin.asterhome/media/ui-panel.png</texturefocus><texturenofocus border="20" colordiffuse="99000000">special://home/addons/skin.asterhome/media/ui-panel.png</texturenofocus><align>center</align>',2)
    series_b=series.encode();sx_b=sx.encode()
    series_manifest=manifest_with(PATHS['series_manifest'],{'default.py':series_b,
        'resources/skins/Default/1080i/SeriesPreview.xml':sx_b})

    movie=original['movie_py'].decode()
    movie=replace(movie,"if (window_id,focus) not in ((10025,50),(10000,100),(10000,110)):",
        "if (window_id,focus) not in ((10025,50),(10000,100),(10000,110),(11112,100),(11112,110)):",
        'movie-home-source')
    movie=replace(movie,"item=110 if (window_id,focus)==(10000,110) else 100 if window_id==10000 else 50",
        "item=110 if focus==110 else 100 if focus==100 else 50",'movie-home-container')
    movie=replace(movie,"window.setProperty('Movie.Status','Choose Play or Resume · opening this page never starts playback')",
        "window.setProperty('Movie.Status','')",'movie-instructions')
    movie_b=movie.encode()

    dispatch=original['dispatch_live'].decode()
    dispatch=replace(dispatch,
        "if (window_id, focus_id) in ((10025, 50), (10000, 100), (10000, 110)):",
        "if (window_id, focus_id) in ((10025, 50), (10000, 100), (10000, 110), (11112, 100), (11112, 110)):",
        'dispatch-movie-home')
    dispatch=replace(dispatch,
        "if (window_id, focus_id) in ((10025, 50), (10000, 110)):",
        "if (window_id, focus_id) in ((10025, 50), (10000, 110), (11112, 110)):",
        'dispatch-series-home')
    dispatch_b=dispatch.encode()

    mx=original['movie_live'].decode()
    for identity,left,top,width,height in (('200','565','725','96','90'),('201','810','725','96','90'),('202','1705','35','96','90')):
        anchor='<control type="button" id="'+identity+'"'
        panel=('<control type="image"><left>'+left+'</left><top>'+top+'</top><width>'+width+'</width><height>'+height+'</height>'
               '<texture border="24" colordiffuse="dd005c46">special://skin/media/ui-panel.png</texture>'
               '<visible>Control.HasFocus('+identity+')</visible></control>')
        mx=replace(mx,anchor,panel+anchor,'movie-focus-'+identity)
    mx_b=mx.encode()

    search_manifest=manifest_with(PATHS['search_manifest'],{
        'movie.py':movie_b,'overlay/custom_1130_movie.xml':mx_b,'overlay/select_dispatch.py':dispatch_b})

    requests=original['requests_live'].decode()
    anchor='    <control type="image"><left>110</left><top>0</top><width>240</width>'
    rail='    <include content="AsterNavigationRail"><param name="content" value="30" /><param name="railfocus" value="9009" /></include>\n'
    requests=replace(requests,anchor,rail+anchor,'requests-rail')
    requests=replace(requests,'<onleft>52</onleft>','<onleft>8999</onleft>','requests-rail-focus')
    requests_b=requests.encode()

    family=json.loads(original['family'])
    family['components']['aster-series-preview24']['manifest_sha256']=sha(series_manifest)
    family['components']['aster-global-search-ui22']['manifest_sha256']=sha(search_manifest)
    family['skin']['tools/select_dispatch.py']=sha(dispatch_b)
    family['skin']['1080i/custom_1130_movie.xml']=sha(mx_b)
    family['skin']['1080i/custom_1132_requests.xml']=sha(requests_b)
    family_b=encode(family)
    replacement={
        'series_py':series_b,'series_xml':sx_b,'series_manifest':series_manifest,
        'movie_py':movie_b,'movie_overlay':mx_b,'dispatch_overlay':dispatch_b,
        'search_manifest':search_manifest,'movie_live':mx_b,'dispatch_live':dispatch_b,
        'requests_live':requests_b,'family':family_b,
    }
    CHECKPOINT.mkdir(mode=0o700)
    evidence={'kind':'astertv-v2-acceptance-r11-navigation','files':{}}
    for name,path in PATHS.items():
        saved=CHECKPOINT/(name+'__'+path.name);saved.write_bytes(original[name]);os.chmod(saved,0o600)
        evidence['files'][str(path.relative_to(ADDONS))]={'before':sha(original[name]),'after':sha(replacement[name])}
    (CHECKPOINT/'manifest.json').write_bytes(encode(evidence))
    subprocess.run(['systemctl','stop','kodi'],check=True)
    try:
        for name,path in PATHS.items():
            temp=path.with_suffix(path.suffix+'.r11');temp.write_bytes(replacement[name]);os.chmod(temp,path.stat().st_mode&0o777);os.replace(temp,path)
    finally:subprocess.run(['systemctl','start','kodi'],check=True)
    print(json.dumps({'checkpoint':str(CHECKPOINT),'series':sha(series_b),
        'series_manifest':sha(series_manifest),'search_manifest':sha(search_manifest),
        'family':sha(family_b)},sort_keys=True))


if __name__=='__main__':main()
