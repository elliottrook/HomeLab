"""HP-only ID-bound TV-show route; other items retain Kodi's native Select."""
import hashlib,json,platform,re
from pathlib import Path

STAGE=Path('/storage/.aster-staging/@SERIES_STAGE@')
MANIFEST_SHA='@SERIES_SHA@'

def selected_show(window,control,kind,identity,parent=False):
    if window!=10025 or control!=50 or parent or kind!='tvshow':return None
    if not isinstance(identity,str) or re.fullmatch('[0-9]{1,10}',identity) is None:return None
    number=int(identity)
    return number if 0<number<=2147483647 else None

def launch_selected_show():
    if platform.node()!='AsterTV':return False
    import xbmc,xbmcgui
    window=xbmcgui.getCurrentWindowId()
    try:control=xbmcgui.Window(window).getFocusId()
    except RuntimeError:return False
    identity=selected_show(window,control,xbmc.getInfoLabel('Container(50).ListItem.DBTYPE'),
        xbmc.getInfoLabel('Container(50).ListItem.DBID'),xbmc.getCondVisibility('Container(50).ListItem.IsParentFolder'))
    if identity is None:return False
    if xbmc.getInfoLabel('Window(Home).Property(AsterSeries.PreviewWindow)'):
        return True
    try:
        source=STAGE/'manifest.json'
        if hashlib.sha256(source.read_bytes()).hexdigest()!=MANIFEST_SHA:return False
        manifest=json.loads(source.read_text())
        if manifest.get('kind')!='hp-series-player' or len(manifest.get('files',[]))!=6:return False
        for row in manifest['files']:
            if hashlib.sha256((STAGE/row['path']).read_bytes()).hexdigest()!=row['sha256']:return False
    except (OSError,ValueError,KeyError,TypeError):return False
    xbmc.executebuiltin('RunScript('+str(STAGE/'default.py')+','+str(identity)+',play)')
    return True
