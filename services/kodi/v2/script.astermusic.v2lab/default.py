"""Isolated HP Music pilot with approved normal mode or expiring test grants."""
import json
from pathlib import Path
import platform
import sys
import time
import traceback
import threading
from types import SimpleNamespace

import xbmc
import xbmcgui

ROOT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'resources'/'lib'))
from lab_model import LabModel
from music_catalogue import CatalogueUnavailable, read_catalogue
from music_album import AlbumUnavailable, read_album
from music_selection import SelectionUnavailable,read_song
from music_audio import read_source,read_details
from music_playlists import PlaylistUnavailable,read_playlists,read_playlist,indexed_mapping,server_mapping
from music_jellyfin import PlaylistReader,PlaylistCreator
from music_shared_save import save_owned_queue
from music_playlist_save import PlaylistSaveUnavailable
from music_queue import propose,nonholiday_shuffle,QueueSnapshot
from music_scrub import ScrubPreview
from queue_reader import QueueUnavailable, read_queue
from music_trial import TrialPlayer,TrialUnavailable,capability,normal_playback_capability,save_empty_checkpoint,validate_write
from music_expanded_trial import ExpandedTrial,TrialCancelled,expanded_capability,save_intent
from music_progressive import ProgressiveSession,clock_milliseconds,clock_label,seek_owned

ASSETS = 'special://home/addons/skin.asterhome/media/'
READS = {'AudioLibrary.GetAlbums','AudioLibrary.GetArtists','AudioLibrary.GetSongs',
         'AudioLibrary.GetAlbumDetails','AudioLibrary.GetArtistDetails','AudioLibrary.GetSongDetails',
         'Player.GetActivePlayers','Player.GetProperties','Player.GetItem','Playlist.GetItems','XBMC.GetInfoLabels','Settings.GetSettingValue'}
BACK = {9,10,92,216,247,257,275}
DIRECTIONS = {1:'left',2:'right',3:'up',4:'down'}
ICONS = {'album':'23-music-album.png','artist':'24-music-artist.png','song':'25-music-song.png','playlist':'26-music-playlist.png'}


def rpc(method,params):
    if method not in READS: raise CatalogueUnavailable('read-only-pilot')
    if method=='Settings.GetSettingValue' and params!={'setting':'audiooutput.audiodevice'}:
        raise CatalogueUnavailable('read-only-pilot')
    return execute(method,params)


def execute(method,params):
    result=json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params})))
    if 'error' in result: raise CatalogueUnavailable('library-read-failed')
    return result.get('result',{})


def trial_directory():
    import xbmcvfs
    return Path(xbmcvfs.translatePath('special://profile/addon_data/script.astermusic.v2lab'))


def live_ids():
    return live_grant()[0]


def live_grant():
    return expanded_capability(trial_directory()/'live-trial.json',host=platform.node(),now=time.time())


def normal_playback():
    return normal_playback_capability(trial_directory()/'normal-playback.json',host=platform.node())


def playback_allowed(ids,limit):
    if len(ids)>limit:return False
    if normal_playback() and limit==20000:return True
    granted,current_limit=live_grant()
    return limit==current_limit and set(ids)<=set(granted)


def load_catalogue():
    progress=xbmcgui.DialogProgress()
    progress.create('Aster Music v2 Lab','Checking the complete music catalogue…')
    cancelled=False; calls=0
    def read(method,params):
        nonlocal cancelled,calls
        if progress.iscanceled() or xbmc.Monitor().abortRequested():
            cancelled=True; raise CatalogueUnavailable('cancelled')
        calls+=1
        progress.update(min(95,calls*2),'Reading genres and artist links. No playback changes.')
        return rpc(method,params)
    try:
        return read_catalogue(read),None
    except CatalogueUnavailable as error:
        return None,'Refresh cancelled' if cancelled else 'Catalogue unavailable · '+str(error)
    except Exception:
        return None,'Catalogue unavailable · unexpected-read-error'
    finally: progress.close()


class AlbumLab(xbmcgui.WindowXML):
    """Read-only by default; optional explicitly approved bounded HP trial."""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.selection=None; self.title=''; self.artwork='';self.allowed=();self.trial=None;self.finished=False
        self.dialog_open=False;self.back_guard_until=0
        self.queue_limit=3
        self.scrub=None;self.next_player_update=0
        self.control_worker=None;self.control_errors=[]
        self.display_ids=None;self.queue_view=False;self.rendered_queue=None
        self.marked_index=None
        self.control_labels={400:'Play / Pause',404:'Stop',401:'Play Next',402:'Add to Queue',403:'Replace Queue',405:'Back 10 seconds',406:'Forward 10 seconds'}

    def configure_controls(self,shuffle=False):
        icons={400:'play',404:'stop',401:'page-back' if shuffle else 'play-next',
               402:'page-next' if shuffle else 'add',403:'current' if shuffle else 'replace',405:'back',406:'forward'}
        order=(405,400,406,404,401,402,403) if self.allowed else (401,402,403)
        width,gap=(64,12) if self.allowed else (76,30)
        span=len(order)*width+(len(order)-1)*gap
        start=170+(530-span)//2
        for index,identity in enumerate(order):
            left=start+index*(width+gap)
            self.getControl(identity).setPosition(left,930);self.getControl(identity).setWidth(width)
            for offset,size,top in ((8000,44,940),(9000,48,938),(10000,20,991)):
                self.getControl(offset+identity).setPosition(left+(width-size)//2,top)
            self.setProperty('Album.Icon'+str(identity),str(ROOT/'resources'/'controls'/(icons[identity]+'.png')))
            self.getControl(identity).setLabel(self.control_labels[identity])
        self.setProperty('Album.ControlHint','Select a track · playback test' if self.allowed else 'Queue preview only · no playback starts')

    def onFocus(self,control):
        if control==611 and self.scrub:self.render_scrub();return
        if control in self.control_labels:
            text=self.control_labels[control]+(' · preview' if not self.allowed else '')
            if getattr(self,'control_worker',None):text='Updating playback…'
            self.setProperty('Album.ControlHint',text)

    def focus_control(self,control):
        self.setFocusId(control)
        self.onFocus(control)

    def dialog(self,method,*args):
        # Native Back may also reach the underlying WindowXML callback while
        # a Python modal is unwinding. Cancel must not become a second exit.
        self.dialog_open=True
        result=None;origin=self.getFocusId()
        try:
            result=getattr(xbmcgui.Dialog(),method)(*args)
            if method=='yesno':xbmc.log('AsterMusicTrial confirmation='+str(bool(result)),xbmc.LOGINFO)
            return result
        finally:
            self.dialog_open=False
            cancelled=result is False or (method=='select' and type(result) is int and result<0)
            self.back_guard_until=time.monotonic()+.3 if cancelled else 0
            if not self.finished and origin:self.focus_control(origin)

    def onInit(self):
        kind=getattr(self.selection,'kind','album')
        self.setProperty('Album.Context',kind.upper()+(' / PLAYER' if self.allowed else ' / QUEUE PREVIEW'))
        self.setProperty('Album.TrackHeading','Tracks')
        self.setProperty('Album.Title',self.title)
        self.setProperty('Album.Id',str(self.selection.album_id))
        self.setProperty('Album.Art',self.artwork)
        self.setProperty('Album.AudioDetails','')
        self.setProperty('Album.Busy','false')
        self.setProperty('Album.ScrubMode','false');self.setProperty('Album.Playing','false')
        ordering='disc / track' if self.selection.disc_numbers_available else 'track tags · disc numbers unavailable'
        self.setProperty('Album.Count','1 song' if kind=='song' else str(len(self.selection.tracks))+' tracks · '+('saved playlist order' if kind=='playlist' else 'ordered by '+ordering))
        self.setProperty('Album.Status','Read-only queue preview · no playback starts')
        self.setProperty('Album.Live','true' if self.allowed else 'false')
        self.setProperty('Album.Help','Preview only · select a track for its queue options. Back returns to the same tile. No playback or queue changes.')
        if self.allowed:
            self.setProperty('Album.Status',f'HP Music pilot · {len(self.allowed)} tracks · Back stops and restores the original empty queue' if normal_playback() else f'HP live trial · {len(self.allowed)} approved tracks · Back stops and restores the original empty queue')
            self.setProperty('Album.Help','OK plays a track. Menu on a track: Play Next, add or remove its queued occurrence. Menu on controls: shuffle, save or clear. Back stops playback.' if normal_playback()
                else 'OK opens track actions. Menu: shuffle/order, audio details and save a private Jellyfin playlist. Back stops playback.')
        self.configure_controls()
        items=[]
        for row in self.selection.tracks:
            number=f'{row.disc}.{row.track:02}' if row.disc else str(row.track)
            item=xbmcgui.ListItem(label=number+'  '+row.title)
            item.setProperty('SongId',str(row.song_id))
            item.setProperty('Duration',f'{row.duration//60}:{row.duration%60:02}' if row.duration else '—')
            items.append(item)
        self.getControl(600).reset();self.getControl(600).addItems(items)
        self.setFocusId(600)
        xbmcgui.Window(10000).setProperty('AsterV2Lab.AlbumWindow',str(xbmcgui.getCurrentWindowId()))

    def preview(self,action,ids):
        try:
            snapshot=read_queue(rpc)
            if action=='next' and snapshot.current_index is None:
                self.dialog('ok','Play Next · preview','There is no current music track. Add to Queue can preview an idle queue. Nothing has changed.');return
            plan=propose(snapshot,ids,action=action)
        except (QueueUnavailable,ValueError) as error:
            message={'unsupported-queue-item':'The queue contains a file or stream this preview cannot safely represent.',
                     'unsupported-active-player':'The current player is not a supported music queue.',
                     'queue-changed-during-read':'The queue changed while reading it. Please try again.'}.get(str(error),'Queue preview unavailable. Please retry without changing playback.')
            self.dialog('ok','Queue preview unavailable',message+'\n\nYour queue is unchanged.');return
        names={'next':'Play Next','append':'Add to Queue','replace':'Replace Queue'}
        effect=('Would replace the existing queue. Live replacement will require confirmation.'
                if plan.replaces_queue else 'Would preserve the current track and existing queue order.')
        self.dialog('ok',names[action]+' · preview',f'{len(ids)} selected tracks · {len(snapshot.song_ids)} currently queued · {len(plan.song_ids)} proposed total.\n\n'+effect+'\n\nPreview only. Nothing was played, saved or changed.')

    def onClick(self,control):
        if self.finished:return
        if self.control_worker:return
        if self.allowed:
            if control==611:
                if self.scrub:
                    preview=self.scrub;self.cancel_scrub();self.seek_album(preview)
                else:self.begin_scrub()
            elif control in (405,406):
                self.begin_scrub()
                if self.scrub:
                    preview=self.scrub.adjust(-1 if control==405 else 1).adjust(-1 if control==405 else 1)
                    self.cancel_scrub();self.seek_album(preview)
            elif control==400:
                self.live('toggle',self.allowed)
            elif control==404:self.live('stop',())
            elif control in (401,402,403):self.live({401:'next',402:'append',403:'replace'}[control],self.allowed)
            elif control==600:
                index=self.getControl(600).getSelectedPosition()
                if not 0<=index<len(self.display_ids if self.display_ids is not None else self.selection.tracks):return
                identity=self.display_ids[index] if self.display_ids is not None else self.selection.tracks[index].song_id
                if identity not in self.allowed:
                    self.dialog('ok','Bounded HP trial','This track is outside the approved test selection. No changes made.');return
                if normal_playback():self.play_selected(index,identity);return
                option=self.dialog('select','This track',['Play this track','Play Next','Add to Queue','Replace Queue'])
                if option in (0,1,2,3):self.live(('play','next','append','replace')[option],(identity,))
            return
        if control in (401,402,403):
            self.preview({401:'next',402:'append',403:'replace'}[control],self.selection.song_ids)
        elif control==600:
            index=self.getControl(600).getSelectedPosition()
            if not 0<=index<len(self.selection.tracks):return
            option=self.dialog('select','This track · preview',['Play Next','Add to Queue','Replace Queue'])
            if option in (0,1,2):self.preview(('next','append','replace')[option],(self.selection.tracks[index].song_id,))

    def play_selected(self,index,identity):
        if self.trial:
            state=self.trial.observe()
            displayed=self.display_ids if self.display_ids is not None else self.selection.song_ids
            if state.current_index is not None and displayed==state.song_ids:
                def work():
                    try:self.trial.select(index,expected_queue=state.fingerprint)
                    except Exception as error:self.control_errors.append(error)
                self.control_worker=threading.Thread(target=work,name='AsterAlbumSelect')
                self.setProperty('Album.Busy','true')
                self.control_worker.start();return
        self.live('play',(identity,))

    def track_menu(self):
        if self.control_worker:return
        displayed=self.display_ids if self.display_ids is not None else self.selection.song_ids
        index=self.getControl(600).getSelectedPosition()
        if not 0<=index<len(displayed):return
        identity=displayed[index]
        if identity not in self.allowed:raise TrialUnavailable('song-outside-trial')
        snapshot=self.trial.observe() if self.trial else None
        owned=snapshot is not None and displayed==snapshot.song_ids
        options=['Play this track','Play Next','Add to Queue']
        if owned:options.append('Remove this queued occurrence…')
        option=self.dialog('select','This track',options)
        if option==0:self.play_selected(index,identity)
        elif option in (1,2):self.live('next' if option==1 else 'append',(identity,))
        elif option==3 and owned:
            if index==snapshot.current_index:
                self.dialog('ok','Keep playing song','The playing occurrence cannot be removed. Select another queued song.');return
            if self.dialog('yesno','Remove queued song','Remove this occurrence only? Your library and saved playlists are unchanged.'):
                self.edit_album_queue('remove',(index,snapshot.fingerprint))

    def edit_album_queue(self,action,value):
        if self.control_worker or not self.trial:return
        if action not in ('remove','clear'):raise TrialUnavailable('unsupported-queue-edit')
        self.queue_view=True
        def work():
            try:
                if action=='remove':self.trial.remove(value[0],expected_queue=value[1])
                else:
                    with self.trial.lock:
                        if self.trial.observe().fingerprint!=value:raise TrialUnavailable('queue-preview-stale')
                        self.trial.stop()
                        idle=self.trial.observe()
                        self.trial.clear(expected_queue=idle.fingerprint,confirmed=True)
            except Exception as error:self.control_errors.append(error)
        self.setProperty('Album.ControlHint','Updating playback…')
        self.control_worker=threading.Thread(target=work,name='AsterAlbumQueueEdit')
        self.setProperty('Album.Busy','true')
        self.control_worker.start()

    def live(self,action,ids):
        try:
            if action=='toggle':
                if self.trial and self.trial.observe().current_index is not None:
                    speed=rpc('Player.GetProperties',{'playerid':0,'properties':['speed']}).get('speed')
                    action='resume' if speed==0 else 'pause'
                else:action='play'
            if action not in ('stop',) and not playback_allowed(self.allowed,self.queue_limit):
                raise TrialUnavailable('trial-capability-expired')
            confirmed=False
            if action in ('play','replace'):
                confirmed=self.dialog('yesno','Play music' if action=='play' else 'Replace Queue',
                    f'This will replace the trial queue with {len(ids)} approved track(s).'+
                    (' Playback will start.' if action=='play' else ' Playback will not start.'))
                if not confirmed:return
            if self.trial is None:
                if action in ('stop','pause','resume'):return
                def transport(method,params):
                    if method in READS:return rpc(method,params)
                    if method not in ('Player.Stop','Playlist.Clear') and not (method=='Player.SetShuffle' and params.get('shuffle') is False):
                        if not playback_allowed(self.allowed,self.queue_limit):
                            raise TrialUnavailable('trial-capability-expired')
                    validate_write(method,params,self.allowed,queue_limit=self.queue_limit)
                    xbmc.log('AsterMusicTrial write='+method,xbmc.LOGINFO)
                    return execute(method,params)
                stamp=time.time_ns()
                self.trial=ExpandedTrial(transport,tuple(dict.fromkeys(self.allowed)),lambda snapshot:save_empty_checkpoint(
                    trial_directory()/f'queue-checkpoint-{stamp}.json',snapshot),queue_limit=self.queue_limit,
                    intent=lambda snapshot,**kw:save_intent(trial_directory()/f'queue-intent-{stamp}.json',snapshot,**kw))
            if action=='play':self.start_cancellable(ids,confirmed)
            elif action in ('pause','resume'):self.trial.pause(action=='resume')
            elif action=='stop':self.trial.stop()
            else:self.trial.edit(action,ids,confirmed=confirmed)
            active=self.trial.observe().current_index is not None
            paused=active and rpc('Player.GetProperties',{'playerid':0,'properties':['speed']}).get('speed')==0
            self.control_labels[400]='Resume' if paused else 'Pause' if active else 'Play'
            self.getControl(400).setLabel(self.control_labels[400])
            self.setProperty('Album.Icon400',str(ROOT/'resources'/'controls'/('pause.png' if active and not paused else 'play.png')))
            self.onFocus(self.getFocusId())
            self.setProperty('Album.Status','HP Music · '+action+' completed · Back stops and restores the original queue')
            self.setProperty('Album.AudioDetails',read_source(rpc) if active else '')
            self.next_player_update=0
        except TrialCancelled:
            self.setProperty('Album.Status','Start cancelled · playback stopped and original empty queue restored')
        except (TrialUnavailable,QueueUnavailable,ValueError,OSError) as error:
            message={'replacement-confirmation-required':'Replacement was not confirmed.',
                     'stop-before-replace':'Stop this trial before replacing its queue.',
                     'three-item-trial-limit':'This first trial is limited to three queued items. Choose one track or stop and replace.',
                     'trial-capability-expired':'The live trial approval has expired. Back will stop and restore the queue.',
                     'idle-empty-queue-required':'The HP must be idle with an empty music queue before this trial.',
                     'external-queue-change':'The queue changed outside this trial. No further queue changes will be made.'}.get(str(error),'The live trial could not complete safely. Stop testing and retain the checkpoint.')
            if str(error)=='turn-shuffle-off-before-editing':message='Turn shuffle off in Menu before adding or removing tracks. Playback is unchanged.'
            self.setProperty('Album.Status','Trial action refused · '+str(error))
            self.dialog('ok','Aster Music trial',message)

    def start_cancellable(self,ids,confirmed):
        """Only the main thread touches GUI; never abandon an in-flight writer."""
        progress=xbmcgui.DialogProgress();progress.create('Starting Aster Music','Preparing the verified album queue. Back cancels this start.')
        errors=[];counts=[0,len(ids)];self.dialog_open=True
        self.trial.cancel.clear()
        self.trial.progress=lambda done,total:counts.__setitem__(slice(None),[done,total])
        def work():
            try:
                # Explicit confirmed replacement may stop only this verified
                # owned player, then wait out its existing delayed clear.
                if self.trial.observe().current_index is not None:self.trial.stop()
                self.trial.play(ids,confirmed=confirmed)
            except Exception as error:errors.append(error)
        worker=threading.Thread(target=work,name='AsterMusicStart')
        try:
            worker.start()
            while worker.is_alive():
                if progress.iscanceled() or xbmc.Monitor().abortRequested():self.trial.cancel.set()
                progress.update(min(99,int(counts[0]*100/max(1,counts[1]))),
                    'Cancelling safely…' if self.trial.cancel.is_set() else 'Preparing queue · '+str(counts[0])+' / '+str(counts[1]))
                xbmc.sleep(50)
            worker.join()
            if errors:raise errors[0]
        finally:
            progress.close();self.dialog_open=False;self.back_guard_until=time.monotonic()+.3

    def begin_scrub(self):
        if self.control_worker or not self.trial:return
        try:
            with self.trial.lock:
                state=self.trial.observe()
                props=rpc('Player.GetProperties',{'playerid':0,'properties':['time','totaltime','canseek']})
                if state.current_index is None or props.get('canseek') is not True:raise TrialUnavailable('seek-unavailable')
                self.scrub=ScrubPreview.start(state,clock_milliseconds(props.get('totaltime')),clock_milliseconds(props.get('time')))
            self.setProperty('Album.ScrubMode','true');self.focus_control(611)
        except (TrialUnavailable,QueueUnavailable,ValueError):
            self.cancel_scrub()
            self.dialog('ok','Seek unavailable','This song does not report a stable seekable duration. Playback is unchanged.')

    def render_scrub(self):
        if not self.scrub:return
        self.getControl(610).setPercent(self.scrub.percentage)
        self.getControl(620).setPosition(170+int(self.scrub.percentage/100*360),906)
        self.setProperty('Album.Clock',clock_label(self.scrub.target_ms)+' / '+clock_label(self.scrub.duration_ms))
        self.setProperty('Album.ControlHint','Seek '+clock_label(self.scrub.target_ms)+' · Left/right · OK apply · Back cancel')

    def cancel_scrub(self,focus=True):
        self.scrub=None;self.setProperty('Album.ScrubMode','false');self.next_player_update=0
        if focus:self.focus_control(400)

    def seek_album(self,preview):
        if self.control_worker or not self.trial:return
        def work():
            try:seek_owned(self.trial,self.trial.last.song_ids,preview)
            except Exception as error:self.control_errors.append(error)
        self.control_worker=threading.Thread(target=work,name='AsterAlbumSeek')
        self.setProperty('Album.Busy','true')
        self.control_worker.start()

    def shuffle_album(self):
        if self.control_worker or not self.trial:return
        state=self.trial.observe();enabled=not self.trial.shuffled
        if state.current_index is None or len(state.song_ids)<2:
            self.dialog('ok','More songs needed','Start an album or playlist with at least two queued songs before shuffling.');return
        if not self.dialog('yesno','Shuffle queue' if enabled else 'Restore queue order',
                'Change the order of this owned queue without restarting the playing song? Turn shuffle off before adding or removing tracks.'):return
        self.queue_view=True
        def work():
            try:self.trial.set_shuffle(enabled,expected_queue=state.fingerprint,confirmed=True)
            except Exception as error:self.control_errors.append(error)
        self.control_worker=threading.Thread(target=work,name='AsterAlbumShuffle')
        self.setProperty('Album.Busy','true')
        self.control_worker.start()

    def render_owned_queue(self,state):
        key=(state.song_ids,self.trial.shuffled)
        if not self.queue_view:return
        if key==self.rendered_queue:
            self.setProperty('Album.QueueFingerprint',QueueSnapshot(self.display_ids,state.current_index).fingerprint);return
        self.rendered_queue=key;self.display_ids=state.song_ids
        self.marked_index=None
        details={row.song_id:row for row in self.selection.tracks}
        rows=[]
        for index,identity in enumerate(state.song_ids):
            track=details[identity]
            item=xbmcgui.ListItem(label=str(index+1)+'  '+track.title)
            item.setProperty('SongId',str(identity))
            item.setProperty('Duration',f'{track.duration//60}:{track.duration%60:02}' if track.duration else '—')
            rows.append(item)
        self.getControl(600).reset();self.getControl(600).addItems(rows)
        # Publish the GUI model from its owning WindowXML interpreter. Native
        # test clients must not wrap our controls in another Python invoker.
        rendered=tuple(int(self.getControl(600).getListItem(i).getProperty('SongId')) for i in range(len(rows)))
        self.setProperty('Album.QueueFingerprint',QueueSnapshot(rendered,state.current_index).fingerprint)
        if state.current_index is not None:self.getControl(600).selectItem(state.current_index)
        self.setProperty('Album.TrackHeading','Queue · '+('shuffle on' if self.trial.shuffled else 'original order'))
        self.setProperty('Album.Status','Queue empty · library and saved playlists unchanged' if not state.song_ids
            else 'HP Music · '+('Shuffle on' if self.trial.shuffled else 'Original order restored')+' · playing song preserved')

    def mark_playing(self,state):
        displayed=self.display_ids if self.display_ids is not None else self.selection.song_ids
        target=None
        if state.current_index is not None:
            if displayed==state.song_ids:target=state.current_index
            else:
                matches=[i for i,identity in enumerate(displayed) if identity==state.song_ids[state.current_index]]
                if len(matches)==1:target=matches[0]  # Never guess a duplicate source occurrence.
        if self.marked_index==target:return
        if self.marked_index is not None and 0<=self.marked_index<len(displayed):
            self.getControl(600).getListItem(self.marked_index).setProperty('NowPlaying','false')
        if target is not None:self.getControl(600).getListItem(target).setProperty('NowPlaying','true')
        self.marked_index=target

    def refresh(self):
        if self.control_worker:
            if self.control_worker.is_alive():return
            self.control_worker.join();self.control_worker=None;self.next_player_update=0
            self.setProperty('Album.Busy','false')
            if self.getFocusId()==600:
                self.setProperty('Album.ControlHint','OK plays this track · Menu opens track actions')
            if self.control_errors:
                self.control_errors.clear()
                if self.trial and self.trial.shuffle_uncertain:raise TrialUnavailable('shuffle-recovery-required')
                self.dialog('ok','Action not verified','The song or queue may have changed. The action will not be retried. Check playback before continuing.')
        if not self.trial or time.monotonic()<self.next_player_update:return
        self.next_player_update=time.monotonic()+1
        state=self.trial.observe();active=state.current_index is not None
        self.render_owned_queue(state)
        self.mark_playing(state)
        self.setProperty('Album.Playing','true' if active else 'false')
        if not active:
            if self.scrub:self.cancel_scrub()
            self.control_labels[400]='Play';self.getControl(400).setLabel('Play')
            self.setProperty('Album.Icon400',str(ROOT/'resources'/'controls'/'play.png'))
            self.setProperty('Album.AudioDetails','');self.onFocus(self.getFocusId());return
        props=rpc('Player.GetProperties',{'playerid':0,'properties':['time','totaltime','speed']})
        if self.scrub and (self.scrub.queue_fingerprint!=state.fingerprint):self.cancel_scrub()
        if not self.scrub:
            try:
                elapsed=clock_milliseconds(props.get('time'));duration=clock_milliseconds(props.get('totaltime'))
                if not 0<=elapsed<=duration or not duration:raise TrialUnavailable('playback-clock-unavailable')
                self.getControl(610).setPercent(elapsed/duration*100)
                self.setProperty('Album.Clock',clock_label(elapsed)+' / '+clock_label(duration))
            except TrialUnavailable:self.getControl(610).setPercent(0);self.setProperty('Album.Clock','— / —')
        paused=props.get('speed')==0
        self.control_labels[400]='Resume' if paused else 'Pause'
        self.getControl(400).setLabel(self.control_labels[400])
        self.setProperty('Album.Icon400',str(ROOT/'resources'/'controls'/('play.png' if paused else 'pause.png')))
        self.setProperty('Album.AudioDetails',read_source(rpc))
        self.onFocus(self.getFocusId())

    def close(self):
        xbmc.log('AsterMusicTrial close='+','.join(frame.name for frame in traceback.extract_stack(limit=3))+' finished='+str(self.finished),xbmc.LOGINFO)
        if self.finished:return
        self.finished=True
        try:
            if self.trial:
                self.trial.cancel.set()
                if self.control_worker:self.control_worker.join()
                self.trial.close()
        except (TrialUnavailable,QueueUnavailable,ValueError):
            xbmcgui.Window(10000).setProperty('AsterV2Lab.TrialRecovery','required')
            xbmcgui.Dialog().notification('Music trial recovery required','Unexpected playback/queue state. Checkpoint retained; do not continue testing.')
        finally:super().close()

    def save_shared_queue(self,engine,snapshot):
        self.dialog_open=True
        try:
            keyboard=xbmc.Keyboard('','Name saved Jellyfin playlist')
            keyboard.doModal()
            if not keyboard.isConfirmed():return
            name=keyboard.getText().strip()
        finally:self.dialog_open=False;self.back_guard_until=time.monotonic()+.3
        if not name or len(name)>100 or any(ord(c)<32 or ord(c)==127 for c in name):
            self.dialog('ok','Playlist name','Use a name of 1–100 characters without control characters.');return
        if not self.dialog('yesno','Save queue to Jellyfin',f'Create a new private playlist “{name}” with {len(snapshot.song_ids)} tracks under the signed-in account? Existing playlists will not be changed.'):return
        progress=xbmcgui.DialogProgress();progress.create('Saving playlist','Preparing the private shared playlist. Back cancels before the request is sent.')
        cancelled=threading.Event();result=[];errors=[];self.dialog_open=True
        def work():
            try:
                import xbmcvfs
                creator=PlaylistCreator(xbmcvfs.translatePath('special://profile/addon_data/plugin.video.jellyfin/data.json'))
                result.append(save_owned_queue(engine,snapshot.fingerprint,name,creator,
                    lambda ids:server_mapping(xbmcvfs.translatePath('special://profile/Database/jellyfin.db'),ids),
                    trial_directory(),confirmed=True,cancelled=cancelled.is_set))
            except Exception as error:errors.append(error)
        worker=threading.Thread(target=work,name='AsterSharedPlaylistSave')
        try:
            worker.start()
            while worker.is_alive():
                if progress.iscanceled() or xbmc.Monitor().abortRequested():cancelled.set()
                progress.update(50,'Finishing safely; a sent request must be resolved.' if cancelled.is_set() else 'Verifying exact song order and private access…')
                xbmc.sleep(50)
            worker.join()
        finally:
            progress.close();self.dialog_open=False;self.back_guard_until=time.monotonic()+.3
        if errors:
            error=errors[0];code=str(error) if isinstance(error,(PlaylistSaveUnavailable,PlaylistUnavailable)) else 'shared-save-unavailable'
            message={'playlist-save-cancelled':'Save cancelled before sending. Your queue and server playlists are unchanged.',
                'playlist-name-already-exists':'That playlist name already exists. Choose a different name; nothing was overwritten.',
                'queue-preview-stale':'The queue or playing song changed. Open Menu again to review a fresh queue.',
                'playlist-saving-identity-changed':'The signed-in identity changed. Shared saving needs review before it can continue.',
                'shared-save-recovery-required':'An earlier save has an uncertain result. Do not repeat it; retain the recovery journal for review.'}.get(code,
                'The save could not be verified. A request may have reached Jellyfin: do not repeat it. The private recovery journal is retained; playback is unchanged.')
            self.dialog('ok','Playlist not saved' if code in ('playlist-save-cancelled','playlist-name-already-exists','queue-preview-stale') else 'Check playlist save',message)
        elif result:
            self.setProperty('Album.Status',f'Saved private Jellyfin playlist · {result[0]["count"]} tracks · playback unchanged')
            xbmcgui.Dialog().notification('Playlist saved',result[0]['name'])

    def audio_details(self):
        focused=self.getFocusId()
        self.dialog('ok','Audio details',read_details(rpc))
        # Native modal closure may leave WindowXML without a focused control.
        # Restore the exact originating control, not an arbitrary track.
        self.focus_control(focused)

    def onAction(self,action):
        if self.finished:return
        key=action.getId()
        if key in BACK:
            if self.scrub:self.cancel_scrub();return
            if not self.dialog_open and time.monotonic()>=self.back_guard_until:self.close()
            return
        if key==117:
            if self.dialog_open or self.control_worker:return
            if self.getFocusId()==600 and normal_playback():
                try:self.track_menu()
                except (TrialUnavailable,QueueUnavailable):
                    self.dialog('ok','Queue changed','The selected track could not be verified. No action was retried.')
                return
            if not self.trial:
                self.dialog('ok','Queue not started','Start music in this player before saving its owned queue.');return
            try:
                snapshot=self.trial.observe()
                if not snapshot.song_ids:
                    self.dialog('ok','Empty queue','There is no queued music to save.');return
                option=self.dialog('select','Queue actions',['Save queue to Jellyfin…','Audio details',
                    'Restore original order' if self.trial.shuffled else 'Shuffle queue','Stop and clear queue…'])
                if option==0:self.save_shared_queue(self.trial,snapshot)
                elif option==1:self.audio_details()
                elif option==2:self.shuffle_album()
                elif option==3 and self.dialog('yesno','Stop and clear queue','Stop this player and clear its queue? Your library and saved playlists are unchanged.'):
                    self.edit_album_queue('clear',snapshot.fingerprint)
            except (TrialUnavailable,QueueUnavailable):
                self.dialog('ok','Queue changed','The queue could not be verified. No playlist was saved.')
            return
        control=self.getFocusId()
        buttons=(405,400,406,404,401,402,403) if self.allowed else (401,402,403)
        if control==611:
            if key in (1,2) and self.scrub:self.scrub=self.scrub.adjust(-1 if key==1 else 1);self.render_scrub()
            elif key in (3,4):self.cancel_scrub(focus=False);self.focus_control(600 if key==3 else 400)
            return
        if control==600 and key==1:self.focus_control(400 if self.allowed else buttons[0]);return
        if control in buttons and key in DIRECTIONS:
            index=buttons.index(control)
            if key==1:self.focus_control(buttons[max(0,index-1)])
            elif key==2:self.focus_control(buttons[min(len(buttons)-1,index+1)])
            elif key==3 and control==400:self.begin_scrub()
            elif key in (3,4):self.focus_control(600)


class ShuffleLab(AlbumLab):
    """Same stripped-back player, with a single owned background filler."""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.session=None;self.paused=False;self.loaded=-1
        self.last_phase=None
        self.next_player_update=0;self.current_song=None;self.catalogue=None
        self.page_offset=0;self.current_position=0
        self.initialized=False
        self.control_worker=None;self.control_errors=[]
        self.next_audio_update=0
        self.scrub=None;self.control_labels[611]='Seek position'

    def onInit(self):
        super().onInit()
        self.setProperty('Album.Shuffle','true')
        self.setProperty('Album.ScrubMode','false')
        self.setProperty('Album.Context','SHUFFLE ALL / NO HOLIDAY MUSIC')
        self.setProperty('Album.Count',f'{len(self.allowed):,} verified songs')
        self.setProperty('Album.Help','Select to play · Menu edits a fully loaded queue. Page arrows browse; Current finds the playing song. Back stops playback.')
        self.control_labels.update({401:'Previous queue page',402:'Next queue page',403:'Show playing song'})
        self.configure_controls(shuffle=True)
        for identity in (401,402,403):self.getControl(identity).setVisible(True)
        self.render_page()
        self.focus_control(400)
        self.initialized=True

    def render_page(self):
        ids=self.allowed[self.page_offset:self.page_offset+200]
        self.setProperty('Album.TrackHeading',f'Queue · {self.page_offset+1:,}–{self.page_offset+len(ids):,} / {len(self.allowed):,}'+
            (' · shuffle on' if self.session and self.session.engine.shuffled else ''))
        rows=[]
        for n,identity in enumerate(ids):
            item=xbmcgui.ListItem(label=f'{self.page_offset+n+1:,}  '+self.catalogue.songs[identity].get('label','Untitled'))
            item.setProperty('NowPlaying','true' if self.current_song is not None and self.page_offset+n==self.current_position else 'false');rows.append(item)
        self.getControl(600).reset();self.getControl(600).addItems(rows)

    def refresh(self):
        if self.control_worker and not self.control_worker.is_alive():
            self.control_worker.join();self.control_worker=None;self.next_player_update=0
            if self.control_errors:
                error=self.control_errors.pop(0)
                if isinstance(error,TrialUnavailable) and str(error)=='selected-track-not-loaded':
                    self.dialog('ok','Still loading','This song has not reached the native queue yet. Choose a loaded song or wait.')
                elif isinstance(error,TrialUnavailable) and str(error) in ('seek-unavailable','playback-clock-unavailable','track-changed-before-seek','scrub-preview-stale'):
                    self.dialog('ok','Seek unavailable','This song does not currently report a stable seekable duration. Playback is unchanged.')
                elif isinstance(error,TrialUnavailable) and str(error) in ('queue-preview-stale','queue-remove-refused','queue-still-loading'):
                    self.dialog('ok','Queue unchanged',{'queue-preview-stale':'The queue or playing song changed. Open Menu again to review a fresh selection.',
                        'queue-remove-refused':'The playing occurrence cannot be removed. Choose a different queued song.',
                        'queue-still-loading':'Queue editing becomes available after loading finishes.'}[str(error)])
                elif isinstance(error,TrialUnavailable) and str(error)=='turn-shuffle-off-before-editing':
                    self.dialog('ok','Queue unchanged','Turn shuffle off in Menu before adding or removing tracks. Playback is unchanged.')
                else:raise TrialUnavailable('player-control-failed')
            if self.session.selected!=self.allowed:
                self.allowed=self.session.selected
                self.page_offset=min(self.page_offset,max(0,(len(self.allowed)-1)//200*200))
                self.current_song=None;self.render_page()
            elif getattr(self,'last_control_action',None)=='shuffle':self.render_page()
        state=self.session.status()
        if state['phase']=='cleared':self.close();return
        if state['phase']=='failed':raise TrialUnavailable(state['error'] or 'progressive-fill-failed')
        if state['loaded']!=self.loaded or state['phase']!=self.last_phase:
            self.loaded=state['loaded'];self.last_phase=state['phase']
            self.setProperty('Album.Status',f"{state['loaded']:,} / {state['total']:,} queued · "+
                ('Ready' if state['phase']=='ready' else 'Loading in background · Back cancels safely'))
        if self.control_worker:return  # Never interpret half-finished native player transitions as new UI state.
        if time.monotonic()>=self.next_player_update:
            self.next_player_update=time.monotonic()+1
            props=rpc('Player.GetProperties',{'playerid':0,'properties':['position','speed','time','totaltime','canseek']})
            position=props.get('position')
            if type(position) is int and 0<=position<len(self.allowed):
                identity=self.allowed[position]
                item=rpc('Player.GetItem',{'playerid':0,'properties':[]}).get('item',{})
                if item.get('type')=='song' and item.get('id')==identity:
                    if time.monotonic()>=self.next_audio_update:
                        self.setProperty('Album.AudioDetails',read_source(rpc));self.next_audio_update=time.monotonic()+3
                    try:
                        elapsed=clock_milliseconds(props.get('time'));duration=clock_milliseconds(props.get('totaltime'))
                        if not 0<=elapsed<=duration or not duration:raise TrialUnavailable('playback-clock-unavailable')
                        if self.scrub and (self.scrub.index!=position or self.scrub.song_id!=identity):self.cancel_scrub()
                        if not self.scrub:
                            self.setProperty('Album.Clock',clock_label(elapsed)+' / '+clock_label(duration))
                            self.getControl(610).setPercent(elapsed/duration*100)
                    except TrialUnavailable:
                        self.setProperty('Album.Clock','— / —');self.getControl(610).setPercent(0)
                    old_position=self.current_position
                    self.current_position=position
                    if identity!=self.current_song or position!=old_position:
                        visible=self.allowed[self.page_offset:self.page_offset+200]
                        if self.current_song is not None and self.page_offset<=old_position<self.page_offset+len(visible):
                            self.getControl(600).getListItem(old_position-self.page_offset).setProperty('NowPlaying','false')
                        self.current_song=identity
                        if self.page_offset<=position<self.page_offset+len(visible):self.getControl(600).getListItem(position-self.page_offset).setProperty('NowPlaying','true')
                        song=self.catalogue.songs[identity]
                        names=[self.catalogue.artists[i].get('label','') for i in song.get('artistid',[])
                               if i in self.catalogue.artists and not (i==1 and self.catalogue.artists[i].get('label')=='[Missing Tag]')]
                        self.setProperty('Album.Title',song.get('label','Untitled'))
                        self.setProperty('Album.Count',(' / '.join(names) or 'Artist unavailable')+f' · {position+1:,} / {len(self.allowed):,}')
                        try:
                            art=rpc('AudioLibrary.GetSongDetails',{'songid':identity,'properties':['thumbnail']}).get('songdetails',{}).get('thumbnail')
                            self.setProperty('Album.Art',art if isinstance(art,str) and art else ASSETS+ICONS['album'])
                        except CatalogueUnavailable:pass
                    if props.get('speed') in (0,1):
                        self.paused=props['speed']==0
                        if not self.control_worker:
                            self.control_labels[400]='Resume' if self.paused else 'Pause'
                            self.getControl(400).setLabel(self.control_labels[400])
                            self.setProperty('Album.Icon400',str(ROOT/'resources'/'controls'/('play.png' if self.paused else 'pause.png')))
                            self.onFocus(self.getFocusId())

    def control(self,action,value):
        if self.control_worker:return
        self.last_control_action=action
        def work():
            try:
                if action=='pause':self.session.pause(value)
                elif action=='seek':self.session.seek(value)
                elif action=='scrub':self.session.seek_to(value)
                elif action=='remove':self.session.remove(value[0],expected_queue=value[1])
                elif action=='clear':self.session.clear(expected_queue=value,confirmed=True)
                elif action=='shuffle':self.session.set_shuffle(value[0],expected_queue=value[1],confirmed=True)
                else:self.session.select(value)
            except Exception as error:self.control_errors.append(error)
        self.getControl(400).setLabel('Updating…')
        self.setProperty('Album.ControlHint','Updating playback…')
        self.control_worker=threading.Thread(target=work,name='AsterMusicControl')
        self.control_worker.start()

    def begin_scrub(self):
        if self.control_worker:return
        self.session.control_pending.set()
        try:
            with self.session.engine.lock:
                state=self.session.engine.observe()
                props=rpc('Player.GetProperties',{'playerid':0,'properties':['time','totaltime','canseek']})
                if props.get('canseek') is not True or state.current_index is None:raise TrialUnavailable('seek-unavailable')
                self.scrub=ScrubPreview.start(QueueSnapshot(self.session.selected,state.current_index),
                    clock_milliseconds(props.get('totaltime')),clock_milliseconds(props.get('time')))
            self.setProperty('Album.ScrubMode','true');self.focus_control(611)
        except (TrialUnavailable,QueueUnavailable,ValueError):
            self.scrub=None;self.setProperty('Album.ScrubMode','false')
            self.dialog('ok','Seek unavailable','This song does not report a stable seekable duration. Playback is unchanged.')
        finally:self.session.control_pending.clear()

    def render_scrub(self):
        if not self.scrub:return
        self.getControl(610).setPercent(self.scrub.percentage)
        self.getControl(620).setPosition(170+int(self.scrub.percentage/100*360),906)
        self.setProperty('Album.Clock',clock_label(self.scrub.target_ms)+' / '+clock_label(self.scrub.duration_ms))
        self.setProperty('Album.ControlHint','Seek '+clock_label(self.scrub.target_ms)+' · Left/right · OK apply · Back cancel')

    def cancel_scrub(self,focus=True):
        self.scrub=None;self.setProperty('Album.ScrubMode','false');self.next_player_update=0
        if focus:self.focus_control(400)

    def onFocus(self,control):
        if control==611 and self.scrub:self.render_scrub()
        else:super().onFocus(control)

    def queue_menu(self):
        if self.control_worker:return
        state=self.session.status()
        if state['phase']!='ready' or state['writer_active']:
            self.dialog('ok','Queue loading','Let loading finish before editing the queue. You can still play loaded songs, pause or exit.');return
        snapshot=self.session.engine.observe()
        position=self.page_offset+self.getControl(600).getSelectedPosition()
        if not 0<=position<len(snapshot.song_ids):return
        option=self.dialog('select','Queue actions',['Remove selected song','Stop and clear queue…','Save queue to Jellyfin…','Audio details',
            'Restore starting queue order' if self.session.engine.shuffled else 'Shuffle queue'])
        if option==0:
            if position==snapshot.current_index:
                self.dialog('ok','Keep playing song','The playing occurrence cannot be removed. Select another queued song.');return
            if self.dialog('yesno','Remove queued song','Remove this occurrence from the queue? Your library and saved playlists are unchanged.'):
                self.control('remove',(position,snapshot.fingerprint))
        elif option==1 and self.dialog('yesno','Stop and clear queue','Stop this player and clear its queue? Your library and saved playlists are unchanged.'):
            self.control('clear',snapshot.fingerprint)
        elif option==2:self.save_shared_queue(self.session.engine,snapshot)
        elif option==3:self.audio_details()
        elif option==4 and self.dialog('yesno','Shuffle queue' if not self.session.engine.shuffled else 'Restore queue order',
                'Change queue order without restarting the playing song? Turn shuffle off before editing tracks.'):
            self.control('shuffle',(not self.session.engine.shuffled,snapshot.fingerprint))

    def onClick(self,control):
        if self.finished:return
        try:
            if control==611:
                if self.scrub:
                    preview=self.scrub;self.cancel_scrub();self.control('scrub',preview)
                else:self.begin_scrub()
            elif control==400:
                self.control('pause',self.paused)
            elif control==404:self.close()
            elif control in (405,406):self.control('seek',-10 if control==405 else 10)
            elif control in (401,402,403):
                target={401:max(0,self.page_offset-200),402:min((len(self.allowed)-1)//200*200,self.page_offset+200),403:self.current_position//200*200}[control]
                self.page_offset=target;self.render_page()
                if control==403:self.getControl(600).selectItem(self.current_position-self.page_offset)
            elif control==600:
                self.control('select',self.page_offset+self.getControl(600).getSelectedPosition())
        except TrialUnavailable as error:
            if str(error)=='selected-track-not-loaded':self.dialog('ok','Still loading','This song has not reached the native queue yet. Choose a loaded song or wait for loading to finish.')
            else:self.close()
        except Exception:self.close()

    def onAction(self,action):
        if self.finished:return
        key=action.getId()
        if key in BACK:
            if self.scrub:
                self.cancel_scrub();return
            if not self.dialog_open and time.monotonic()>=self.back_guard_until:self.close()
            return
        if key==117:
            if not self.dialog_open:self.queue_menu()
            return
        control=self.getFocusId()
        buttons=(405,400,406,404,401,402,403)
        if control==611:
            if key in (1,2):
                if self.scrub:self.scrub=self.scrub.adjust(-1 if key==1 else 1);self.render_scrub()
            elif key in (3,4):
                self.cancel_scrub(focus=False);self.focus_control(600 if key==3 else 400)
        elif control in buttons:
            if key in (1,2):self.focus_control(buttons[max(0,min(len(buttons)-1,buttons.index(control)+(1 if key==2 else -1)))])
            elif key==3:
                if control==400:self.begin_scrub()
                else:self.focus_control(600)
            elif key==4:self.focus_control(600)
        elif control==600 and key==1:self.focus_control(400)

    def close(self):
        if self.finished:return
        self.finished=True
        self.setProperty('Album.Status','Stopping playback · cancelling background loading safely…')
        try:
            if self.session:
                self.session.engine.cancel.set()
                if self.control_worker:self.control_worker.join()
                self.session.close()
        except Exception:
            xbmcgui.Window(10000).setProperty('AsterV2Lab.TrialRecovery','required')
            xbmcgui.Dialog().notification('Music recovery required','Unexpected queue state. Checkpoint retained; stop testing.')
        finally:xbmcgui.WindowXML.close(self)


class MusicLab(xbmcgui.WindowXML):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.model=None; self.rail=False; self.pending_focus=None; self.art_cache={};self.playlist_reader=None

    def onInit(self):
        self.setProperty('Lab.Rail','false')
        self.getControl(201).setLabel('Shuffle all · no holiday music' if normal_playback() else 'Shuffle all · eligibility preview')
        self.prop('Status','HP Music pilot · confirm Play / Shuffle · Back stops playback' if normal_playback() else 'Read-only pilot · no playback or library changes')
        self.render()
        self.focus_grid()
        xbmcgui.Window(10000).setProperty('AsterV2Lab.Window',str(xbmcgui.getCurrentWindowId()))

    def prop(self,key,value): self.setProperty('Lab.'+key,str(value))

    def focus(self,control):
        self.pending_focus=control
        self.setFocusId(control)

    def focus_grid(self):
        self.focus(500+self.model.index if self.model.page()['rows'] else 300)

    def art(self,row):
        if self.model.mode=='genres': return ASSETS+ICONS['album']
        if self.model.kind=='playlist':return ASSETS+ICONS['playlist']
        kind=self.model.kind; identity=row[kind+'id']; key=(kind,identity)
        if key not in self.art_cache:
            value=''
            try:
                method='AudioLibrary.Get'+kind.title()+'Details'
                data=rpc(method,{kind+'id':identity,'properties':['thumbnail']})
                value=data.get(kind+'details',{}).get('thumbnail','')
                if not isinstance(value,str): value=''
            except CatalogueUnavailable: pass
            if len(self.art_cache)>=128:self.art_cache.pop(next(iter(self.art_cache)))
            self.art_cache[key]=value or ASSETS+ICONS[kind]
        return self.art_cache[key]

    def render(self):
        page=self.model.page();rows=page['rows']
        self.prop('View','genres' if self.model.mode=='genres' else self.model.kind)
        artist=self.model.catalogue.artists.get(self.model.artist_id,{}).get('label')
        self.prop('Heading','Browse genres' if self.model.mode=='genres' else 'Jellyfin / Playlists' if self.model.mode=='playlists' else self.model.category+' / '+((artist+' / ') if artist else '')+self.model.kind.title()+'s')
        self.prop('Count',f"{page['total']:,} "+('categories' if self.model.mode=='genres' else self.model.kind+'s'))
        self.prop('Search',self.model.query or 'Search…')
        self.prop('Page',f"{self.model.offset+1 if rows else 0}–{self.model.offset+len(rows)} of {page['total']:,}")
        self.prop('Note',f"{page['uncredited_song_count']} tracks have unavailable artist credits; still available in Songs/Albums." if page['uncredited_song_count'] else 'Holiday music remains browseable. Only the dedicated shuffle excludes it.')
        self.prop('Empty','No matching '+('categories' if self.model.mode=='genres' else self.model.kind+'s')+'. Clear search or choose another view.' if not rows else '')
        for i in range(8):
            row=rows[i] if i<len(rows) else None
            self.prop(f'Item{i}.Title',row['label'] if row else '')
            self.prop(f'Item{i}.Detail',f"{row['song_count']:,} tracks" if row and self.model.mode=='genres' else self.model.kind.title() if row else '')
            self.prop(f'Item{i}.Art',self.art(row) if row else '')
            self.prop(f'Item{i}.RealArt','true' if row and not self.art(row).startswith(ASSETS) else 'false')
            self.getControl(500+i).setHeight(208 if self.model.mode=='genres' else 400)
        self.hero()

    def hero(self):
        rows=self.model.page()['rows'];row=rows[self.model.index] if rows else None
        self.prop('Title',row['label'] if row else 'Find your music')
        if self.model.mode=='genres' and row:
            copy=f"{row['song_count']:,} tracks · {row['album_count']:,} albums · {row['artist_count']:,} known artists"
        else:
            copy=(self.model.category or 'Your music')+' · Select an artist for their albums, or a song/album/playlist for the player. '+('Play needs confirmation; Back stops playback.' if normal_playback() else 'Playback requires the bounded HP test grant.')
        self.prop('Copy',copy)
        self.prop('HeroArt',self.art(row) if row else ASSETS+ICONS['album'])
        self.prop('Shuffle',f"{len(self.model.catalogue.shuffle_summary['eligible_ids']):,} eligible tracks · "+('confirm to shuffle' if normal_playback() else 'preview only'))

    def onFocus(self,control):
        if 500<=control<508 and control-500<len(self.model.page()['rows']):
            self.model.index=control-500
            if self.pending_focus!=control:self.model.column=self.model.index%4
            if self.pending_focus==control:self.pending_focus=None
            self.hero()

    def onClick(self,control):
        if 500<=control<508:
            selected=self.model.enter(control-500)
            if selected is not None:
                if self.model.kind=='album':self.open_album(selected)
                elif self.model.kind=='artist':
                    self.model.open_artist(selected['artistid']);self.render();self.focus_grid()
                elif self.model.kind=='song':self.open_song(selected)
                else:self.open_playlist(selected)
            else:self.render();self.focus_grid()
        elif control in (100,101,102):
            self.model.set_kind({100:'album',101:'artist',102:'song'}[control]);self.render();self.focus_grid()
        elif control==103:
            try:
                import xbmcvfs
                reader=PlaylistReader(xbmcvfs.translatePath('special://profile/addon_data/plugin.video.jellyfin/data.json'))
                rows=read_playlists(reader)
                self.playlist_reader=reader;self.model.open_playlists(rows);self.render();self.focus_grid()
            except PlaylistUnavailable:
                xbmcgui.Dialog().ok('Playlists unavailable','The signed-in Jellyfin playlists could not be read completely. Your current view and playlists are unchanged.')
        elif control==104:
            self.model.genres();self.render();self.focus_grid()
        elif control==200:self.focus_grid()
        elif control==201:
            s=self.model.catalogue.shuffle_summary
            granted,limit=live_grant()
            if normal_playback():limit=20000;granted=s['eligible_ids']
            if s['eligible_ids'] and len(s['eligible_ids'])<=limit and set(s['eligible_ids'])<=set(granted):
                self.open_shuffle(limit)
            else:xbmcgui.Dialog().ok('Shuffle all · eligibility preview',f"{len(s['eligible_ids']):,} eligible tracks; {s['excluded']:,} excluded by track or album holiday tags.\n\nNo playback starts and your queue is unchanged.")
        elif control==300:
            keyboard=xbmc.Keyboard(self.model.query,'Search '+('genres' if self.model.mode=='genres' else self.model.kind+'s'))
            keyboard.doModal()
            if keyboard.isConfirmed():self.model.search(keyboard.getText());self.render()
            self.focus(300)
        elif control==301:
            self.model.search('');self.render();self.focus_grid()
        elif control==302:
            if self.model.mode=='playlists':
                try:
                    self.model.open_playlists(read_playlists(self.playlist_reader));self.render();self.prop('Status','Jellyfin playlists refreshed')
                except PlaylistUnavailable:self.prop('Status','Playlist refresh unavailable · previous view retained')
                self.focus(302);return
            view,error=load_catalogue()
            if view is None:self.prop('Status',(error or 'Refresh failed')+' · previous view retained')
            else:
                self.model.catalogue=view;self.model.clamp();self.art_cache.clear();self.render();self.prop('Status','Complete catalogue refreshed')
            self.focus(302)
        elif control in (303,304):
            self.model.turn_page(-1 if control==303 else 1);self.render();self.focus_grid()
        elif control in (305,9008):self.close()
        elif control==9007:
            self.rail=False;self.prop('Rail','false');self.focus_grid()

    def open_shuffle(self,limit):
        view=self.model.catalogue
        ids=nonholiday_shuffle(list(view.songs.values()),list(view.albums.values()),expected_total=len(view.songs),seed=time.time_ns())
        if not xbmcgui.Dialog().yesno('Shuffle all',f'Start {len(ids):,} songs without holiday music? Back stops and cancels loading.'):return
        window=None;session=None;global_exit=False
        try:
            def transport(method,params):
                if method in READS:return rpc(method,params)
                if method not in ('Player.Stop','Playlist.Clear') and not (method=='Player.SetShuffle' and params.get('shuffle') is False):
                    if not playback_allowed(ids,limit):raise TrialUnavailable('trial-capability-expired')
                validate_write(method,params,set(ids),queue_limit=limit)
                return execute(method,params)
            def resources():
                available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))
                if available<512*1024:raise TrialUnavailable('low-memory-stop')
            stamp=time.time_ns()
            engine=ExpandedTrial(transport,ids,lambda snapshot:save_empty_checkpoint(trial_directory()/f'queue-checkpoint-{stamp}.json',snapshot),
                queue_limit=limit,intent=lambda snapshot,**kw:save_intent(trial_directory()/f'queue-intent-{stamp}.json',snapshot,**kw))
            session=ProgressiveSession(engine,resource_check=resources)
            window=ShuffleLab('AlbumLab.xml',str(ROOT),'Default','1080i')
            window.allowed=ids;window.queue_limit=limit;window.title='Shuffle all · no holiday music'
            window.artwork=ASSETS+ICONS['album'];window.session=session
            window.catalogue=view
            window.selection=SimpleNamespace(album_id='shuffle',disc_numbers_available=False,
                tracks=tuple(SimpleNamespace(song_id=i,disc=0,track=n+1,title=view.songs[i].get('label','Untitled'),duration=0) for n,i in enumerate(ids[:200])))
            window.show()
            deadline=time.monotonic()+5
            while not window.finished:
                if window.initialized and window.getControl(600).size()==min(200,len(ids)):break
                if time.monotonic()>deadline:raise TrialUnavailable('native-player-not-ready')
                xbmc.sleep(20)
            if not window.finished:session.start(ids,confirmed=True)
            while not window.finished:
                if xbmc.Monitor().abortRequested():window.close();break
                active=xbmcgui.Window(10000).getProperty('AsterV2Lab.AlbumWindow')
                if active and str(xbmcgui.getCurrentWindowId())!=active and not window.dialog_open:
                    global_exit=True;window.close();break
                window.refresh();xbmc.sleep(100)
        except Exception as error:
            frames=traceback.extract_tb(error.__traceback__)
            code=str(error) if isinstance(error,(TrialUnavailable,QueueUnavailable)) else ''
            if not code or len(code)>80 or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in code):code='unclassified'
            xbmc.log('AsterMusicShuffle failure='+type(error).__name__+' code='+code+' at '+','.join(f.name+':'+str(f.lineno) for f in frames),xbmc.LOGERROR)
            xbmcgui.Dialog().ok('Shuffle unavailable','The HP trial could not continue safely. Your recovery checkpoint is retained.')
        finally:
            if window:window.close()
            elif session:session.close()
            xbmcgui.Window(10000).clearProperty('AsterV2Lab.AlbumWindow')
            if global_exit:self.close()
            else:self.focus(201)

    def open_album(self,row):
        identity=row['albumid']
        expected=[i for i,song in self.model.catalogue.songs.items() if song.get('albumid')==identity]
        try:selection=read_album(rpc,identity,expected)
        except AlbumUnavailable as error:
            message=('This album has missing track numbers. Album order cannot be guessed; its songs remain available in Songs.'
                     if str(error)=='album-track-number-unavailable' else
                     'The complete album order could not be verified. Refresh the catalogue and try again.')
            xbmcgui.Dialog().ok('Album order unavailable',message);return
        self.open_selection(selection,row)

    def open_song(self,row):
        try:selection=read_song(rpc,row['songid'],row)
        except SelectionUnavailable:
            xbmcgui.Dialog().ok('Song unavailable','The selected song could not be verified. Refresh the catalogue and try again.');return
        self.open_selection(selection,row)

    def open_selection(self,selection,row):
        window=AlbumLab('AlbumLab.xml',str(ROOT),'Default','1080i')
        window.selection=selection;window.title=row.get('label','Album');window.artwork=self.art(row)
        if normal_playback():window.allowed=selection.song_ids;window.queue_limit=20000
        else:
            window.allowed=tuple(i for i in selection.song_ids if i in live_ids())
            window.queue_limit=live_grant()[1]
        global_exit=False
        try:
            window.show()
            while not window.finished:
                if xbmc.Monitor().abortRequested():window.close();break
                active=xbmcgui.Window(10000).getProperty('AsterV2Lab.AlbumWindow')
                if active and str(xbmcgui.getCurrentWindowId())!=active and not window.dialog_open:
                    global_exit=True;window.close();break
                window.refresh();xbmc.sleep(100)
        finally:
            window.close()  # Also clean up when Kodi navigates away globally.
            xbmcgui.Window(10000).clearProperty('AsterV2Lab.AlbumWindow')
            del window
        if global_exit:self.close()
        else:self.focus_grid()

    def open_playlist(self,row):
        try:
            import xbmcvfs
            if self.playlist_reader is None:raise PlaylistUnavailable('playlist-reader-unavailable')
            selection=read_playlist(self.playlist_reader,row['playlistid'],self.model.playlists,self.model.catalogue,
                lambda ids:indexed_mapping(xbmcvfs.translatePath('special://profile/Database/jellyfin.db'),ids))
            if not selection.tracks:
                xbmcgui.Dialog().ok('Empty playlist','This saved playlist has no songs yet. No playback starts.');return
        except PlaylistUnavailable:
            xbmcgui.Dialog().ok('Playlist unavailable','The complete saved order could not be matched to indexed songs. Refresh the catalogue or let Jellyfin finish syncing; no tracks were guessed or omitted.');return
        self.open_selection(selection,row)

    def onAction(self,action):
        key=action.getId()
        if key in BACK:
            if self.rail:self.rail=False;self.prop('Rail','false');self.focus_grid()
            elif self.model.back():self.render();self.focus_grid()
            else:self.close()
            return
        if key not in DIRECTIONS:return
        direction=DIRECTIONS[key];control=self.getFocusId()
        if 500<=control<508:
            self.model.index=control-500
            target=self.model.move_grid(direction)
            if target=='rail':self.rail=True;self.prop('Rail','true');self.focus(9007)
            elif target=='search':self.focus(300)
            elif target=='browse':self.focus(200)
            else:self.focus_grid()
        elif control in (9007,9008):
            if direction=='right':self.rail=False;self.prop('Rail','false');self.focus_grid()
            elif direction in ('up','down'):self.focus(9008 if control==9007 else 9007)
        elif 100<=control<=104:
            if direction=='left':self.focus(max(100,control-1))
            elif direction=='right':self.focus(min(104,control+1))
            elif direction=='down':self.focus(200)
        elif control in (200,201):
            if direction=='down':self.focus_grid()
            elif direction=='up':self.focus(104)
            elif direction=='left':self.focus(200)
            elif direction=='right':self.focus(201)
        elif 300<=control<=305:
            if direction=='left':self.focus_grid()
            elif direction=='up':self.focus(max(300,control-1))
            elif direction=='down':self.focus(min(305,control+1))


def main():
    home=xbmcgui.Window(10000)
    previous=home.getProperty('AsterV2Lab.Window')
    if previous.isdigit() and xbmc.getCondVisibility('Window.IsVisible('+previous+')'):
        xbmcgui.Dialog().notification('Aster Music v2 Lab','The pilot is already open.');return
    view,error=load_catalogue()
    if view is None:
        xbmcgui.Dialog().ok('Aster Music v2 Lab',error or 'Catalogue unavailable');return
    window=MusicLab('MusicLab.xml',str(ROOT),'Default','1080i')
    window.model=LabModel(view)
    try:window.doModal()
    finally:
        home.clearProperty('AsterV2Lab.Window')
        del window


if __name__=='__main__':main()
