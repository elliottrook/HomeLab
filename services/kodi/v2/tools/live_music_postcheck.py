"""Read-only in-process HP preservation check after a native Music trial.

RunScript(path,candidate-number,expected-archive-sha256). No queue writes,
credential reads, settings changes or production-host support.
"""
import hashlib,json,os,sqlite3,sys,time
from pathlib import Path
import xml.etree.ElementTree as ET
import xbmc

assert os.uname().nodename=='AsterTV'
candidate=int(sys.argv[1]);expected=sys.argv[2]
assert candidate>0 and len(expected)==64 and all(c in '0123456789abcdef' for c in expected)
def rpc(method,params):
    reply=json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params})))
    assert 'error' not in reply,'native-read-failed'
    return reply['result']

assert not rpc('Player.GetActivePlayers',{})
assert rpc('Playlist.GetItems',{'playlistid':0,'limits':{'start':0,'end':1}})['limits']['total']==0
profile=Path('/storage/.kodi/userdata/addon_data/script.astermusic.v2lab')
assert not (profile/'live-trial.json').exists()
keys=['Window(Home).Property(AsterV2Lab.'+name+')' for name in ('TrialRecovery','AlbumWindow','Window')]
assert not any(rpc('XBMC.GetInfoLabels',{'labels':keys}).values()),'live-or-recovery-window-retained'
stage=Path('/storage/.aster-staging');addons=Path('/storage/.kodi/addons')
baseline=json.loads((stage/'aster-artist-repair-v1-baseline-20261023.json').read_text())
rows=[row for archive in baseline['archives'] for row in archive['files']]
assert len(rows)==153
assert all(hashlib.sha256((addons/row['path']).read_bytes()).hexdigest()==row['sha256'] for row in rows)
manifest=json.loads((stage/f'aster-music-v2lab-0.1.0-candidate{candidate}/manifest.json').read_text())
assert manifest['sha256']==expected
assert hashlib.sha256((stage/f'aster-music-v2lab-0.1.0-candidate{candidate}'/manifest['archive']).read_bytes()).hexdigest()==expected
assert len(manifest['files'])==14
assert all(hashlib.sha256((addons/row['path']).read_bytes()).hexdigest()==row['sha256'] for row in manifest['files'])
settings=ET.parse('/storage/.kodi/userdata/guisettings.xml')
values=sorted((node.get('id'),node.text or '') for node in settings.findall('.//setting')
              if (node.get('id') or '').startswith(('audiooutput.','videoscreen.','locale.')))
av={'count':len(values),'sha256':hashlib.sha256(json.dumps(values).encode()).hexdigest()}
assert av==json.loads(Path('/storage/.aster-checkpoints/aster-music-expanded-trial-20261023/before-candidate14/av-baseline.json').read_text())
connection=sqlite3.connect('file:/storage/.kodi/userdata/Database/MyMusic83.db?mode=ro',uri=True)
try:
    assert connection.execute('SELECT count(*) FROM song s WHERE NOT EXISTS(SELECT 1 FROM song_artist sa WHERE sa.idSong=s.idSong AND sa.idRole=1)').fetchone()[0]==0
    assert connection.execute('PRAGMA integrity_check').fetchall()==[('ok',)]
finally:connection.close()
root=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
output=root/('postcheck-'+str(time.time_ns())+'.json')
with output.open('x') as handle:
    json.dump({'candidate':candidate,'sha256':expected,'lab_files_verified':14,
               'v1_files_verified':153,'av_language_settings_verified':len(values),
               'database_integrity':'ok','missing_primary_artist_links':0,
               'no_player':True,'original_empty_queue':True,'capability_removed':True,
               'all_lab_windows_closed':True},handle)
output.chmod(0o600)
