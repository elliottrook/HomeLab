"""HP-only ID-bound TV-show route; other items retain Kodi's native Select."""
import hashlib,json,platform,re
from pathlib import Path

STAGE=Path('/storage/.kodi/addons/script.asterruntime/aster-series-preview24')
MANIFEST_SHA='aa589c8939b627aa19f9ec9b7abf9a0852eb3b33595b8c884e2b56f8ddb2dba0'

def selected_show(window,control,kind,identity,parent=False):
    if (window,control) not in ((10025,50),(10000,110)) or parent or kind!='tvshow':return None
    if not isinstance(identity,str) or re.fullmatch('[0-9]{1,10}',identity) is None:return None
    number=int(identity)
    return number if 0<number<=2147483647 else None

def launch_selected_show():
    if platform.node() not in ('AsterTV-Bedroom','AsterTV-Family'):return False
    import xbmc,xbmcgui
    window=xbmcgui.getCurrentWindowId()
    try:control=xbmcgui.Window(window).getFocusId()
    except RuntimeError:return False
    container=110 if (window,control)==(10000,110) else 50
    identity_label=xbmc.getInfoLabel('Container('+str(container)+').ListItem.DBID')
    if not identity_label:
        identity_label=xbmc.getInfoLabel('Container('+str(container)+').ListItem.Property(AsterDbId)')
    kind=xbmc.getInfoLabel('Container('+str(container)+').ListItem.DBTYPE')
    if not kind:
        kind=xbmc.getInfoLabel('Container('+str(container)+').ListItem.Property(AsterMediaKind)')
    identity=selected_show(window,control,kind,
        identity_label,
        xbmc.getCondVisibility('Container('+str(container)+').ListItem.IsParentFolder'))
    if identity is None:return False
    if xbmc.getInfoLabel('Window(Home).Property(AsterSeries.PreviewWindow)'):
        return True
    try:
        source=STAGE/'manifest.json'
        if hashlib.sha256(source.read_bytes()).hexdigest()!=MANIFEST_SHA:return False
        manifest=json.loads(source.read_text())
        if manifest.get('kind')!='hp-series-player' or len(manifest.get('files',[]))!=9:return False
        for row in manifest['files']:
            if hashlib.sha256((STAGE/row['path']).read_bytes()).hexdigest()!=row['sha256']:return False
    except (OSError,ValueError,KeyError,TypeError):return False
    xbmc.executebuiltin('RunScript(script.asterruntime,aster-series-preview24,default,'+str(identity)+',play)')
    return True
