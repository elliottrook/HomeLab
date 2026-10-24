"""Read-only in-process HP preservation check after a native Music trial.

RunScript(path,candidate-number,expected-archive-sha256). No queue writes,
credential reads, settings changes or production-host support.
"""


def _require(condition,message="native-check-failed"):
    """Unlike assert, this check remains active in Kodi optimized Python."""
    if not condition:raise AssertionError(message)

import hashlib,json,os,sqlite3,sys,time
from pathlib import Path
import xml.etree.ElementTree as ET
import xbmc

_require((os.uname().nodename=='AsterTV'), ('native-check-failed'))
candidate=int(sys.argv[1]);expected=sys.argv[2]
expected_count=int(sys.argv[3]) if len(sys.argv)>3 else 14
_require((candidate>0 and len(expected)==64 and all(c in '0123456789abcdef' for c in expected)), ('native-check-failed'))
def rpc(method,params):
    reply=json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params})))
    _require(('error' not in reply), ('native-read-failed'))
    return reply['result']

_require((not rpc('Player.GetActivePlayers',{})), ('native-check-failed'))
_require((rpc('Playlist.GetItems',{'playlistid':0,'limits':{'start':0,'end':1}})['limits']['total']==0), ('native-check-failed'))
_require((rpc('Player.GetProperties',{'playerid':0,'properties':['shuffled']}).get('shuffled') is False), 'idle-shuffle-not-off')
profile=Path('/storage/.kodi/userdata/addon_data/script.astermusic.v2lab')
_require((not (profile/'live-trial.json').exists()), ('native-check-failed'))
normal=False
if (profile/'normal-playback.json').exists():
    _require((json.loads((profile/'normal-playback.json').read_text())==dict(enabled=True,queue_limit=20000,host='AsterTV')), ('native-check-failed'))
    normal=True
if (profile/'shared-playlist-pending.json').exists():
    _require((json.loads((profile/'shared-playlist-pending.json').read_text()).get('status')=='verified'), ('shared-save-recovery-required'))
keys=['Window(Home).Property(AsterV2Lab.'+name+')' for name in ('TrialRecovery','AlbumWindow','Window')]
keys.append('Window(Home).Property(AsterSeries.PreviewWindow)')
keys.append('Window(Home).Property(AsterSeries.Recovery)')
_require(not Path('/storage/.aster-checkpoints/aster-series-playback-20261024/unresolved-start.json').exists(),'series-recovery-required')
_require((not any(rpc('XBMC.GetInfoLabels',{'labels':keys}).values())), ('live-or-recovery-window-retained'))
stage=Path('/storage/.aster-staging');addons=Path('/storage/.kodi/addons')
baseline=json.loads((stage/'aster-artist-repair-v1-baseline-20261023.json').read_text())
rows=[row for archive in baseline['archives'] for row in archive['files']]
_require((len(rows)==153), ('native-check-failed'))
base_paths={row['path'] for row in rows}
overlay_file=Path('/storage/.aster-checkpoints/aster-floating-controls-20261024/overlay-manifest.json')
overrides={}
if overlay_file.exists():
    overlay=json.loads(overlay_file.read_text())
    _require((overlay['sha256']=='591cc32b4f9c3a621e395df744d3a8c3b5f7d178623ff8094fda072fa79a16d0'), ('native-check-failed'))
    overrides={'skin.asterhome/'+r['path']:r['sha256'] for r in overlay['files'] if r['path'].startswith('1080i/')}
    _require((len(overrides)==4), ('native-check-failed'))
    _require((all(hashlib.sha256((addons/'skin.asterhome'/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in overlay['files'])), ('native-check-failed'))
overlay_count=len(overrides)
integration_file=Path('/storage/.aster-checkpoints/aster-music-integration-20261024/active-manifest.json')
integration_count=0
if integration_file.exists():
    _require(len(sys.argv) in (5,6,7),'integration-manifest-proof-required')
    integration_sha=sys.argv[4]
    _require(len(integration_sha)==64 and all(c in '0123456789abcdef' for c in integration_sha),'integration-sha')
    _require(hashlib.sha256(integration_file.read_bytes()).hexdigest()==integration_sha,'integration-manifest-hash')
    integration=json.loads(integration_file.read_text())
    _require(integration.get('schema')==1 and integration.get('kind')=='hp-normal-music-integration','integration-kind')
    expected_paths={'tools/music_data.py','tools/aster_v2_music.py','1080i/IncludesMusic.xml',
        '1080i/custom_1113_music.xml','1080i/custom_1114_albums.xml','1080i/custom_1115_artists.xml',
        '1080i/custom_1116_songs.xml','1080i/custom_1117_playlists.xml'}
    _require(len(integration['files'])==8 and {r['path'] for r in integration['files']}==expected_paths,'integration-targets')
    for row in integration['files']:
        _require(hashlib.sha256((addons/'skin.asterhome'/row['path']).read_bytes()).hexdigest()==row['sha256'],'integration-member-hash')
        overrides['skin.asterhome/'+row['path']]=row['sha256']
    integration_count=8
rail_file=Path('/storage/.aster-checkpoints/aster-floating-rail-20261024/active-manifest.json')
rail_count=0
if rail_file.exists():
    _require(len(sys.argv) in (6,7),'rail-manifest-proof-required')
    _require(hashlib.sha256(rail_file.read_bytes()).hexdigest()==sys.argv[5],'rail-manifest-hash')
    rail=json.loads(rail_file.read_text())
    _require(rail.get('schema')==1 and rail.get('kind')=='hp-floating-rail' and rail.get('path')=='1080i/IncludesHub.xml','rail-target')
    _require(hashlib.sha256((addons/'skin.asterhome'/rail['path']).read_bytes()).hexdigest()==rail['sha256'],'rail-member-hash')
    overrides['skin.asterhome/'+rail['path']]=rail['sha256'];rail_count=1
series_file=Path('/storage/.aster-checkpoints/aster-series-integration-20261024/active-manifest.json')
series_count=0
if series_file.exists():
    import re
    _require(len(sys.argv)==7 and hashlib.sha256(series_file.read_bytes()).hexdigest()==sys.argv[6],'series-manifest-proof')
    series=json.loads(series_file.read_text())
    _require(series.get('schema')==1 and series.get('kind')=='hp-series-integration','series-kind')
    _require(len(series['files'])==2 and {r['path'] for r in series['files']}=={'tools/select_dispatch.py','tools/aster_v2_series.py'},'series-targets')
    for row in series['files']:
        _require(hashlib.sha256((addons/'skin.asterhome'/row['path']).read_bytes()).hexdigest()==row['sha256'],'series-member-hash')
        overrides['skin.asterhome/'+row['path']]=row['sha256']
    _require(re.fullmatch(r'aster-series-preview[1-9][0-9]*',series['series_stage']),'series-stage')
    player_stage=stage/series['series_stage']
    _require(hashlib.sha256((player_stage/'manifest.json').read_bytes()).hexdigest()==series['series_manifest_sha256'],'series-stage-hash')
    player=json.loads((player_stage/'manifest.json').read_text())
    _require(player.get('kind')=='hp-series-player' and len(player['files'])==6,'series-player-kind')
    _require(all(hashlib.sha256((player_stage/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in player['files']),'series-player-members')
    series_count=2
_require((all(hashlib.sha256((addons/row['path']).read_bytes()).hexdigest()==overrides.get(row['path'],row['sha256']) for row in rows)), ('native-check-failed'))
manifest=json.loads((stage/f'aster-music-v2lab-0.1.0-candidate{candidate}/manifest.json').read_text())
_require((manifest['sha256']==expected), ('native-check-failed'))
_require((hashlib.sha256((stage/f'aster-music-v2lab-0.1.0-candidate{candidate}'/manifest['archive']).read_bytes()).hexdigest()==expected), ('native-check-failed'))
_require((len(manifest['files'])==expected_count), ('native-check-failed'))
_require((all(hashlib.sha256((addons/row['path']).read_bytes()).hexdigest()==row['sha256'] for row in manifest['files'])), ('native-check-failed'))
settings=ET.parse('/storage/.kodi/userdata/guisettings.xml')
values=sorted((node.get('id'),node.text or '') for node in settings.findall('.//setting')
              if (node.get('id') or '').startswith(('audiooutput.','videoscreen.','locale.')))
av={'count':len(values),'sha256':hashlib.sha256(json.dumps(values).encode()).hexdigest()}
_require((av==json.loads(Path('/storage/.aster-checkpoints/aster-music-expanded-trial-20261023/before-candidate14/av-baseline.json').read_text())), ('native-check-failed'))
connection=sqlite3.connect('file:/storage/.kodi/userdata/Database/MyMusic83.db?mode=ro',uri=True)
try:
    _require((connection.execute('SELECT count(*) FROM song s WHERE NOT EXISTS(SELECT 1 FROM song_artist sa WHERE sa.idSong=s.idSong AND sa.idRole=1)').fetchone()[0]==0), ('native-check-failed'))
    _require((connection.execute('PRAGMA integrity_check').fetchall()==[('ok',)]), ('native-check-failed'))
finally:connection.close()
root=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
output=root/('postcheck-'+str(time.time_ns())+'.json')
with output.open('x') as handle:
    json.dump({'candidate':candidate,'sha256':expected,'lab_files_verified':expected_count,
               'checks_enforced':True,'python_optimization':sys.flags.optimize,
               'music_shuffle_off':True,
               'v1_files_verified':sum(row['path'] not in overrides for row in rows),'approved_overlay_pages_verified':overlay_count,
               'approved_normal_music_files_verified':integration_count,
               'approved_floating_rail_files_verified':rail_count,
               'approved_series_integration_files_verified':series_count,
               'av_language_settings_verified':len(values),
               'database_integrity':'ok','missing_primary_artist_links':0,
               'no_player':True,'original_empty_queue':True,'capability_removed':True,
               'all_lab_windows_closed':True,'approved_normal_playback':normal},handle)
output.chmod(0o600)
