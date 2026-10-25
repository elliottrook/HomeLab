"""Minimal current-video Audio/Subtitles/Quality menus; no global defaults."""
import json,os,sys
import xbmc,xbmcgui
from compact_menu import choose

def rpc(method,params):
    if method not in ('Player.GetActivePlayers','Player.GetProperties','Player.SetAudioStream','Player.SetSubtitle'):
        raise ValueError('osd-method-boundary')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))))
    if 'error' in reply:raise ValueError('osd-request-unavailable')
    return reply['result']

def stream_label(row):
    # Labels only, never media URLs or paths. Native metadata is not markup.
    value=' · '.join(str(row.get(k,'')) for k in ('language','name','codec','channels') if row.get(k))
    return value.replace('[','(').replace(']',')')[:220] or 'Unnamed track'

def main(kind):
    if os.uname().nodename!='AsterTV' or kind not in ('audio','subtitles','quality'):return
    player=xbmc.Player()
    if not player.isPlayingVideo():return
    identity=player.getPlayingFile()
    def owned():
        try:
            active=rpc('Player.GetActivePlayers',{})
            return (player.isPlayingVideo() and player.getPlayingFile()==identity and len(active)==1
                    and active[0].get('playerid')==1 and active[0].get('type')=='video'
                    and active[0].get('playertype','internal')=='internal')
        except Exception:return False
    if not owned():return
    properties={'audio':['audiostreams','currentaudiostream'],
                'subtitles':['subtitles','currentsubtitle','subtitleenabled'],
                'quality':['currentvideostream']}[kind]
    def snapshot():return rpc('Player.GetProperties',dict(playerid=1,properties=properties))
    before=snapshot();selected=0
    if kind=='quality':
        row=before.get('currentvideostream',{})
        size=' × '.join(str(row.get(k,'?')) for k in ('width','height'))
        choose('Video quality',[size+' · '+str(row.get('codec','')).upper(),'Source quality · no conversion requested'],left=1130,top=680)
        return  # No invented transcode controls or hidden global settings.
    rows=before.get('audiostreams' if kind=='audio' else 'subtitles',[])
    if not isinstance(rows,list) or len(rows)>200:return
    current=before.get('currentaudiostream' if kind=='audio' else 'currentsubtitle',{}).get('index')
    labels=[('✓  ' if r.get('index')==current else '')+stream_label(r) for r in rows]
    if kind=='subtitles':labels.insert(0,'Subtitles: '+('On · select to turn off' if before['subtitleenabled'] else 'Off · select to turn on'))
    elif not rows:labels=['No selectable audio tracks']
    index=choose('Soundtrack' if kind=='audio' else 'Subtitles',labels,left=1130,top=500,selected=selected)
    if index<0 or not owned() or snapshot()!=before:return
    if kind=='subtitles' and index==0:
        rpc('Player.SetSubtitle',dict(playerid=1,subtitle='off' if before['subtitleenabled'] else 'on'));return
    offset=index-(1 if kind=='subtitles' else 0)
    if not 0<=offset<len(rows) or type(rows[offset].get('index')) is not int:return
    if kind=='audio':rpc('Player.SetAudioStream',dict(playerid=1,stream=rows[offset]['index']))
    else:rpc('Player.SetSubtitle',dict(playerid=1,subtitle=rows[offset]['index'],enable=True))

if __name__=='__main__':
    try:main(sys.argv[1])
    except Exception:xbmcgui.Dialog().notification('Aster','Tracks changed or are unavailable. Reopen the menu.')
