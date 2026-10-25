"""Read only active compact-menu labels; never player URLs or credentials."""
import json,os,time
from pathlib import Path
import xbmc,xbmcgui
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
dialog=xbmcgui.getCurrentWindowDialogId()
value=dict(dialog=dialog,title=xbmcgui.Window(dialog).getProperty('Compact.Title'),
    count=xbmc.getInfoLabel('Container(10).NumItems'),selected=xbmc.getInfoLabel('Container(10).ListItem.Label'),
    first=xbmc.getInfoLabel('Container(10).ListItemAbsolute(0).Label'))
path=Path('/storage/.aster-checkpoints/aster-review2-20261025')/('menu-state-'+str(time.time_ns())+'.json')
path.write_text(json.dumps(value));path.chmod(0o600)
