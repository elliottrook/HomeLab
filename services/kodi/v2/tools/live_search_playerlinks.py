"""Actual HP Home entry -> search -> accepted child -> native source return."""
import fcntl,hashlib,json,os,sys,time
from pathlib import Path
import xbmc,xbmcgui
def require(value,reason):
    if not value:raise RuntimeError(reason)
require(os.uname().nodename=='AsterTV','hp-only')
# Never let one driver's finally/Back sequence act on another driver's child.
lock=os.open('/storage/.aster-checkpoints/aster-global-search-20261024/native-driver.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:
    os.close(lock);raise RuntimeError('native-driver-already-running')
name=sys.argv[1] if len(sys.argv)==2 else 'aster-global-search-ui5'
require(name in ('aster-global-search-ui5','aster-global-search-ui6','aster-global-search-ui7','aster-global-search-ui8','aster-global-search-ui9','aster-global-search-ui10','aster-global-search-ui11','aster-global-search-ui12'),'known-stage')
movie_linked=name in ('aster-global-search-ui10','aster-global-search-ui11','aster-global-search-ui12')
stage=Path('/storage/.aster-staging')/name
home=xbmcgui.Window(10000)
def prop(key):return home.getProperty('AsterSearch.'+key)
def rpc(method,params=None):
    require(method in {'Player.GetActivePlayers','Playlist.GetItems','Input.ExecuteAction','Input.SendText','Input.Home'},'native-input-only')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in reply,'native-request-failed');return reply['result']
def until(check,reason):
    end=time.monotonic()+40
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(80)
    raise RuntimeError(reason)
def press(action):rpc('Input.ExecuteAction',dict(action=action))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def idle():return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def label(key):return xbmc.getInfoLabel(key)
def enter():
    xbmc.executebuiltin('SetFocus(134)');until(lambda:xbmc.getCondVisibility('Control.HasFocus(134)'),'collections-focus')
    press('right');until(lambda:xbmc.getCondVisibility('Control.HasFocus(135)'),'normal-search-reachable')
    select();until(lambda:xbmcgui.getCurrentWindowId()==11127 and prop('Ready')=='true','normal-search-open')
    require(idle(),'search-entry-no-autoplay')
def query(value):
    xbmc.executebuiltin('SetFocus(10)');select()
    until(lambda:xbmcgui.getCurrentWindowDialogId()==10103,'native-keyboard')
    rpc('Input.SendText',dict(text=value,done=True))
    until(lambda:prop('Query')==value and prop('Ready')=='true','query-ready')
def result(index,kind):
    xbmc.executebuiltin('Control.SetFocus(20,'+str(index)+',absolute)')
    until(lambda:label('Container(30).ListItem.Property(Search.Kind)')==kind,'group-'+kind)
    press('right');until(lambda:xbmc.getCondVisibility('Control.HasFocus(30)'),'result-focus')
    press('down');xbmc.sleep(200)
    identity=label('Container(30).ListItem.Property(Search.Id)')
    title=label('Container(30).ListItem.Label');require(identity.isdecimal(),'indexed-result')
    select();until(lambda:xbmcgui.getCurrentWindowDialogId()==11128 and prop('DetailTitle')==title,'details-'+kind)
    return identity,title
def open_child(index,kind):
    identity,title=result(index,kind)
    require(prop('CanOpen')=='true','link-available-'+kind)
    if kind=='album':
        xbmc.executebuiltin('TakeScreenshot(/storage/.aster-checkpoints/aster-global-search-20261024/playerlink-detail-'+str(time.time_ns())+'.png)')
        xbmc.sleep(500)
    started=time.monotonic();xbmc.executebuiltin('SetFocus(11)');select()
    marker='AsterSeries.PreviewWindow' if kind=='tvshow' else 'AsterMovie.Window' if kind=='movie' else 'AsterV2Lab.AlbumWindow'
    until(lambda:home.getProperty(marker).isdecimal() and prop('Handoff')=='child','accepted-child-'+kind)
    expected=title if kind=='tvshow' else identity if kind in ('album','movie') else 'song-'+identity
    until(lambda:label('Window.Property(Series.Title)' if kind=='tvshow' else 'Window.Property(Movie.Id)' if kind=='movie' else 'Window.Property(Album.Id)')==expected,'exact-child-'+kind)
    require(idle(),'child-no-autoplay-'+kind)
    timings.setdefault(kind,[]).append(round((time.monotonic()-started)*1000))
    return identity,marker
checks=[];passed=False;failure=None;failure_state=None;timings={};started_test=time.monotonic()
try:
    require(idle() and xbmcgui.getCurrentWindowId()==10000 and not prop('Open'),'idle-home-required')
    home_shot='playerlink-home-'+str(time.time_ns())+'.png'
    xbmc.executebuiltin('TakeScreenshot(/storage/.aster-checkpoints/aster-global-search-20261024/'+home_shot+')');xbmc.sleep(500)
    require(hashlib.sha256((stage/'manifest.json').read_bytes()).hexdigest()==hashlib.sha256((Path('/storage/.aster-checkpoints/aster-global-search-20261024')/'active-manifest.json').read_bytes()).hexdigest(),'active-stage')
    enter();query('a');checks.append('normal-home-entry-no-autoplay')
    for index,kind in (((0,'tvshow'),(1,'movie'),(2,'album'),(4,'song')) if movie_linked else ((0,'tvshow'),(2,'album'),(4,'song'))):
        identity,marker=open_child(index,kind)
        press('back')
        until(lambda:xbmcgui.getCurrentWindowId()==11127 and prop('Ready')=='true' and not prop('Handoff')
            and not home.getProperty(marker),'child-back-'+kind)
        until(lambda:xbmc.getCondVisibility('Control.HasFocus(30)') and label('Container(30).ListItem.Property(Search.Kind)')==kind
            and label('Container(30).ListItem.Property(Search.Id)')==identity,'exact-search-return-'+kind)
        require(prop('Query')=='a' and idle(),'query-and-idle-'+kind)
        checks.append(kind+'-page-no-autoplay-exact-search-return')
    for index,kind in (() if movie_linked else ((1,'movie'),) if name in ('aster-global-search-ui7','aster-global-search-ui8','aster-global-search-ui9') else ((1,'movie'),(3,'artist'))):
        result(index,kind);require(prop('CanOpen')=='false','truthful-details-only-'+kind)
        press('back');until(lambda:xbmcgui.getCurrentWindowId()==11127 and not prop('DetailOpen'),'details-back')
    checks.append('all-video-music-types-connected' if movie_linked else 'unsupported-player-links-remain-details-only')
    if name in ('aster-global-search-ui7','aster-global-search-ui8','aster-global-search-ui9','aster-global-search-ui10','aster-global-search-ui11','aster-global-search-ui12'):
        artist_id,title=result(3,'artist')
        require(prop('CanOpen')=='true','artist-link-available')
        xbmc.executebuiltin('SetFocus(11)');select()
        until(lambda:xbmcgui.getCurrentWindowDialogId() in (0,9999)
            and prop('Query')=='Albums · '+title and prop('Ready')=='true'
            and label('Container(30).ListItem.Property(Search.Kind)')=='album','artist-albums-open')
        require(idle(),'artist-no-autoplay')
        album_id=label('Container(30).ListItem.Property(Search.Id)');require(album_id.isdecimal(),'artist-album-id')
        select();until(lambda:xbmcgui.getCurrentWindowDialogId()==11128,'artist-album-details')
        xbmc.executebuiltin('SetFocus(11)');select()
        until(lambda:prop('Handoff')=='child' and label('Window.Property(Album.Id)')==album_id,'artist-album-player')
        require(idle(),'artist-album-no-autoplay');press('back')
        until(lambda:xbmcgui.getCurrentWindowId()==(11129 if name in ('aster-global-search-ui8','aster-global-search-ui9','aster-global-search-ui10','aster-global-search-ui11','aster-global-search-ui12') else 11127) and not prop('Handoff') and prop('Ready')=='true'
            and label('Container(30).ListItem.Property(Search.Id)')==album_id and prop('Query')=='Albums · '+title,'artist-album-exact-return')
        xbmc.executebuiltin('TakeScreenshot(/storage/.aster-checkpoints/aster-global-search-20261024/artist-albums-'+str(time.time_ns())+'.png)')
        press('back')
        until(lambda:prop('Query')=='a' and prop('Ready')=='true'
            and label('Container(30).ListItem.Property(Search.Kind)')=='artist'
            and label('Container(30).ListItem.Property(Search.Id)')==artist_id
            and xbmc.getCondVisibility('Control.HasFocus(30)'),'artist-parent-exact-return')
        checks.append('artist-albums-player-back-exact-parent-return')
    open_child(2,'album');rpc('Input.Home')
    until(lambda:xbmcgui.getCurrentWindowId()==10000 and not prop('Handoff') and not prop('Open')
        and not home.getProperty('AsterV2Lab.AlbumWindow') and idle(),'global-home-exits-search')
    xbmc.sleep(1000);require(xbmcgui.getCurrentWindowId()==10000,'home-not-hijacked')
    checks.append('global-home-does-not-reopen-search')
    enter();query('AsterNoMatchQualificationXZQ901728')
    until(lambda:prop('Status')=='No matching titles in this group.' and label('Container(30).NumItems')=='0','explicit-empty')
    press('back');until(lambda:xbmcgui.getCurrentWindowId()==10000 and not prop('Open'),'search-back-home')
    until(lambda:xbmc.getCondVisibility('Control.HasFocus(135)'),'home-search-focus-restored')
    require(idle(),'final-idle-empty');checks.extend(['empty-results','home-entry-focus-restored']);passed=True
except Exception as error:
    value=str(error);failure=value if value.isascii() and len(value)<100 else 'native-test-failed'
    failure_state=dict(window=xbmcgui.getCurrentWindowId(),dialog=xbmcgui.getCurrentWindowDialogId(),
        result_kind=label('Container(30).ListItem.Property(Search.Kind)'),
        result_id=label('Container(30).ListItem.Property(Search.Id)'),
        original_query=prop('Query')=='a',ready=prop('Ready')=='true',handoff=prop('Handoff'),
        expected_id=locals().get('identity'),expected_kind=locals().get('kind'))
finally:
    if idle():
        for dialog in (10103,11128):
            if xbmcgui.getCurrentWindowDialogId()==dialog:press('back');xbmc.sleep(300)
        if home.getProperty('AsterV2Lab.AlbumWindow') or home.getProperty('AsterSeries.PreviewWindow'):
            press('back');xbmc.sleep(1200)
        if xbmcgui.getCurrentWindowId()==11130:press('back');xbmc.sleep(1200)
        if xbmcgui.getCurrentWindowId()==11129:press('back');xbmc.sleep(500)
        if xbmcgui.getCurrentWindowId()==11127:press('back');xbmc.sleep(500)
    clean=idle() and xbmcgui.getCurrentWindowId()==10000 and not any(home.getProperty(key) for key in ('AsterSearch.Open','AsterSearch.Handoff','AsterV2Lab.AlbumWindow','AsterSeries.PreviewWindow','AsterMovie.Window'))
    path=Path('/storage/.aster-checkpoints/aster-global-search-20261024')/('native-playerlinks-'+str(time.time_ns())+'.json')
    with path.open('x') as handle:json.dump(dict(stage=name,passed=passed,checks_enforced=True,checks=checks,failure=failure,failure_state=failure_state,
        idle_empty=clean,home_screenshot=locals().get('home_shot'),child_open_ms=timings,elapsed_ms=round((time.monotonic()-started_test)*1000),
        stage_manifest_sha256=hashlib.sha256((stage/'manifest.json').read_bytes()).hexdigest()),handle)
    path.chmod(0o600);os.close(lock);require(clean,'search-playerlinks-recovery-required')
