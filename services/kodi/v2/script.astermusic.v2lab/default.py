"""Isolated HP Music pilot; live writes require a temporary three-song trial."""
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
from music_queue import propose,nonholiday_shuffle
from queue_reader import QueueUnavailable, read_queue
from music_trial import TrialPlayer,TrialUnavailable,capability,save_empty_checkpoint,validate_write
from music_expanded_trial import ExpandedTrial,TrialCancelled,expanded_capability,save_intent
from music_progressive import ProgressiveSession

ASSETS = 'special://home/addons/skin.asterhome/media/'
READS = {'AudioLibrary.GetAlbums','AudioLibrary.GetArtists','AudioLibrary.GetSongs',
         'AudioLibrary.GetAlbumDetails','AudioLibrary.GetArtistDetails','AudioLibrary.GetSongDetails',
         'Player.GetActivePlayers','Player.GetProperties','Player.GetItem','Playlist.GetItems'}
BACK = {9,10,92,216,247,257,275}
DIRECTIONS = {1:'left',2:'right',3:'up',4:'down'}
ICONS = {'album':'23-music-album.png','artist':'24-music-artist.png','song':'25-music-song.png'}


def rpc(method,params):
    if method not in READS: raise CatalogueUnavailable('read-only-pilot')
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

    def dialog(self,method,*args):
        # Native Back may also reach the underlying WindowXML callback while
        # a Python modal is unwinding. Cancel must not become a second exit.
        self.dialog_open=True
        result=None
        try:
            result=getattr(xbmcgui.Dialog(),method)(*args)
            if method=='yesno':xbmc.log('AsterMusicTrial confirmation='+str(bool(result)),xbmc.LOGINFO)
            return result
        finally:
            self.dialog_open=False
            cancelled=result is False or (method=='select' and type(result) is int and result<0)
            self.back_guard_until=time.monotonic()+.3 if cancelled else 0

    def onInit(self):
        self.setProperty('Album.Context','ALBUM / QUEUE PREVIEW')
        self.setProperty('Album.TrackHeading','Tracks')
        self.setProperty('Album.Title',self.title)
        self.setProperty('Album.Id',str(self.selection.album_id))
        self.setProperty('Album.Art',self.artwork)
        ordering='disc / track' if self.selection.disc_numbers_available else 'track tags · disc numbers unavailable'
        self.setProperty('Album.Count',str(len(self.selection.tracks))+' tracks · ordered by '+ordering)
        self.setProperty('Album.Status','Read-only queue preview · no playback starts')
        self.setProperty('Album.Live','true' if self.allowed else 'false')
        self.setProperty('Album.Help','Preview only · select a track for its queue options. Back returns to the same album tile. No playback or queue changes.')
        if self.allowed:
            self.setProperty('Album.Status',f'HP live trial · {len(self.allowed)} approved tracks · Back stops and restores the original empty queue')
            self.setProperty('Album.Help','Live test: approved tracks only. OK opens track actions. Replace needs confirmation; stop before replacing. Back stops this trial and restores the original queue.')
            for control,left,width,label in ((401,470,110,'Next'),(402,600,110,'Add'),(403,730,110,'Replace')):
                self.getControl(control).setPosition(left,930);self.getControl(control).setWidth(width);self.getControl(control).setLabel(label)
        items=[]
        for row in self.selection.tracks:
            number=f'{row.disc}.{row.track:02}' if row.disc else str(row.track)
            item=xbmcgui.ListItem(label=number+'  '+row.title)
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
        if self.allowed:
            if control==400:
                self.live('toggle',self.allowed)
            elif control==404:self.live('stop',())
            elif control in (401,402,403):self.live({401:'next',402:'append',403:'replace'}[control],self.allowed)
            elif control==600:
                index=self.getControl(600).getSelectedPosition()
                if not 0<=index<len(self.selection.tracks):return
                identity=self.selection.tracks[index].song_id
                if identity not in self.allowed:
                    self.dialog('ok','Bounded HP trial','This track is outside the approved test selection. No changes made.');return
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

    def live(self,action,ids):
        try:
            if action=='toggle':
                if self.trial and self.trial.observe().current_index is not None:
                    speed=rpc('Player.GetProperties',{'playerid':0,'properties':['speed']}).get('speed')
                    action='resume' if speed==0 else 'pause'
                else:action='play'
            if action not in ('stop',) and not set(self.allowed)<=set(live_ids()):
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
                    if method not in ('Player.Stop','Playlist.Clear'):
                        granted,limit=live_grant()
                        if limit!=self.queue_limit or not set(self.allowed)<=set(granted):
                            raise TrialUnavailable('trial-capability-expired')
                    validate_write(method,params,self.allowed,queue_limit=self.queue_limit)
                    xbmc.log('AsterMusicTrial write='+method,xbmc.LOGINFO)
                    return execute(method,params)
                stamp=time.time_ns()
                self.trial=ExpandedTrial(transport,self.allowed,lambda snapshot:save_empty_checkpoint(
                    trial_directory()/f'queue-checkpoint-{stamp}.json',snapshot),queue_limit=self.queue_limit,
                    intent=lambda snapshot,**kw:save_intent(trial_directory()/f'queue-intent-{stamp}.json',snapshot,**kw))
            if action=='play':self.start_cancellable(ids,confirmed)
            elif action in ('pause','resume'):self.trial.pause(action=='resume')
            elif action=='stop':self.trial.stop()
            else:self.trial.edit(action,ids,confirmed=confirmed)
            self.setProperty('Album.Status','HP trial · '+action+' completed · Back stops and restores the original queue')
        except TrialCancelled:
            self.setProperty('Album.Status','Start cancelled · playback stopped and original empty queue restored')
        except (TrialUnavailable,QueueUnavailable,ValueError,OSError) as error:
            message={'replacement-confirmation-required':'Replacement was not confirmed.',
                     'stop-before-replace':'Stop this trial before replacing its queue.',
                     'three-item-trial-limit':'This first trial is limited to three queued items. Choose one track or stop and replace.',
                     'trial-capability-expired':'The live trial approval has expired. Back will stop and restore the queue.',
                     'idle-empty-queue-required':'The HP must be idle with an empty music queue before this trial.',
                     'external-queue-change':'The queue changed outside this trial. No further queue changes will be made.'}.get(str(error),'The live trial could not complete safely. Stop testing and retain the checkpoint.')
            self.setProperty('Album.Status','Trial action refused · '+str(error))
            self.dialog('ok','Aster Music trial',message)

    def start_cancellable(self,ids,confirmed):
        """Only the main thread touches GUI; never abandon an in-flight writer."""
        progress=xbmcgui.DialogProgress();progress.create('Starting Aster Music','Preparing the verified album queue. Back cancels this start.')
        errors=[];counts=[0,len(ids)];self.dialog_open=True
        self.trial.cancel.clear()
        self.trial.progress=lambda done,total:counts.__setitem__(slice(None),[done,total])
        def work():
            try:self.trial.play(ids,confirmed=confirmed)
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

    def close(self):
        xbmc.log('AsterMusicTrial close='+','.join(frame.name for frame in traceback.extract_stack(limit=3))+' finished='+str(self.finished),xbmc.LOGINFO)
        if self.finished:return
        self.finished=True
        try:
            if self.trial:self.trial.close()
        except (TrialUnavailable,QueueUnavailable,ValueError):
            xbmcgui.Window(10000).setProperty('AsterV2Lab.TrialRecovery','required')
            xbmcgui.Dialog().notification('Music trial recovery required','Unexpected playback/queue state. Checkpoint retained; do not continue testing.')
        finally:super().close()

    def onAction(self,action):
        if self.finished:return
        key=action.getId()
        if key in BACK:
            if not self.dialog_open and time.monotonic()>=self.back_guard_until:self.close()
            return
        control=self.getFocusId()
        buttons=(400,404,401,402,403) if self.allowed else (401,402,403)
        if control==600 and key==1:self.setFocusId(buttons[0]);return
        if control in buttons and key in DIRECTIONS:
            index=buttons.index(control)
            if key==1:self.setFocusId(buttons[max(0,index-1)])
            elif key==2:self.setFocusId(buttons[min(len(buttons)-1,index+1)])
            elif key in (3,4):self.setFocusId(600)


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

    def onInit(self):
        super().onInit()
        self.setProperty('Album.Context','SHUFFLE ALL / NO HOLIDAY MUSIC')
        self.setProperty('Album.Count',f'{len(self.allowed):,} verified songs')
        self.setProperty('Album.Help','Select a loaded song to play it. Previous / Next page browse the queue; Current returns to the playing song. Stop or Back stops and cancels loading.')
        for identity,label in ((401,'Previous'),(402,'Next page'),(403,'Current')):
            self.getControl(identity).setVisible(True);self.getControl(identity).setLabel(label)
        self.render_page()
        self.setFocusId(400)
        self.initialized=True

    def render_page(self):
        ids=self.allowed[self.page_offset:self.page_offset+200]
        self.setProperty('Album.TrackHeading',f'Queue · {self.page_offset+1:,}–{self.page_offset+len(ids):,} / {len(self.allowed):,}')
        rows=[]
        for n,identity in enumerate(ids):
            item=xbmcgui.ListItem(label=f'{self.page_offset+n+1:,}  '+self.catalogue.songs[identity].get('label','Untitled'))
            item.setProperty('NowPlaying','true' if identity==self.current_song else 'false');rows.append(item)
        self.getControl(600).reset();self.getControl(600).addItems(rows)

    def refresh(self):
        if self.control_worker and not self.control_worker.is_alive():
            self.control_worker.join();self.control_worker=None;self.next_player_update=0
            if self.control_errors:
                error=self.control_errors.pop(0)
                if isinstance(error,TrialUnavailable) and str(error)=='selected-track-not-loaded':
                    self.dialog('ok','Still loading','This song has not reached the native queue yet. Choose a loaded song or wait.')
                else:raise TrialUnavailable('player-control-failed')
        state=self.session.status()
        if state['phase']=='failed':raise TrialUnavailable(state['error'] or 'progressive-fill-failed')
        if state['loaded']!=self.loaded or state['phase']!=self.last_phase:
            self.loaded=state['loaded'];self.last_phase=state['phase']
            self.setProperty('Album.Status',f"{state['loaded']:,} / {state['total']:,} queued · "+
                ('Ready' if state['phase']=='ready' else 'Loading in background · Back cancels safely'))
        if time.monotonic()>=self.next_player_update:
            self.next_player_update=time.monotonic()+1
            props=rpc('Player.GetProperties',{'playerid':0,'properties':['position','speed']})
            position=props.get('position')
            if type(position) is int and 0<=position<len(self.allowed):
                identity=self.allowed[position]
                item=rpc('Player.GetItem',{'playerid':0,'properties':[]}).get('item',{})
                if item.get('type')=='song' and item.get('id')==identity:
                    self.current_position=position
                    if identity!=self.current_song:
                        visible=self.allowed[self.page_offset:self.page_offset+200]
                        if self.current_song in visible:
                            self.getControl(600).getListItem(visible.index(self.current_song)).setProperty('NowPlaying','false')
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
                        if not self.control_worker:self.getControl(400).setLabel('Resume' if self.paused else 'Pause')

    def control(self,action,value):
        if self.control_worker:return
        def work():
            try:
                if action=='pause':self.session.pause(value)
                else:self.session.select(value)
            except Exception as error:self.control_errors.append(error)
        self.getControl(400).setLabel('Updating…')
        self.control_worker=threading.Thread(target=work,name='AsterMusicControl')
        self.control_worker.start()

    def onClick(self,control):
        if self.finished:return
        try:
            if control==400:
                self.control('pause',self.paused)
            elif control==404:self.close()
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
            if not self.dialog_open and time.monotonic()>=self.back_guard_until:self.close()
            return
        control=self.getFocusId()
        buttons=(400,404,401,402,403)
        if control in buttons:
            if key in (1,2):self.setFocusId(buttons[max(0,min(len(buttons)-1,buttons.index(control)+(1 if key==2 else -1)))])
            elif key in (3,4):self.setFocusId(600)
        elif control==600 and key==1:self.setFocusId(400)

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
        self.model=None; self.rail=False; self.pending_focus=None; self.art_cache={}

    def onInit(self):
        self.setProperty('Lab.Rail','false')
        self.prop('Status','Read-only pilot · no playback or library changes')
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
        self.prop('Heading','Browse genres' if self.model.mode=='genres' else self.model.category+' / '+self.model.kind.title()+'s')
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
            copy=(self.model.category or 'Your music')+' · Select an album for ordered tracks and queue previews. Playback remains disabled.'
        self.prop('Copy',copy)
        self.prop('HeroArt',self.art(row) if row else ASSETS+ICONS['album'])
        self.prop('Shuffle',f"{len(self.model.catalogue.shuffle_summary['eligible_ids']):,} eligible tracks · preview only")

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
                else:xbmcgui.Dialog().ok('Read-only Music pilot',selected.get('label','Untitled')+'\n\nThis '+self.model.kind+' is indexed in your library. Playback is intentionally disabled in this pilot.')
            else:self.render();self.focus_grid()
        elif control in (100,101,102):
            self.model.set_kind({100:'album',101:'artist',102:'song'}[control]);self.render();self.focus_grid()
        elif control==103:
            xbmcgui.Dialog().ok('Playlists','Existing playlists remain in ordinary Aster Music. This isolated pilot tests Genres, Albums, Artists and Songs only.')
        elif control==104:
            self.model.genres();self.render();self.focus_grid()
        elif control==200:self.focus_grid()
        elif control==201:
            s=self.model.catalogue.shuffle_summary
            granted,limit=live_grant()
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
                if method not in ('Player.Stop','Playlist.Clear'):
                    grant,current_limit=live_grant()
                    if current_limit!=limit or not set(ids)<=set(grant):raise TrialUnavailable('trial-capability-expired')
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
                if active and str(xbmcgui.getCurrentWindowId())!=active:
                    global_exit=True;window.close();break
                window.refresh();xbmc.sleep(100)
        except Exception as error:
            frames=traceback.extract_tb(error.__traceback__)
            xbmc.log('AsterMusicShuffle failure='+type(error).__name__+' at '+','.join(f.name+':'+str(f.lineno) for f in frames),xbmc.LOGERROR)
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
        window=AlbumLab('AlbumLab.xml',str(ROOT),'Default','1080i')
        window.selection=selection;window.title=row.get('label','Album');window.artwork=self.art(row)
        window.allowed=tuple(i for i in selection.song_ids if i in live_ids())
        window.queue_limit=live_grant()[1]
        try:window.doModal()
        finally:
            window.close()  # Also clean up when Kodi navigates away globally.
            xbmcgui.Window(10000).clearProperty('AsterV2Lab.AlbumWindow')
            del window
        self.focus_grid()

    def onAction(self,action):
        key=action.getId()
        if key in BACK:
            if self.rail:self.rail=False;self.prop('Rail','false');self.focus_grid()
            elif self.model.mode=='detail':self.model.genres();self.render();self.focus_grid()
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
