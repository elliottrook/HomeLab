"""HP-only isolated native search preview. Never opens media or child players."""
import fcntl,hashlib,json,os,sys,time
from pathlib import Path
import xbmc,xbmcgui
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'resources/lib'))
from global_search import SOURCES,READS,SearchUnavailable,search_group,normalize_query
PREFIX='AsterSearch.'
NATIVE=Path('/storage/.kodi/addons/skin.asterhome/1080i/custom_1127_search.xml')
DIRECTORY=Path('/storage/.aster-checkpoints/aster-global-search-20261024')

def require(value,reason):
    if not value:raise SearchUnavailable(reason)

def rpc(method,params=None):
    require(method in READS|{'Player.GetActivePlayers','Playlist.GetItems'},'read-only-search-boundary')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    if 'error' in reply:raise SearchUnavailable('native-read-unavailable')
    return reply.get('result',{})

def main():
    if os.uname().nodename!='AsterTV':return
    DIRECTORY.mkdir(mode=0o700,parents=True,exist_ok=True)
    fd=os.open(DIRECTORY/'entry.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    home=xbmcgui.Window(10000);opened=False;admitted=False
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return
        admitted=True
        require(xbmcgui.getCurrentWindowId()==10000 and not rpc('Player.GetActivePlayers'),'idle-home-required')
        require(all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1)),'empty-queues-required')
        manifest=json.loads((ROOT/'manifest.json').read_text())
        require(manifest.get('kind')=='hp-search-preview','search-preview-stage')
        require(all(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in manifest['files']),'stage-integrity')
        native=next(r for r in manifest['files'] if r['path']=='overlay/custom_1127_search.xml')
        require(hashlib.sha256(NATIVE.read_bytes()).hexdigest()==native['sha256'],'native-search-not-verified')
        for key in ('Command','Query','Status','Detail','Ready'):home.clearProperty(PREFIX+key)
        home.setProperty(PREFIX+'Query','Search titles…')
        home.setProperty(PREFIX+'Status','Search this box’s synced TV, film and music index.')
        xbmc.executebuiltin('ActivateWindow(1127)');opened=True
        monitor=xbmc.Monitor();end=time.monotonic()+10
        while not xbmc.getCondVisibility('Window.IsVisible(11127)'):
            require(time.monotonic()<end and not monitor.waitForAbort(.05),'search-window-not-ready')
        window=xbmcgui.Window(11127);categories=window.getControl(20);results=window.getControl(30)
        groups=[];current=-1;query='';positions={}
        def display(index):
            nonlocal current
            if 0<=current<len(groups):positions[current]=results.getSelectedPosition()
            current=index;results.reset();home.setProperty(PREFIX+'Detail','')
            if not groups:return
            group=groups[index]
            for hit in group.hits:
                item=xbmcgui.ListItem(label=hit.title,label2=hit.detail)
                item.setProperty('Search.Kind',hit.kind);item.setProperty('Search.Id',str(hit.identity))
                results.addItem(item)
            if group.hits:results.selectItem(min(max(positions.get(index,0),0),len(group.hits)-1))
            state={'empty':'No matching titles in this group.',
                   'unavailable':'This source could not be checked. Try Search again.',
                   'idle':'Enter a title to search.'}.get(group.state)
            if state is None:
                state=(f'Showing first {len(group.hits)} of {group.total} matches — refine your search.'
                       if group.truncated else f'{group.total} matches · synced local index')
            home.setProperty(PREFIX+'Status',state)
        def run_query(value):
            nonlocal groups,current,query,positions
            query=normalize_query(value);positions={};home.setProperty(PREFIX+'Ready','')
            home.setProperty(PREFIX+'Query',query or 'Search titles…')
            categories.reset();results.reset();groups=[];current=-1
            for source in SOURCES:
                home.setProperty(PREFIX+'Status','Searching '+source.label.lower()+'…')
                group=search_group(rpc,source,query,cancelled=lambda:monitor.abortRequested() or not xbmc.getCondVisibility('Window.IsVisible(11127)'))
                groups.append(group)
                suffix='Unavailable' if group.state=='unavailable' else str(group.total) if query else '—'
                categories.addItem(xbmcgui.ListItem(label=group.label,label2=suffix))
            categories.selectItem(0);display(0);home.setProperty(PREFIX+'Ready','true')
        run_query('')
        while xbmc.getCondVisibility('Window.IsVisible(11127)') and not monitor.abortRequested():
            command=home.getProperty(PREFIX+'Command')
            if command:
                home.clearProperty(PREFIX+'Command')
                if command=='query':
                    keyboard=xbmc.Keyboard(query,'Search titles on this Aster box')
                    keyboard.doModal()
                    if keyboard.isConfirmed():
                        try:run_query(keyboard.getText())
                        except SearchUnavailable as error:
                            if str(error)=='cancelled':break
                            home.setProperty(PREFIX+'Status','Use up to 100 characters and eight words.')
                elif command=='details' and 0<=current<len(groups):
                    index=results.getSelectedPosition();hits=groups[current].hits
                    if 0<=index<len(hits):
                        hit=hits[index]
                        home.setProperty(PREFIX+'Detail',hit.title+'[CR]'+hit.detail+'[CR]Preview only · opening this result is not connected yet.')
            index=categories.getSelectedPosition()
            if 0<=index<len(groups) and index!=current:display(index)
            if monitor.waitForAbort(.05):break
    except (ValueError,OSError,KeyError,StopIteration):
        xbmcgui.Dialog().notification('Search unavailable','Return to Home and try again. Nothing was played.')
    finally:
        if opened:xbmc.executebuiltin('Dialog.Close(11127)')
        if admitted:
            for key in ('Open','Command','Query','Status','Detail','Ready'):home.clearProperty(PREFIX+key)
        os.close(fd)

if __name__=='__main__':main()
