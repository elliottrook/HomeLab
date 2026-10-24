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
_require((not any(rpc('XBMC.GetInfoLabels',{'labels':keys}).values())), ('live-or-recovery-window-retained'))
stage=Path('/storage/.aster-staging');addons=Path('/storage/.kodi/addons')
baseline=json.loads((stage/'aster-artist-repair-v1-baseline-20261023.json').read_text())
rows=[row for archive in baseline['archives'] for row in archive['files']]
_require((len(rows)==153), ('native-check-failed'))
overlay_file=Path('/storage/.aster-checkpoints/aster-floating-controls-20261024/overlay-manifest.json')
overrides={}
if overlay_file.exists():
    overlay=json.loads(overlay_file.read_text())
    _require((overlay['sha256']=='591cc32b4f9c3a621e395df744d3a8c3b5f7d178623ff8094fda072fa79a16d0'), ('native-check-failed'))
    overrides={'skin.asterhome/'+r['path']:r['sha256'] for r in overlay['files'] if r['path'].startswith('1080i/')}
    _require((len(overrides)==4), ('native-check-failed'))
    _require((all(hashlib.sha256((addons/'skin.asterhome'/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in overlay['files'])), ('native-check-failed'))
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
               'v1_files_verified':153-len(overrides),'approved_overlay_pages_verified':len(overrides),
               'av_language_settings_verified':len(values),
               'database_integrity':'ok','missing_primary_artist_links':0,
               'no_player':True,'original_empty_queue':True,'capability_removed':True,
               'all_lab_windows_closed':True,'approved_normal_playback':normal},handle)
output.chmod(0o600)
