"""HP series page: read-only by default, explicit ID-only native playback mode."""
import importlib.util,json,os,sys,time
from dataclasses import replace
from pathlib import Path
import xbmc,xbmcgui

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'resources/lib'))
from series_adapter import read_series,READS
from series_model import SeriesUnavailable
from series_view import SeriesSelection,episode_metadata
from series_playback import EpisodeSession,PLAYER_READS,entry_lock
from series_catalogue import merge_page,season_proposal
from series_seerr_client import (CatalogueClient,CatalogueUnavailable,
    GrayscaleCache,SeasonRequestWriter)
BACK={9,10,92,216,247,257,275}

def rpc(method,params=None):
    if method not in READS|PLAYER_READS:
        raise SeriesUnavailable('read-only-series-preview')
    return execute(method,params)

def execute(method,params=None):
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    if 'error' in result:raise SeriesUnavailable('local-series-read-failed')
    return result.get('result',{})

def playback_rpc(method,params):
    if method not in READS|PLAYER_READS|{'Player.Open','Player.Stop'}:raise SeriesUnavailable('series-player-boundary')
    return execute(method,params)

def recovery_path():return Path('/storage/.aster-checkpoints/aster-series-playback-20261024/unresolved-start.json')

def idle():
    return not rpc('Player.GetActivePlayers') and all(
        rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))

def accepted_next():
    spec=importlib.util.spec_from_file_location('aster_accepted_upnext','/storage/.kodi/addons/plugin.video.asterhome/library.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.next_up_item

class SeriesPreview(xbmcgui.WindowXML):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.ready=False;self.finished=False;self.identity=None;self.updating=False;self.pending_index=None
        self.playback_enabled=False;self.session=None;self.close_requested=False;self.refresh_due=0;self.next_poll=0
        self.fullscreen_requested=False;self.return_deadline=0;self.restore_due=0
        self.catalogue=None;self.catalogue_client=None;self.catalogue_loaded={};self.catalogue_base=None
        self.catalogue_cache=None;self.season_writer=None;self.request_arm=None
        self.last_playback_phase=None

    def onInit(self):
        if not self.ready:
            self.dialog_open=False;self.back_guard_until=0
            self.season_menu=False
            self.selection=SeriesSelection(self.snapshot.page,self.snapshot.page.primary_episode_id)
        self.season_menu=getattr(self,'season_menu',False)
        self.setProperty('Series.SeasonMenu','true' if self.season_menu else 'false')
        self.setProperty('Series.Title',self.snapshot.title)
        self.setProperty('Series.Synopsis',self.snapshot.synopsis or 'Synopsis unavailable')
        self.setProperty('Series.Fanart',self.snapshot.fanart)
        metadata=' / '.join(self.snapshot.genres)
        if self.snapshot.year:metadata+='  [COLOR ff91c6a2]'+str(self.snapshot.year)+'[/COLOR]'
        self.setProperty('Series.Metadata',metadata)
        score=f'Score {self.snapshot.rating:.1f} / 10' if self.snapshot.rating else ''
        self.setProperty('Series.Rating','  '.join(x for x in (score,self.snapshot.certificate) if x))
        self.setProperty('Series.Multiple','true' if self.snapshot.page.show_season_picker else 'false')
        self.setProperty('Series.Empty','true' if not self.snapshot.page.seasons else 'false')
        self.setProperty('Series.Mode','TV SERIES · OK plays · Menu for details' if self.playback_enabled else 'HP SERIES PREVIEW · NO PLAYBACK')
        self.setProperty('Series.Status','')
        primary=self.snapshot.page.primary_episode_id
        row=next((e for s in self.snapshot.page.seasons for e in s.episodes if e.episode_id==primary),None)
        label={'resume':'Resume','next':'Play next','play':'Play'}.get(self.snapshot.page.primary_action,'Browse episodes')
        self.setProperty('Series.Primary',label+(' · '+row.numbering if row else '')+('' if self.playback_enabled else ' · preview'))
        if self.playback_enabled and self.session is None:self.session=EpisodeSession(playback_rpc,self.snapshot.page.show_id,self.following_id)
        self.populate()
        self.setFocusId(300 if self.selection.group else 202)
        # On return Kodi invokes onInit before changing current-window metadata.
        # Keep the allocated ID; never replace it with Home/fullscreen's ID.
        if self.identity is None:self.identity=xbmcgui.getCurrentWindowId()
        self.ready=True
        xbmcgui.Window(10000).setProperty('AsterSeries.PreviewWindow',str(self.identity))
        self.publish()

    def populate(self):
        self.setProperty('Series.Ready','false')
        group=self.selection.group
        self.setProperty('Series.Season',group.label if group else 'No episodes')
        self.setProperty('Series.SeasonIndex',str(self.selection.season))
        rows=[]
        for index,row in enumerate(group.episodes if group else ()):
            item=xbmcgui.ListItem(label=row.title)
            item.setProperty('Selected','true' if index==self.selection.index else 'false')
            item.setProperty('EpisodeId',str(row.episode_id) if row.episode_id else '');item.setProperty('Synopsis',row.synopsis or 'Synopsis unavailable')
            item.setProperty('Metadata',episode_metadata(row))
            item.setProperty('Still',row.thumbnail);item.setProperty('HasStill','true' if row.thumbnail else 'false')
            item.setProperty('Progress',str(row.progress_percent or 0))
            item.setProperty('HasProgress','true' if row.progress_percent is not None else 'false')
            item.setProperty('State',('Catalogue · not in your library' if row.catalogue else
                'Watched' if row.watched else 'In progress' if row.progress_percent is not None else ''))
            item.setProperty('Missing','true' if row.catalogue else 'false')
            if row.catalogue:
                request=('Request Season '+str(row.season) if row.requestable else
                    'Season request '+row.request_state if row.request_state!='none' else 'Not in your library')
            else:request='' if row.available else 'Not available'
            item.setProperty('Unavailable',request)
            rows.append(item)
        self.pending_index=self.selection.index if rows else None
        self.marked_index=self.pending_index
        self.getControl(300).reset();self.getControl(300).addItems(rows)
        if rows:self.getControl(300).selectItem(self.pending_index)

    def publish(self):
        if not self.ready or self.updating or self.dialog_open:return
        if self.selection.group:
            position=self.getControl(300).getSelectedPosition()
            if self.pending_index is not None and position!=self.pending_index:return
            if position!=self.marked_index and 0<=position<len(self.selection.group.episodes):
                armed=self.request_arm is not None
                self.request_arm=None
                if armed:self.setProperty('Series.Status','OK plays the selected episode · Back returns to library')
                if self.marked_index is not None:self.getControl(300).getListItem(self.marked_index).setProperty('Selected','false')
                self.getControl(300).getListItem(position).setProperty('Selected','true');self.marked_index=position
            self.pending_index=None;self.selection.select(position)
        row=self.selection.episode
        self.setProperty('Series.SelectedId',str(row.episode_id) if row and row.episode_id else '')
        self.setProperty('Series.Ready','true')

    def consume_command(self):
        command=self.getProperty('Series.Command')
        if not command:return
        self.clearProperty('Series.Command')
        if command=='select':
            try:identity=self.getFocusId()
            except RuntimeError:return
            if identity in (200,201,202,300,311,312,313,314,315):self.onClick(identity)

    def onClick(self,identity):
        if not self.ready or self.finished:return
        if identity==202:self.close()
        elif identity==201:
            self.publish()
            self.season_menu=not self.season_menu
            self.setProperty('Series.SeasonMenu','true' if self.season_menu else 'false')
            if self.season_menu:
                self.season_cursor=self.selection.season
                self.draw_seasons()
            else:self.setFocusId(201)
        elif 311<=identity<=315 and self.season_menu:
            index=self.season_start+identity-311
            self.season_menu=False;self.setProperty('Series.SeasonMenu','false')
            self.updating=True
            try:
                number=self.snapshot.page.seasons[index].number
                self.load_catalogue_season(number)
                index=next(i for i,row in enumerate(self.snapshot.page.seasons) if row.number==number)
                changed=self.selection.change_season(index)
                if changed:self.populate();self.setFocusId(300)
                else:self.setFocusId(201)
            except (CatalogueUnavailable,ValueError,OSError):
                self.setProperty('Series.Status','The complete season catalogue is temporarily unavailable.')
                self.setFocusId(201)
            finally:self.updating=False
            self.publish()
        elif identity in (200,300):
            self.publish()
            if self.pending_index is not None:return
            row=self.selection.episode
            if identity==200:
                primary=next((e for s in self.snapshot.page.seasons for e in s.episodes
                    if e.episode_id==self.snapshot.page.primary_episode_id),None)
                if self.playback_enabled and primary is None:self.setFocusId(300);return
                row=primary or row
            if row:
                if row.catalogue:
                    self.request_missing(row);self.setFocusId(300);return
                if self.playback_enabled:
                    if self.session.phase not in ('idle',):return
                    self.setProperty('Series.Status','Opening '+row.numbering+'…')
                    self.fullscreen_requested=False
                    try:self.session.start(row.episode_id)
                    except Exception:
                        self.setProperty('Series.Status','Playback could not be verified. The request was not retried.')
                        if self.session.phase=='idle':self.dialog('ok','Episode unavailable','The episode or idle player could not be verified. Nothing was started.')
                else:self.details(row)
            if not self.playback_enabled:self.setFocusId(identity)

    def load_catalogue_season(self,number):
        if (self.catalogue is None or number is None or number in self.catalogue_loaded
                or not any(row.number==number for row in self.catalogue.seasons)):
            return
        self.setProperty('Series.Status','Loading complete episode catalogue…')
        detail=self.catalogue_client.season(self.catalogue,number)
        # Local episode art always wins during merge. Do not hold the page
        # while downloading catalogue duplicates for episodes already owned.
        local_numbers={row.number for group in self.catalogue_base.seasons
            if group.number==number for row in group.episodes
            if type(row.number) is int}
        detail=self.catalogue_cache.localize(detail,local_numbers)
        old_key=self.selection.episode.selection_key if self.selection.episode else None
        remembered=dict(self.selection.remembered)
        self.catalogue_loaded[number]=detail
        page=merge_page(self.catalogue_base,self.catalogue,self.catalogue_loaded.values())
        self.snapshot=replace(self.snapshot,page=page)
        self.selection=SeriesSelection(page,old_key);self.selection.remembered=remembered
        self.setProperty('Series.Status','')

    def request_missing(self,row):
        if not row.requestable:
            state=row.request_state.replace('_',' ')
            self.setProperty('Series.Status',('Season request '+state if state!='none'
                else 'This season is not currently requestable.'))
            return
        key=(self.catalogue.candidate_id,row.season)
        if self.request_arm!=key:
            self.request_arm=key
            self.setProperty('Series.Status','Press OK again to request Season '+str(row.season)+' in Seerr')
            return
        self.request_arm=None
        try:
            payload=season_proposal(self.catalogue,row.season,True)
            result=self.season_writer.submit(payload,self.catalogue)
            self.setProperty('Series.Status','Season '+str(row.season)+' request '+result['state'])
        except (CatalogueUnavailable,ValueError):
            self.setProperty('Series.Status','Request result uncertain or unavailable · nothing was retried')

    def draw_seasons(self):
        # A fixed slice avoids native list overscroll leaving empty rows at
        # the end. Cursor identity remains absolute across slice changes.
        count=len(self.snapshot.page.seasons);visible=min(5,count)
        start=min(max(self.season_cursor-2,0),max(0,count-visible))
        self.season_start=start
        for row in range(5):
            self.setProperty('Series.SeasonRow'+str(row),self.snapshot.page.seasons[start+row].label if row<visible else '')
        self.getControl(302).setHeight(visible*54+16)
        self.setFocusId(311+self.season_cursor-start)

    def details(self,row):
        self.dialog('ok','Episode information' if self.playback_enabled else 'Episode preview',
            row.numbering+' · '+row.title+'\n'+episode_metadata(row)+'\n\n'+(row.synopsis or 'Synopsis unavailable')+
            ('' if self.playback_enabled else '\n\nRead-only preview: nothing was played.'))

    def following_id(self,identity):
        spec=importlib.util.spec_from_file_location('aster_existing_episode_markers','/storage/.kodi/addons/skin.asterhome/tools/next_episode.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        rows=[dict(episodeid=e.episode_id,season=e.season or 0,episode=e.number or 0,
                   firstaired=e.first_aired,file='indexed' if e.available else '')
              for s in self.snapshot.page.seasons for e in s.episodes if e.episode_id is not None]
        current=next((r for r in rows if r['episodeid']==identity),None)
        result=module.following_episode(current,rows)
        return result.get('episodeid') if result else None

    def refresh_playback(self):
        if not self.session or time.monotonic()<self.next_poll:return
        self.next_poll=time.monotonic()+.2
        if self.session.poll():
            self.refresh_due=time.monotonic()+1;self.return_deadline=time.monotonic()+5
            # Script WindowXML pages are not native video navigation history.
            # Kodi may return to Home after fullscreen Back; explicitly restore
            # our still-live page only after the owned player has stopped.
            if not self.close_requested:self.restore_due=time.monotonic()+.75
        if (self.restore_due and time.monotonic()>=self.restore_due and idle()
                and xbmcgui.getCurrentWindowId()!=12005 and not self.close_requested):
            self.restore_due=0
            self.show()
            xbmc.executebuiltin('ActivateWindow('+str(self.identity)+')')
        if (self.session.phase=='playing' and self.selection.episode
                and self.session.expected!=self.selection.episode.episode_id
                and self.selection.follow_episode(self.session.expected)):
            self.pending_index=None
            if xbmcgui.getCurrentWindowId()==self.identity:self.populate()
        if self.session.phase=='playing' and not self.fullscreen_requested:
            self.fullscreen_requested=True
            if xbmcgui.getCurrentWindowId()==self.identity:xbmc.executebuiltin('ActivateWindow(fullscreenvideo)')
        self.setProperty('Series.Playback',self.session.phase)
        if self.session.phase!=self.last_playback_phase:
            self.last_playback_phase=self.session.phase
            if self.session.phase=='playing':self.setProperty('Series.Status','Playing · Back from video stops and returns here')
            elif self.session.phase=='idle':self.setProperty('Series.Status','OK plays the selected episode · Back returns to library')
            elif self.session.phase=='conflict':self.setProperty('Series.Status','Another player is active; it has not been interrupted.')
            elif self.session.phase=='recovery':self.setProperty('Series.Status','Playback result uncertain. No retry; close and check the player.')
        if self.refresh_due and time.monotonic()>=self.refresh_due and idle() and not self.dialog_open:
            self.refresh_due=0;old=self.selection
            try:
                snapshot=read_series(rpc,self.snapshot.page.show_id,accepted_next())
                self.catalogue_base=snapshot.page
                if self.catalogue is not None:
                    snapshot=replace(snapshot,page=merge_page(snapshot.page,self.catalogue,
                        self.catalogue_loaded.values()))
                selection=SeriesSelection(snapshot.page,old.episode.selection_key if old.episode else None)
                selection.remembered=dict(old.remembered)
                if old.group:
                    restored=snapshot.page.restore(old.episode.selection_key,season=old.group.number)
                    if restored:selection.season,selection.index=restored
                self.updating=True;self.snapshot=snapshot;self.selection=selection;self.populate()
                row=next((e for s in snapshot.page.seasons for e in s.episodes if e.episode_id==snapshot.page.primary_episode_id),None)
                label={'resume':'Resume','next':'Play next','play':'Play'}.get(snapshot.page.primary_action,'Browse episodes')
                self.setProperty('Series.Primary',label+(' · '+row.numbering if row else ''))
            except Exception:self.setProperty('Series.Status','Library is still syncing; reopen later to refresh progress.')
            finally:self.updating=False
        if self.close_requested and self.session.can_close and self.safe_to_close():self.finish_close()

    def safe_to_close(self):
        # Closing a hidden WindowXML can restore its source window, unloading
        # fullscreen video and indirectly stopping an unrelated native player.
        return not (self.session and self.session.phase in ('conflict','recovery') and rpc('Player.GetActivePlayers'))

    def dialog(self,method,*args,**kwargs):
        self.dialog_open=True
        try:return getattr(xbmcgui.Dialog(),method)(*args,**kwargs)
        finally:self.dialog_open=False;self.back_guard_until=time.monotonic()+.3

    def onAction(self,action):
        if not self.ready or self.finished:return
        key=action.getId()
        try:control=self.getFocusId()
        except RuntimeError:return
        if 311<=control<=315 and self.season_menu and key in (3,4):
            self.season_cursor=max(0,min(len(self.snapshot.page.seasons)-1,self.season_cursor+(-1 if key==3 else 1)))
            self.draw_seasons();return
        if control==300 and key in (3,4):self.pending_index=None
        if key in BACK:
            if xbmcgui.getCurrentWindowId()!=self.identity:return
            if self.season_menu:
                self.season_menu=False;self.setProperty('Series.SeasonMenu','false');self.setFocusId(201);return
            if not self.dialog_open and time.monotonic()>=self.back_guard_until:self.close()
            return
        if self.playback_enabled and key in (11,117) and self.selection.episode:
            self.publish();self.details(self.selection.episode);self.setFocusId(control);return
        if control==300 and key==3 and self.selection.index==0 and self.snapshot.page.show_season_picker:self.setFocusId(201)
        elif control==300 and key==1:self.setFocusId(200)
        elif control in (200,201) and key==2 and self.selection.group:self.setFocusId(300)

    def close(self):
        if self.finished:return
        if self.session:
            self.close_requested=True;self.session.cancel()
            if not self.session.can_close or not self.safe_to_close():return
        self.finish_close()

    def finish_close(self):
        if self.finished:return
        if not self.safe_to_close():return
        self.record_recovery()
        self.finished=True;super().close()

    def record_recovery(self):
        if self.session and self.session.phase=='recovery':
            path=recovery_path();path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
            if not path.exists():
                with path.open('x') as output:json.dump(dict(show_id=self.session.show_id,episode_id=self.session.expected,
                    error=self.session.error,time=int(time.time())),output)
                path.chmod(0o600)
            xbmcgui.Window(10000).setProperty('AsterSeries.Recovery','required')

def run_entry():
    if os.uname().nodename!='AsterTV':return
    try:
        if len(sys.argv) not in (2,3) or not sys.argv[1].isdecimal() or (len(sys.argv)==3 and sys.argv[2]!='play'):
            raise SeriesUnavailable('invalid-show-link')
        playback=len(sys.argv)==3
        if playback and recovery_path().exists():raise SeriesUnavailable('unresolved-series-start')
        if not idle():raise SeriesUnavailable('idle-player-required')
        show_id=int(sys.argv[1]);snapshot=read_series(rpc,show_id,accepted_next())
    except Exception:
        xbmcgui.Dialog().ok('Series unavailable','The complete idle series snapshot could not be verified, or an earlier start needs review. Nothing was started.');return
    home=xbmcgui.Window(10000)
    if home.getProperty('AsterSeries.PreviewWindow'):return
    window=SeriesPreview('SeriesPreview.xml',str(ROOT),'Default','1080i')
    window.catalogue_base=snapshot.page
    try:
        if snapshot.tvdb_id:
            client=CatalogueClient('http://192.168.20.40:8788',Path('/storage/.aster-private/seerr-token'))
            catalogue=client.resolve(snapshot.tvdb_id,snapshot.title)
            page=merge_page(snapshot.page,catalogue)
            position=page.restore(page.primary_episode_id) or (0,0)
            number=page.seasons[position[0]].number if page.seasons else None
            loaded={}
            cache=GrayscaleCache('/storage/.kodi/userdata/addon_data/script.asterseries/catalogue-stills')
            if number is not None and any(row.number==number for row in catalogue.seasons):
                loaded[number]=cache.localize(client.season(catalogue,number))
                page=merge_page(snapshot.page,catalogue,loaded.values())
            snapshot=replace(snapshot,page=page)
            window.catalogue=catalogue;window.catalogue_client=client
            window.catalogue_loaded=loaded;window.catalogue_cache=cache
            window.season_writer=SeasonRequestWriter('/storage/.aster-private/seerr-season-journal',client.request_season)
    except (CatalogueUnavailable,ValueError,OSError):
        pass
    window.snapshot=snapshot;window.playback_enabled=playback
    source=xbmcgui.getCurrentWindowId();previous=0
    try:
        previous=xbmcgui.Window(source).getFocusId()
        window.show();monitor=xbmc.Monitor();deadline=time.monotonic()+15
        while not monitor.abortRequested() and not window.finished:
            if not window.ready:
                if time.monotonic()>deadline:raise SeriesUnavailable('preview-initialization-timeout')
            else:
                window.consume_command()
                window.refresh_playback()
                if window.finished:break
                visible=xbmc.getCondVisibility('Window.IsVisible('+str(window.identity)+')')
                if not visible and (not window.session
                        or (window.session.phase in ('conflict','recovery') and window.safe_to_close())):break
                if (not visible and window.session and window.session.phase=='idle'
                        and not xbmc.getCondVisibility('Player.HasVideo') and time.monotonic()>=window.return_deadline):break
                if visible:window.publish()
            if monitor.waitForAbort(.1):break
    finally:
        window.close();home.clearProperty('AsterSeries.PreviewWindow')
        if not window.finished and window.session:
            end=time.monotonic()+32
            while not window.finished and time.monotonic()<end and not xbmc.Monitor().abortRequested():
                try:window.refresh_playback()
                except Exception:break
                xbmc.sleep(100)
            if not window.finished:
                window.session.phase='recovery';window.session.error='series-exit-not-confirmed';window.record_recovery()
                # Do not destroy the hidden scripted window underneath unknown
                # video: that can unload fullscreen and stop another player.
                # Remain read-only until it ends or Kodi itself shuts down.
                while not xbmc.Monitor().abortRequested() and not window.safe_to_close():xbmc.sleep(500)
                window.finish_close()
        for _ in range(20):
            if xbmcgui.getCurrentWindowId()==source:break
            xbmc.sleep(50)
        if xbmcgui.getCurrentWindowId()==source and previous:xbmc.executebuiltin('SetFocus('+str(previous)+')')
        del window

def main():
    if os.uname().nodename!='AsterTV':return
    try:
        with entry_lock(recovery_path().parent):run_entry()
    except SeriesUnavailable:
        xbmcgui.Dialog().notification('Aster series','The series page is already opening or needs review. Nothing was retried.')

if __name__=='__main__':main()
