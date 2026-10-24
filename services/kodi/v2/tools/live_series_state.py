"""Read-only, non-secret HP series lifecycle diagnostic."""
import json,os,time
from pathlib import Path
import xbmc,xbmcgui
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
def rpc(method,params=None):
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    if 'error' in reply:raise RuntimeError('native-read-failed')
    return reply['result']
home=xbmcgui.Window(10000)
data=dict(window=xbmcgui.getCurrentWindowId(),players=rpc('Player.GetActivePlayers'),
    queues=[rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total'] for i in (0,1)],
    series_window=home.getProperty('AsterSeries.PreviewWindow'),recovery=home.getProperty('AsterSeries.Recovery'),
    fence=Path('/storage/.aster-checkpoints/aster-series-playback-20261024/unresolved-start.json').exists())
fixture_file=Path('/storage/.aster-checkpoints/aster-series-playback-20261024/fixture.json')
if fixture_file.exists():
    fixtures=json.loads(fixture_file.read_text())
    data['fixture_progress']=[]
    for fixture in (fixtures.get('fixture'),fixtures.get('resume_fixture')):
        if not fixture:continue
        row=rpc('VideoLibrary.GetEpisodeDetails',dict(episodeid=fixture['episode_id'],properties=['resume','playcount'])).get('episodedetails',{})
        data['fixture_progress'].append(dict(episode_id=fixture['episode_id'],resume=row.get('resume'),playcount=row.get('playcount')))
path=Path('/storage/.aster-checkpoints/aster-series-playback-20261024')/('state-'+str(time.time_ns())+'.json')
with path.open('x') as handle:json.dump(data,handle)
path.chmod(0o600)
