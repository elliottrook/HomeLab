"""HP-only ID-bound TV-show route; other items retain Kodi's native Select."""
import hashlib,json,platform,re
from pathlib import Path

STAGE=Path('/storage/.kodi/addons/script.asterruntime/aster-series-preview24')
MANIFEST_SHA='c0ebd8db8d2afe49bcde302f2dd5392bed76d4c4a41b8175098b1acc81f399c2'

def selected_show(window,control,kind,identity,parent=False):
    if (window,control) not in ((10025,50),(10000,110)) or parent or kind!='tvshow':return None
    if not isinstance(identity,str) or re.fullmatch('[0-9]{1,10}',identity) is None:return None
    number=int(identity)
    return number if 0<number<=2147483647 else None

def launch_selected_show():
    if platform.node() not in ('AsterTV','AsterTVProd'):return False
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
        if manifest.get('kind')!='hp-series-player' or len(manifest.get('files',[]))!=8:return False
        for row in manifest['files']:
            if hashlib.sha256((STAGE/row['path']).read_bytes()).hexdigest()!=row['sha256']:return False
    except (OSError,ValueError,KeyError,TypeError):return False
    xbmc.executebuiltin('RunScript(script.asterruntime,aster-series-preview24,default,'+str(identity)+',play)')
    return True
