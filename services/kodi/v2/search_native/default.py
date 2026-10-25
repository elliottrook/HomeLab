"""HP-only native search; optional accepted-page links, no direct playback."""
import fcntl,hashlib,json,os,sys,time
from pathlib import Path
import xbmc,xbmcgui
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'resources/lib'))
from global_search import SOURCES,READS,SearchUnavailable,search_group,normalize_query
PREFIX='AsterSearch.'
DETAIL_READS=frozenset(('VideoLibrary.GetTVShowDetails','VideoLibrary.GetMovieDetails',
    'AudioLibrary.GetAlbumDetails','AudioLibrary.GetArtistDetails','AudioLibrary.GetSongDetails'))
NATIVE=Path('/storage/.kodi/addons/skin.asterhome/1080i/custom_1127_search.xml')
DIRECTORY=Path('/storage/.aster-checkpoints/aster-global-search-20261024')

def require(value,reason):
    if not value:raise SearchUnavailable(reason)

def rpc(method,params=None):
    require(method in READS|DETAIL_READS|{'Player.GetActivePlayers','Playlist.GetItems'},'read-only-search-boundary')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    if 'error' in reply:raise SearchUnavailable('native-read-unavailable')
    return reply.get('result',{})

def main():
    if os.uname().nodename!='AsterTV':return
    DIRECTORY.mkdir(mode=0o700,parents=True,exist_ok=True)
    fd=os.open(DIRECTORY/'entry.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    home=xbmcgui.Window(10000);opened=False;admitted=False;linked=False;source_focus=0
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return
        admitted=True
        require(not (DIRECTORY/'handoff-pending.json').exists(),'search-handoff-needs-review')
        require(xbmcgui.getCurrentWindowId()==10000 and not rpc('Player.GetActivePlayers'),'idle-home-required')
        source_focus=home.getFocusId()
        require(all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1)),'empty-queues-required')
        manifest=json.loads((ROOT/'manifest.json').read_text())
        require(manifest.get('kind') in ('hp-search-preview','hp-search-details','hp-search-playerlinks'),'search-stage')
        linked=manifest['kind']=='hp-search-playerlinks'
        movie_enabled=linked and manifest.get('movie_page')==11130
        details_enabled=manifest['kind'] in ('hp-search-details','hp-search-playerlinks')
        if linked:
            from search_handoff import Admission,Cursor,LABELS,restore_cursor,route_for,verify_child
        require(all(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in manifest['files']),'stage-integrity')
        native=next(r for r in manifest['files'] if r['path']=='overlay/custom_1127_search.xml')
        require(hashlib.sha256(NATIVE.read_bytes()).hexdigest()==native['sha256'],'native-search-not-verified')
        if details_enabled:
            from search_details import read_details
            for member,target in (('overlay/custom_1128_searchdetails.xml',NATIVE.with_name('custom_1128_searchdetails.xml')),
                                  ('overlay/select_dispatch.py',NATIVE.parent.parent/'tools/select_dispatch.py')):
                row=next(r for r in manifest['files'] if r['path']==member)
                require(hashlib.sha256(target.read_bytes()).hexdigest()==row['sha256'],'details-integration-not-verified')
        if linked:
            row=next(r for r in manifest['files'] if r['path']=='overlay/Home.xml')
            require(hashlib.sha256(NATIVE.with_name('Home.xml').read_bytes()).hexdigest()==row['sha256'],'normal-search-entry-not-verified')
            if manifest.get('artist_native_window')==11129:
                row=next(r for r in manifest['files'] if r['path']=='overlay/custom_1129_artistalbums.xml')
                require(hashlib.sha256(NATIVE.with_name('custom_1129_artistalbums.xml').read_bytes()).hexdigest()==row['sha256'],'artist-window-not-verified')
        for key in ('Command','Query','Status','Detail','Ready'):home.clearProperty(PREFIX+key)
        home.setProperty(PREFIX+'Query','Search titles…')
        home.setProperty(PREFIX+'Status','Search this box’s synced TV, film and music index.')
        xbmc.executebuiltin('ActivateWindow(1127)');opened=True
        monitor=xbmc.Monitor();end=time.monotonic()+10
        while not xbmc.getCondVisibility('Window.IsVisible(11127)'):
            require(time.monotonic()<end and not monitor.waitForAbort(.05),'search-window-not-ready')
        window=xbmcgui.Window(11127);categories=window.getControl(20);results=window.getControl(30)
        groups=[];current=-1;query='';positions={};active_detail=None;artist_context=None
        artist_enabled=linked and manifest.get('artist_albums') is True
        if artist_enabled:
            from global_search import Group
            from search_extensions import artist_albums
        def idle():
            return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
        def source_visible():return xbmcgui.getCurrentWindowId()==(11129 if artist_context and manifest.get('artist_native_window')==11129 else 11127) and xbmcgui.getCurrentWindowDialogId() in (0,9999)
        def attach(identity):
            nonlocal window,categories,results
            window=xbmcgui.Window(identity);categories=window.getControl(20);results=window.getControl(30)
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
            if artist_context:state=artist_context[0].title+' · '+state
            home.setProperty(PREFIX+'Status',state)
        def run_query(value):
            nonlocal groups,current,query,positions,artist_context
            if artist_context and manifest.get('artist_native_window')==11129:
                if xbmcgui.getCurrentWindowId()==11129:
                    xbmc.executebuiltin('ActivateWindow(1127)')
                    end=time.monotonic()+5
                    while xbmcgui.getCurrentWindowId()!=11127:
                        require(time.monotonic()<end and not monitor.waitForAbort(.05),'artist-parent-not-ready')
                attach(11127)
            artist_context=None
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
        def browse_artist(hit,parent):
            nonlocal groups,current,positions,artist_context
            detail=read_details(rpc,hit)
            value=artist_albums(rpc,hit.identity,cancelled=lambda:monitor.abortRequested() or not source_visible())
            artist_context=(detail.hit,parent)
            if manifest.get('artist_native_window')==11129:
                if xbmcgui.getCurrentWindowId()!=11129:
                    xbmc.executebuiltin('ActivateWindow(1129)')
                    end=time.monotonic()+5
                    while xbmcgui.getCurrentWindowId()!=11129:
                        require(time.monotonic()<end and not monitor.waitForAbort(.05),'artist-window-not-ready')
                attach(11129)
            groups=[Group('album','Artist albums','ready' if value['hits'] else 'empty',
                value['hits'],value['total'],value['truncated'])]
            current=-1;positions={};categories.reset();results.reset()
            categories.addItem(xbmcgui.ListItem(label='Artist albums',label2=str(value['total'])))
            home.setProperty(PREFIX+'Query','Albums · '+hit.title)
            categories.selectItem(0);display(0);home.setProperty(PREFIX+'Ready','true')
            xbmc.executebuiltin('SetFocus('+('30' if value['hits'] else '40')+')')
        def restore_search(cursor):
            run_query(cursor.query)
            return select_cursor(cursor)
        def select_cursor(cursor):
            home.clearProperty(PREFIX+'Ready')
            group_index,result_index=restore_cursor(groups,cursor)
            categories.selectItem(group_index);display(group_index)
            if result_index is not None:
                results.selectItem(result_index);positions[group_index]=result_index
                xbmc.executebuiltin('SetFocus(30)')
                # Native list selection arrives asynchronously. Do not let the
                # ordinary group-change loop save an old position over this
                # requested result while Kodi is still settling its controls.
                end=time.monotonic()+5;settled=0
                while settled<2:
                    if not source_visible():return False
                    require(time.monotonic()<end,'search-return-selection-not-ready')
                    matches=(categories.getSelectedPosition()==group_index and results.getSelectedPosition()==result_index
                        and xbmc.getInfoLabel('Container(30).ListItem.Property(Search.Id)')==str(cursor.identity)
                        and xbmc.getCondVisibility('Control.HasFocus(30)'))
                    settled=settled+1 if matches else 0
                    require(not monitor.waitForAbort(.05),'cancelled')
                positions[group_index]=result_index
            else:
                home.setProperty(PREFIX+'Status','That result no longer matches. Your search has been refreshed.')
                xbmc.executebuiltin('SetFocus(10)')
            home.setProperty(PREFIX+'Ready','true')
            return True
        run_query('')
        while (xbmc.getCondVisibility('Window.IsVisible(11127)') or xbmc.getCondVisibility('Window.IsVisible(11129)')) and not monitor.abortRequested():
            if artist_context and manifest.get('artist_native_window')==11129 and xbmcgui.getCurrentWindowId()==11127:
                restore_search(artist_context[1]);continue
            command=home.getProperty(PREFIX+'Command')
            if command:
                home.clearProperty(PREFIX+'Command')
                if command=='back' and artist_enabled:
                    if artist_context:restore_search(artist_context[1])
                    else:xbmc.executebuiltin('ActivateWindow(Home)')
                elif command=='query':
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
                        if linked and (hit.kind in LABELS or (artist_enabled and hit.kind=='artist') or (movie_enabled and hit.kind=='movie')):
                            # Use the real media page as the sole details page.
                            active_detail=hit;command='open'
                        elif details_enabled:
                            try:
                                detail=read_details(rpc,hit)
                                active_detail=detail.hit
                                for key,value in dict(DetailTitle=detail.hit.title,DetailMetadata=detail.hit.detail,
                                    DetailSynopsis=detail.synopsis,DetailHero=detail.hero,DetailArt=detail.artwork or 'special://skin/media/'+
                                    dict(tvshow='07-tv.png',movie='08-film.png',album='23-music-album.png',
                                         artist='24-music-artist.png',song='25-music-song.png')[hit.kind],DetailSource=detail.source).items():
                                    home.setProperty(PREFIX+key,value)
                                can_open=linked and (hit.kind in LABELS or (artist_enabled and hit.kind=='artist') or (movie_enabled and hit.kind=='movie'))
                                home.setProperty(PREFIX+'CanOpen','true' if can_open else 'false')
                                home.setProperty(PREFIX+'OpenLabel',('Browse artist albums' if hit.kind=='artist' else 'Open movie' if hit.kind=='movie' else LABELS.get(hit.kind,'')) if can_open else '')
                                home.setProperty(PREFIX+'DetailHint','Opens the existing page · select Play there' if can_open else 'Details only · player link not connected for this type')
                                xbmc.executebuiltin('ActivateWindow(1128)')
                            except SearchUnavailable:
                                home.setProperty(PREFIX+'Status','This result changed or is unavailable. Search again to refresh it.')
                        else:home.setProperty(PREFIX+'Detail','Browse-only preview · details are not connected.')
                if command=='open' and linked and active_detail and (source_visible() or xbmc.getCondVisibility('Window.IsVisible(11128)')):
                    admission=None
                    try:
                        if artist_enabled and active_detail.kind=='artist':
                            hit=read_details(rpc,active_detail).hit
                            require(idle(),'artist-source-not-idle')
                            parent=Cursor(query,'artist',hit.identity)
                            if xbmc.getCondVisibility('Window.IsVisible(11128)'):xbmc.executebuiltin('Dialog.Close(11128)')
                            until=time.monotonic()+5
                            while not source_visible():
                                require(time.monotonic()<until and not monitor.waitForAbort(.05),'artist-source-not-ready')
                            browse_artist(hit,parent);active_detail=None
                            continue
                        detail=read_details(rpc,active_detail);verify_child(detail.hit.kind,movie=movie_enabled)
                        route=route_for(detail.hit,movie=movie_enabled);cursor=Cursor(query,detail.hit.kind,detail.hit.identity)
                        if xbmc.getCondVisibility('Window.IsVisible(11128)'):xbmc.executebuiltin('Dialog.Close(11128)')
                        until=time.monotonic()+5
                        while not source_visible():
                            require(time.monotonic()<until and not monitor.waitForAbort(.05),'search-source-not-ready')
                        admission=Admission(route,time.monotonic())
                        command=admission.dispatch(idle=idle(),source_visible=source_visible())
                        home.setProperty(PREFIX+'Handoff','pending');home.clearProperty(PREFIX+'Ready')
                        xbmc.executebuiltin(command)
                        while not monitor.abortRequested():
                            marker=home.getProperty(route.marker)
                            ready=bool(marker and marker.isdecimal() and xbmcgui.getCurrentWindowId()==int(marker))
                            if detail.hit.kind=='tvshow':ready=ready and xbmc.getInfoLabel('Window.Property(Series.Ready)')=='true' and xbmc.getInfoLabel('Window.Property(Series.Title)')==route.expected
                            elif detail.hit.kind=='movie':ready=ready and xbmc.getInfoLabel('Window.Property(Movie.Ready)')=='true' and xbmc.getInfoLabel('Window.Property(Movie.Id)')==route.expected
                            else:ready=ready and xbmc.getInfoLabel('Window.Property(Album.Id)')==route.expected
                            phase=admission.observe(marker=marker,ready=ready,source_visible=source_visible(),
                                players=bool(rpc('Player.GetActivePlayers')),now=time.monotonic())
                            home.setProperty(PREFIX+'Handoff',phase)
                            if phase in ('restore','left','uncertain'):break
                            if monitor.waitForAbort(.1):break
                        if monitor.abortRequested():break
                        if phase=='uncertain':
                            path=DIRECTORY/'handoff-pending.json'
                            with path.open('x') as handle:json.dump(dict(kind=detail.hit.kind,identity=detail.hit.identity,time=int(time.time())),handle)
                            path.chmod(0o600)
                            break
                        if phase=='left':break
                        # Native child returns to the original search window.
                        # Re-read and restore by identity, never by its old offset.
                        attach(11129 if artist_context and manifest.get('artist_native_window')==11129 else 11127)
                        if artist_context:
                            artist,parent=artist_context;browse_artist(artist,parent)
                        else:run_query(cursor.query)
                        if not select_cursor(cursor):break
                        home.clearProperty(PREFIX+'Handoff');active_detail=None
                    except SearchUnavailable:
                        if admission is not None and admission.phase!='new':
                            path=DIRECTORY/'handoff-pending.json'
                            if not path.exists():
                                with path.open('x') as handle:json.dump(dict(kind=active_detail.kind,identity=active_detail.identity,time=int(time.time())),handle)
                                path.chmod(0o600)
                            break
                        home.setProperty(PREFIX+'DetailHint','The page or idle source could not be verified. Nothing was retried.')
                        home.setProperty(PREFIX+'Status','The page or idle source could not be verified. Search again to refresh.')
            index=categories.getSelectedPosition()
            if 0<=index<len(groups) and index!=current:display(index)
            if monitor.waitForAbort(.05):break
    except (ValueError,OSError,KeyError,StopIteration):
        xbmcgui.Dialog().notification('Search unavailable','Return to Home and try again. Nothing was played.')
    finally:
        if opened:
            xbmc.executebuiltin('Dialog.Close(11128)')
            if not linked:xbmc.executebuiltin('Dialog.Close(11127)')
            elif xbmcgui.getCurrentWindowId() in (11127,11129) and not rpc('Player.GetActivePlayers'):
                xbmc.executebuiltin('ActivateWindow(Home)')
        if admitted:
            for key in ('Open','Command','Query','Status','Detail','Ready','DetailOpen','DetailTitle',
                        'DetailMetadata','DetailSynopsis','DetailArt','DetailHero','DetailSource','CanOpen','OpenLabel','DetailHint','Handoff'):home.clearProperty(PREFIX+key)
            if source_focus and xbmcgui.getCurrentWindowId()==10000:xbmc.executebuiltin('SetFocus('+str(source_focus)+')')
        os.close(fd)

if __name__=='__main__':main()
