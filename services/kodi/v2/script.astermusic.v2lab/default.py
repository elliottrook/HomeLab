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

ASSETS = 'special://home/addons/skin.asterhome/media/'
READS = {'AudioLibrary.GetAlbums','AudioLibrary.GetArtists','AudioLibrary.GetSongs',
         'AudioLibrary.GetAlbumDetails','AudioLibrary.GetArtistDetails','AudioLibrary.GetSongDetails'}
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
            copy=(self.model.category or 'Your music')+' · Read-only design pilot. Select to inspect; playback is not enabled.'
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
                xbmcgui.Dialog().ok('Read-only Music pilot',selected.get('label','Untitled')+'\n\nThis '+self.model.kind+' is indexed in your library. Playback is intentionally disabled in this pilot.')
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
