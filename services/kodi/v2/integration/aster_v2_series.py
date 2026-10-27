"""HP-only ID-bound TV-show route; other items retain Kodi's native Select."""
import hashlib,json,platform,re
from pathlib import Path

STAGE=Path('/storage/.aster-staging/@SERIES_STAGE@')
MANIFEST_SHA='@SERIES_SHA@'

def selected_show(window,control,kind,identity,parent=False):
    if (window,control) not in ((10025,50),(10000,110)) or parent or kind!='tvshow':return None
    if not isinstance(identity,str) or re.fullmatch('[0-9]{1,10}',identity) is None:return None
    number=int(identity)
    return number if 0<number<=2147483647 else None

def launch_selected_show():
    if platform.node()!='AsterTV':return False
    import xbmc,xbmcgui
    window=xbmcgui.getCurrentWindowId()
    try:control=xbmcgui.Window(window).getFocusId()
    except RuntimeError:return False
    container=110 if (window,control)==(10000,110) else 50
    identity_label=xbmc.getInfoLabel('Container('+str(container)+').ListItem.DBID')
    if not identity_label:
        identity_label=xbmc.getInfoLabel('Container('+str(container)+').ListItem.Property(AsterDbId)')
    identity=selected_show(window,control,xbmc.getInfoLabel('Container('+str(container)+').ListItem.DBTYPE'),
        identity_label,
        xbmc.getCondVisibility('Container('+str(container)+').ListItem.IsParentFolder'))
    if identity is None:return False
    if xbmc.getInfoLabel('Window(Home).Property(AsterSeries.PreviewWindow)'):
        return True
    try:
        source=STAGE/'manifest.json'
        if hashlib.sha256(source.read_bytes()).hexdigest()!=MANIFEST_SHA:return False
        manifest=json.loads(source.read_text())
        if manifest.get('kind')!='hp-series-player' or len(manifest.get('files',[]))!=8:return False
        for row in manifest['files']:
            if hashlib.sha256((STAGE/row['path']).read_bytes()).hexdigest()!=row['sha256']:return False
    except (OSError,ValueError,KeyError,TypeError):return False
    xbmc.executebuiltin('RunScript('+str(STAGE/'default.py')+','+str(identity)+',play)')
    return True
