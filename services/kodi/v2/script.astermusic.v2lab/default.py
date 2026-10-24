"""Isolated HP browse pilot: no player, playlist, settings or media writes."""
import json
from pathlib import Path
import sys

import xbmc
import xbmcgui

ROOT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'resources'/'lib'))
from lab_model import LabModel
from music_catalogue import CatalogueUnavailable, read_catalogue
from music_album import AlbumUnavailable, read_album
from music_queue import propose
from queue_reader import QueueUnavailable, read_queue

ASSETS = 'special://home/addons/skin.asterhome/media/'
READS = {'AudioLibrary.GetAlbums','AudioLibrary.GetArtists','AudioLibrary.GetSongs',
         'AudioLibrary.GetAlbumDetails','AudioLibrary.GetArtistDetails','AudioLibrary.GetSongDetails',
         'Player.GetActivePlayers','Player.GetProperties','Playlist.GetItems'}
BACK = {9,10,92,216,247,257,275}
DIRECTIONS = {1:'left',2:'right',3:'up',4:'down'}
ICONS = {'album':'23-music-album.png','artist':'24-music-artist.png','song':'25-music-song.png'}


def rpc(method,params):
    if method not in READS: raise CatalogueUnavailable('read-only-pilot')
    result=json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params})))
    if 'error' in result: raise CatalogueUnavailable('library-read-failed')
    return result.get('result',{})


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
    """Native album screen; all three queue controls are explicit previews."""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.selection=None; self.title=''; self.artwork=''

    def onInit(self):
        self.setProperty('Album.Title',self.title)
        self.setProperty('Album.Art',self.artwork)
        ordering='disc / track' if self.selection.disc_numbers_available else 'track tags · disc numbers unavailable'
        self.setProperty('Album.Count',str(len(self.selection.tracks))+' tracks · ordered by '+ordering)
        self.setProperty('Album.Status','Read-only queue preview · no playback starts')
        items=[]
        for row in self.selection.tracks:
            number=f'{row.disc}.{row.track:02}' if row.disc else str(row.track)
            item=xbmcgui.ListItem(label=number+'  '+row.title)
            item.setProperty('Duration',f'{row.duration//60}:{row.duration%60:02}')
            items.append(item)
        self.getControl(600).reset();self.getControl(600).addItems(items)
        self.setFocusId(600)
        xbmcgui.Window(10000).setProperty('AsterV2Lab.AlbumWindow',str(xbmcgui.getCurrentWindowId()))

    def preview(self,action,ids):
        try:
            snapshot=read_queue(rpc)
            if action=='next' and snapshot.current_index is None:
                xbmcgui.Dialog().ok('Play Next · preview','There is no current music track. Add to Queue can preview an idle queue. Nothing has changed.');return
            plan=propose(snapshot,ids,action=action)
        except (QueueUnavailable,ValueError) as error:
            message={'unsupported-queue-item':'The queue contains a file or stream this preview cannot safely represent.',
                     'unsupported-active-player':'The current player is not a supported music queue.',
                     'queue-changed-during-read':'The queue changed while reading it. Please try again.'}.get(str(error),'Queue preview unavailable. Please retry without changing playback.')
            xbmcgui.Dialog().ok('Queue preview unavailable',message+'\n\nYour queue is unchanged.');return
        names={'next':'Play Next','append':'Add to Queue','replace':'Replace Queue'}
        effect=('Would replace the existing queue. Live replacement will require confirmation.'
                if plan.replaces_queue else 'Would preserve the current track and existing queue order.')
        xbmcgui.Dialog().ok(names[action]+' · preview',f'{len(ids)} selected tracks · {len(snapshot.song_ids)} currently queued · {len(plan.song_ids)} proposed total.\n\n'+effect+'\n\nPreview only. Nothing was played, saved or changed.')

    def onClick(self,control):
        if control in (401,402,403):
            self.preview({401:'next',402:'append',403:'replace'}[control],self.selection.song_ids)
        elif control==600:
            index=self.getControl(600).getSelectedPosition()
            if not 0<=index<len(self.selection.tracks):return
            option=xbmcgui.Dialog().select('This track · preview',['Play Next','Add to Queue','Replace Queue'])
            if option in (0,1,2):self.preview(('next','append','replace')[option],(self.selection.tracks[index].song_id,))

    def onAction(self,action):
        key=action.getId()
        if key in BACK:self.close();return
        control=self.getFocusId()
        if control==600 and key==1:self.setFocusId(401);return
        if control in (401,402,403) and key in DIRECTIONS:
            if key==1:self.setFocusId(max(401,control-1))
            elif key==2:self.setFocusId(min(403,control+1))
            elif key in (3,4):self.setFocusId(600)


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
            xbmcgui.Dialog().ok('Shuffle all · eligibility preview',f"{len(s['eligible_ids']):,} eligible tracks; {s['excluded']:,} excluded by track or album holiday tags.\n\nNo playback starts and your queue is unchanged.")
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
        try:window.doModal()
        finally:
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
