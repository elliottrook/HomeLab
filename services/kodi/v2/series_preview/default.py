"""HP-only standalone series preview. No playback, stream or server writes."""
import importlib.util,json,os,sys,time
from pathlib import Path
import xbmc,xbmcgui

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'resources/lib'))
from series_adapter import read_series,READS
from series_model import SeriesUnavailable
from series_view import SeriesSelection,episode_metadata
BACK={9,10,92,216,247,257,275}

def rpc(method,params=None):
    if method not in READS|{'Player.GetActivePlayers','Playlist.GetItems'}:
        raise SeriesUnavailable('read-only-series-preview')
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    if 'error' in result:raise SeriesUnavailable('local-series-read-failed')
    return result.get('result',{})

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

    def onInit(self):
        self.dialog_open=False;self.back_guard_until=0
        self.selection=SeriesSelection(self.snapshot.page,self.snapshot.page.primary_episode_id)
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
        self.setProperty('Series.Mode','HP SERIES PREVIEW · NO PLAYBACK')
        primary=self.snapshot.page.primary_episode_id
        row=next((e for s in self.snapshot.page.seasons for e in s.episodes if e.episode_id==primary),None)
        label={'resume':'Resume','next':'Play next','play':'Play'}.get(self.snapshot.page.primary_action,'Browse episodes')
        self.setProperty('Series.Primary',label+(' · '+row.numbering if row else '')+' · preview')
        self.populate()
        self.setFocusId(300 if self.selection.group else 202)
        self.identity=xbmcgui.getCurrentWindowId();self.ready=True
        xbmcgui.Window(10000).setProperty('AsterSeries.PreviewWindow',str(self.identity))
        self.publish()

    def populate(self):
        group=self.selection.group
        self.setProperty('Series.Season',group.label if group else 'No episodes')
        self.setProperty('Series.SeasonIndex',str(self.selection.season))
        rows=[]
        for index,row in enumerate(group.episodes if group else ()):
            item=xbmcgui.ListItem(label=row.title)
            item.setProperty('Selected','true' if index==self.selection.index else 'false')
            item.setProperty('EpisodeId',str(row.episode_id));item.setProperty('Synopsis',row.synopsis or 'Synopsis unavailable')
            item.setProperty('Metadata',episode_metadata(row))
            item.setProperty('Still',row.thumbnail);item.setProperty('HasStill','true' if row.thumbnail else 'false')
            item.setProperty('Progress',str(row.progress_percent or 0))
            item.setProperty('HasProgress','true' if row.progress_percent is not None else 'false')
            item.setProperty('State','Watched' if row.watched else 'In progress' if row.progress_percent is not None else '')
            item.setProperty('Unavailable','' if row.available else 'Not available')
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
                if self.marked_index is not None:self.getControl(300).getListItem(self.marked_index).setProperty('Selected','false')
                self.getControl(300).getListItem(position).setProperty('Selected','true');self.marked_index=position
            self.pending_index=None;self.selection.select(position)
        row=self.selection.episode
        self.setProperty('Series.SelectedId',str(row.episode_id) if row else '')

    def onClick(self,identity):
        if identity==202:self.close()
        elif identity==201:
            self.publish()
            index=self.dialog('select','Choose season',[s.label for s in self.snapshot.page.seasons],preselect=self.selection.season)
            self.updating=True
            try:
                changed=self.selection.change_season(index)
                if changed:self.populate();self.setFocusId(300)
                else:self.setFocusId(201)
            finally:self.updating=False
            self.publish()
        elif identity in (200,300):
            self.publish();row=self.selection.episode
            if identity==200:
                row=next((e for s in self.snapshot.page.seasons for e in s.episodes
                    if e.episode_id==self.snapshot.page.primary_episode_id),None) or row
            if row:
                self.dialog('ok','Episode preview',row.numbering+' · '+row.title+'\n'+episode_metadata(row)+'\n\n'+(row.synopsis or 'Synopsis unavailable')+'\n\nRead-only preview: nothing was played.')
            self.setFocusId(identity)

    def dialog(self,method,*args,**kwargs):
        self.dialog_open=True
        try:return getattr(xbmcgui.Dialog(),method)(*args,**kwargs)
        finally:self.dialog_open=False;self.back_guard_until=time.monotonic()+.3

    def onAction(self,action):
        key=action.getId();control=self.getFocusId()
        if key in BACK:
            if not self.dialog_open and time.monotonic()>=self.back_guard_until:self.close()
            return
        if control==300 and key==1:self.setFocusId(201 if self.snapshot.page.show_season_picker else 200)
        elif control in (200,201) and key==2 and self.selection.group:self.setFocusId(300)

    def close(self):
        if self.finished:return
        self.finished=True;super().close()

def main():
    if os.uname().nodename!='AsterTV':return
    try:
        if len(sys.argv)!=2 or not sys.argv[1].isdecimal():raise SeriesUnavailable('invalid-show-link')
        if not idle():raise SeriesUnavailable('idle-player-required')
        show_id=int(sys.argv[1]);snapshot=read_series(rpc,show_id,accepted_next())
    except Exception:
        xbmcgui.Dialog().ok('Series preview unavailable','The complete idle series snapshot could not be verified. Nothing was played or changed.');return
    home=xbmcgui.Window(10000)
    if home.getProperty('AsterSeries.PreviewWindow'):return
    window=SeriesPreview('SeriesPreview.xml',str(ROOT),'Default','1080i');window.snapshot=snapshot
    source=xbmcgui.getCurrentWindowId();previous=0
    try:
        previous=xbmcgui.Window(source).getFocusId()
        window.show();monitor=xbmc.Monitor();deadline=time.monotonic()+15
        while not monitor.abortRequested() and not window.finished:
            if not window.ready:
                if time.monotonic()>deadline:raise SeriesUnavailable('preview-initialization-timeout')
            elif not xbmc.getCondVisibility('Window.IsVisible('+str(window.identity)+')'):break
            else:window.publish()
            if monitor.waitForAbort(.1):break
    finally:
        window.close();home.clearProperty('AsterSeries.PreviewWindow')
        for _ in range(20):
            if xbmcgui.getCurrentWindowId()==source:break
            xbmc.sleep(50)
        if xbmcgui.getCurrentWindowId()==source and previous:xbmc.executebuiltin('SetFocus('+str(previous)+')')
        del window

if __name__=='__main__':main()
