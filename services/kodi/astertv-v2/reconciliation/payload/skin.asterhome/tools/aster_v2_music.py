"""HP normal skin adapter: emit only literal commands with verified-shaped IDs."""
import platform
import json
import re
from urllib.parse import parse_qs,urlsplit


PAGES={'home':11113,'albums':11114,'artists':11115,'songs':11116,'playlists':11117}
RETURN='AsterMusic.V2Return'


def selection_key(page,identifier,path=''):
    kind='artist' if page=='artists' else 'song' if page=='songs' else 'playlist' if page=='playlists' else 'album'
    value=identifier
    if kind=='playlist':
        if isinstance(path,str) and path.startswith('special://musicplaylists/'):
            return None  # Preserve existing local/smart playlist resolution.
        parsed=urlsplit(path) if isinstance(path,str) and len(path)<=8192 else None
        query=parse_qs(parsed.query) if parsed else {}
        values=query.get('folder',[])
        valid=(parsed is not None and parsed.scheme=='plugin' and parsed.netloc=='plugin.video.jellyfin'
            and not parsed.fragment and query.get('mode')==['browse'] and query.get('type')==['playlists']
            and len(values)==1)
        value=values[0] if valid else ''
        if re.fullmatch(r'[0-9a-fA-F]{32}|[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}',value):
            value=value.replace('-','').lower()
        else:valid=False
    else:
        valid=(page in ('home','albums','artists','songs') and isinstance(value,str)
            and re.fullmatch('[0-9]{1,10}',value) is not None and 0<int(value)<=2147483647)
        if valid:value=str(int(value))
    if not valid:raise ValueError('invalid-music-identity')
    return kind+':'+value


def handoff(xbmc,xbmcgui,page,identifier,path=''):
    if platform.node() not in ('AsterTV','AsterTVProd') or not xbmc.getCondVisibility('System.HasAddon(script.astermusic.v2lab)'):
        return False
    if page=='artists':return False
    try:key=selection_key(page,identifier,path)
    except ValueError:
        xbmcgui.Dialog().ok('Music selection unavailable','This selection has no verified indexed identity. Nothing was played.')
        return True
    if key is None:return False
    kind,value=key.split(':',1)
    xbmcgui.Window(PAGES[page]).setProperty(RETURN,json.dumps(dict(schema=1,key=key,focus=500)))
    xbmc.executebuiltin('RunScript(script.astermusic.v2lab,'+kind+','+value+')')
    return True


def restore_focus(xbmc,window,page,rows):
    raw=window.getProperty(RETURN);window.clearProperty(RETURN)
    if not isinstance(raw,str) or len(raw)>512:return False
    try:
        state=json.loads(raw)
        if set(state)!={'schema','key','focus'} or state['schema']!=1 or type(state['focus']) is not int or state['focus'] not in (500,114,115):return False
        matches=[]
        for index,row in enumerate(rows):
            try:key=selection_key(page,str(row['id'] or ''),row.get('file',''))
            except ValueError:continue
            if key is not None and key==state['key']:matches.append(index)
        if len(matches)!=1:return False
        xbmc.executebuiltin('CancelAlarm(AsterMusicFocus,silent)')
        xbmc.executebuiltin(f'AlarmClock(AsterMusicFocus,Control.SetFocus(500,{matches[0]},absolute),00:00:01,silent)')
        if state['focus']!=500:xbmc.executebuiltin('SetFocus('+str(state['focus'])+')')
        return True
    except (ValueError,TypeError,KeyError):return False


def open_route(xbmc,xbmcgui,route,page):
    if route not in ('genres','shuffle') or page not in PAGES or platform.node() not in ('AsterTV','AsterTVProd'):return
    if not xbmc.getCondVisibility('System.HasAddon(script.astermusic.v2lab)'):return
    try:key=selection_key(page,xbmc.getInfoLabel('Container(500).ListItem.Property(AsterMusic.Id)'),
        xbmc.getInfoLabel('Container(500).ListItem.Property(AsterMusic.File)'))
    except ValueError:key=None
    if key is not None:
        xbmcgui.Window(PAGES[page]).setProperty(RETURN,json.dumps(dict(schema=1,key=key,focus=114 if route=='genres' else 115)))
    xbmc.executebuiltin('RunScript(script.astermusic.v2lab,'+route+')')


if __name__=='__main__':
    import sys,xbmc,xbmcgui
    if len(sys.argv)==3:open_route(xbmc,xbmcgui,sys.argv[1],sys.argv[2])
