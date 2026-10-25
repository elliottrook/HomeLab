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
keys.append('Window(Home).Property(AsterVideo.ScrubOpen)')
keys.extend('Window(Home).Property(AsterSearch.'+name+')' for name in ('Open','DetailOpen','Ready'))
keys.append('Window(Home).Property(AsterSearch.Handoff)')
keys.extend('Window(Home).Property(AsterMovie.'+name+')' for name in ('Window','Ready','Phase'))
_require(not Path('/storage/.aster-checkpoints/aster-movie-playback-20261024/unresolved-start.json').exists(),'movie-recovery-required')
_require(not Path('/storage/.aster-checkpoints/aster-global-search-20261024/handoff-pending.json').exists(),'search-handoff-recovery-required')
_require(not Path('/storage/.aster-checkpoints/aster-series-playback-20261024/unresolved-start.json').exists(),'series-recovery-required')
_require(not Path('/storage/.aster-checkpoints/aster-video-scrub-20261024/unresolved-seek.json').exists(),'scrub-recovery-required')
_require((not any(rpc('XBMC.GetInfoLabels',{'labels':keys}).values())), ('live-or-recovery-window-retained'))
stage=Path('/storage/.aster-staging');addons=Path('/storage/.kodi/addons')
baseline=json.loads((stage/'aster-artist-repair-v1-baseline-20261023.json').read_text())
rows=[row for archive in baseline['archives'] for row in archive['files']]
_require((len(rows)==153), ('native-check-failed'))
base_paths={row['path'] for row in rows}
search_file=Path('/storage/.aster-checkpoints/aster-global-search-20261024/active-manifest.json')
search_dispatch_sha=None;search_count=0;search_home_sha=None
if search_file.exists():
    _require(len(sys.argv)==9 and hashlib.sha256(search_file.read_bytes()).hexdigest()==sys.argv[8],'search-manifest-proof')
    search_manifest=json.loads(search_file.read_text())
    search_linked=search_manifest.get('kind')=='hp-search-playerlinks'
    _require(search_manifest.get('kind') in ('hp-search-details','hp-search-playerlinks')
        and len(search_manifest['files'])==((13 if search_manifest.get('movie_page')==11130 else 10 if search_manifest.get('artist_native_window')==11129 else 9 if search_manifest.get('artist_albums') is True else 8) if search_linked else 6),'search-details-kind')
    _require(search_manifest.get('dispatcher_before_sha256')=='466b69269e56d8699838aabbe72ae533a580909603855850a047bf02e76d1a0e','search-dispatch-predecessor')
    search_stages=[stage/name for name in ('aster-global-search-ui3','aster-global-search-ui4','aster-global-search-ui5','aster-global-search-ui6','aster-global-search-ui7','aster-global-search-ui8','aster-global-search-ui9','aster-global-search-ui10','aster-global-search-ui11','aster-global-search-ui12','aster-global-search-ui13','aster-global-search-ui14')
        if (stage/name/'manifest.json').exists() and hashlib.sha256((stage/name/'manifest.json').read_bytes()).hexdigest()==sys.argv[8]]
    _require(len(search_stages)==1,'search-stage-manifest');search_stage=search_stages[0]
    for member in search_manifest['files']:
        _require(hashlib.sha256((search_stage/member['path']).read_bytes()).hexdigest()==member['sha256'],'search-stage-member')
    for member_name,target in (('custom_1127_search.xml','1080i/custom_1127_search.xml'),
                               ('custom_1128_searchdetails.xml','1080i/custom_1128_searchdetails.xml'),
                               ('select_dispatch.py','tools/select_dispatch.py')):
        member=next(r for r in search_manifest['files'] if r['path']=='overlay/'+member_name)
        _require(hashlib.sha256((addons/'skin.asterhome'/target).read_bytes()).hexdigest()==member['sha256'],'search-installed-member')
        if member_name=='select_dispatch.py':search_dispatch_sha=member['sha256']
    search_count=3
    if search_linked:
        _require(search_manifest.get('home_before_sha256')==('ca2866a0b306844f8a71534ceaecc77ee1e5946d1f4b6b37c9694d7dda94bb44' if search_manifest.get('movie_page')==11130 else '347b4e47d93ed5d25077d00754a05742d0843f091244e9194bc8db1fd305d575'
            if search_manifest.get('artist_albums') is True else '09e5eb4a9103a10c2bd591683a254a1dd374030598444dafc1260124b7079fa1'),'search-home-predecessor')
        member=next(r for r in search_manifest['files'] if r['path']=='overlay/Home.xml')
        _require(hashlib.sha256((addons/'skin.asterhome/1080i/Home.xml').read_bytes()).hexdigest()==member['sha256'],'search-home-member')
        search_home_sha=member['sha256'];search_count=4
        if search_manifest.get('artist_native_window')==11129:
            member=next(r for r in search_manifest['files'] if r['path']=='overlay/custom_1129_artistalbums.xml')
            _require(hashlib.sha256((addons/'skin.asterhome/1080i/custom_1129_artistalbums.xml').read_bytes()).hexdigest()==member['sha256'],'search-artist-window')
            search_count=5
        if search_manifest.get('movie_page')==11130:
            sys.path.insert(0,str(search_stage/'resources/lib'))
            from movie_player import verify_stage
            verify_stage();search_count=6
overlay_file=Path('/storage/.aster-checkpoints/aster-floating-controls-20261024/overlay-manifest.json')
overrides={}
books_count=0;books_overrides={}
books_file=Path('/storage/.aster-checkpoints/aster-books-sync-20261025/active-manifest.json')
if books_file.exists():
    books=json.loads(books_file.read_text())
    accepted_books={'aster-books-sync1':'252f182781531cb9e54aaaeeb58a9ddc1bbb0e1eb08985a94908a1c16d62e89a',
        'aster-books-sync2':'fce7bf41f64e7617a62a26af322ae98460eafd6ec87efc681ed812d15ef5485f',
        'aster-books-sync3':'7bc5c6ec96c8c0bfb0a18272e8da54ecd4bb647622e150864dc229aa41576de9',
        'aster-books-sync4':'d332a979018d92add2999909e4cf272190624c54bf4db5e0f1fb12c281f85af6',
        'aster-books-sync5':'010e23df40c70e1eaeeb478e359b9da7cb56223549701a3795aea2defa676ff8',
        'aster-books-sync6':'dd502b6770ec6c0f76e4c2fb4182c54c4b84e4c5162a70e0c0dd2a205a643dd7'}
    books_name=books.get('stage');_require(books_name in accepted_books and hashlib.sha256(books_file.read_bytes()).hexdigest()==accepted_books[books_name],'books-sync-manifest')
    expected_books_count=13 if books_name=='aster-books-sync6' else 9
    _require(books.get('kind')=='hp-books-shared-progress.v1' and len(books['files'])==expected_books_count,'books-sync-contract')
    _require((stage/books_name/'manifest.json').read_bytes()==books_file.read_bytes(),'books-sync-stage')
    for member in books['files']:
        _require(hashlib.sha256((Path('/storage')/member['path']).read_bytes()).hexdigest()==member['sha256'],'books-sync-installed')
        _require(hashlib.sha256((stage/books_name/'payload'/member['path']).read_bytes()).hexdigest()==member['sha256'],'books-sync-payload')
        if member['path'].startswith('.kodi/addons/'):books_overrides[member['path'][len('.kodi/addons/'):]]=member['sha256']
    health=rpc('XBMC.GetInfoLabels',{'labels':['Window(Home).Property(AsterBooks.SyncService)','Window(Home).Property(AsterBooks.SyncHeartbeat)']})
    _require(health.get('Window(Home).Property(AsterBooks.SyncService)')=='ready','books-sync-service-not-ready')
    _require(-5<=time.time()-float(health.get('Window(Home).Property(AsterBooks.SyncHeartbeat)') or 0)<=30,'books-sync-service-stale')
    journal=Path('/storage/.kodi/userdata/addon_data/plugin.audio.asterbooks/progress-journal')
    _require(all(json.loads(p.read_text()).get('status')=='verified' for p in journal.glob('*.json')),'books-sync-write-needs-review')
    books_count=expected_books_count
canonical_count=0
canonical_overrides={}
canonical_file=Path('/storage/.aster-checkpoints/aster-canonical-pcm32-20261025/verified.json')
if canonical_file.exists():
    canonical=json.loads(canonical_file.read_text())
    canonical_expected={**{name:'76cc78bb5b1c2901a0ceabd25c337daa51a4f1d04e828f94b8cc74e0f69c58ac'
        for name in ('nav-left.wav','nav-right.wav','nav-up.wav','nav-down.wav')},
        'back.wav':'9966043bb9601362f15e3f11f0272c78bad7f2c7201aee7952200c1c0aaef9a8',
        'select.wav':'19ffc9a9ea3d74e69c9e1b8a5ea3ca10ef8c6af8de47629b919609379226ad3e',
        'notify.wav':'5c9f60ac6e86b93beae0801646b9ba8b342e001a9b5fb47cfde3873786dcba80'}
    _require(canonical.get('kind')=='aster-canonical-ui-sounds.v1' and canonical.get('host')=='AsterTV'
        and canonical.get('assets')==canonical_expected and canonical.get('installed') is True,'canonical-sound-adoption')
    for name,expected_sha in canonical_expected.items():
        path='resource.uisounds.asterhome/resources/'+name
        _require(hashlib.sha256((addons/path).read_bytes()).hexdigest()==expected_sha,'canonical-sound-drift')
        canonical_overrides[path]=expected_sha
    canonical_count=7
scrub_file=Path('/storage/.aster-checkpoints/aster-video-scrub-20261024/active-manifest.json')
scrub_active=scrub_file.exists();prepared_scrub=0
if not scrub_active:scrub_file=Path('/storage/.aster-checkpoints/aster-video-scrub-20261024/prepared-native-manifest.json')
scrub_count=0;scrub_osd_sha=None
if scrub_file.exists():
    import re
    _require(len(sys.argv) in (8,9) and hashlib.sha256(scrub_file.read_bytes()).hexdigest()==sys.argv[7],'scrub-manifest-proof')
    scrub=json.loads(scrub_file.read_text())
    native_scrub=scrub.get('kind')=='hp-video-scrub-native'
    _require(scrub.get('schema')==1 and scrub.get('kind') in ('hp-video-scrub','hp-video-scrub-native')
        and re.fullmatch(r'aster-video-scrub[1-9][0-9]*',scrub.get('stage','')),'scrub-kind')
    _require(scrub.get('before_sha256')=='7fe65ddc4e2e33931a771bd57de349ae7a1d47e4d1983534a83e02a5a6ed03c6','scrub-baseline')
    scrub_members={'default.py','resources/lib/video_scrub.py','overlay/VideoOSD.xml',
        'overlay/custom_1126_videoscrub.xml' if native_scrub else 'resources/skins/Default/1080i/VideoScrub.xml'}
    _require(len(scrub['files'])==4 and {r['path'] for r in scrub['files']}==scrub_members,'scrub-members')
    for row in scrub['files']:
        _require(hashlib.sha256((stage/scrub['stage']/row['path']).read_bytes()).hexdigest()==row['sha256'],'scrub-stage-member')
    _require(hashlib.sha256((stage/scrub['stage']/'manifest.json').read_bytes()).hexdigest()==sys.argv[7],'scrub-stage-manifest')
    if native_scrub:
        native_row=next(r for r in scrub['files'] if r['path']=='overlay/custom_1126_videoscrub.xml')
        _require(hashlib.sha256((addons/'skin.asterhome/1080i/custom_1126_videoscrub.xml').read_bytes()).hexdigest()==native_row['sha256'],'prepared-native-dialog-member')
        prepared_scrub=1
    if scrub_active:
        scrub_osd_sha=next(r['sha256'] for r in scrub['files'] if r['path']=='overlay/VideoOSD.xml')
        scrub_count=2 if native_scrub else 1
if overlay_file.exists():
    overlay=json.loads(overlay_file.read_text())
    _require((overlay['sha256']=='591cc32b4f9c3a621e395df744d3a8c3b5f7d178623ff8094fda072fa79a16d0'), ('native-check-failed'))
    overrides={'skin.asterhome/'+r['path']:r['sha256'] for r in overlay['files'] if r['path'].startswith('1080i/')}
    _require((len(overrides)==4), ('native-check-failed'))
    _require((all(hashlib.sha256((addons/'skin.asterhome'/r['path']).read_bytes()).hexdigest()==
        (books_overrides.get('skin.asterhome/'+r['path'],scrub_osd_sha if scrub_osd_sha and r['path']=='1080i/VideoOSD.xml' else r['sha256'])) for r in overlay['files'])), ('native-check-failed'))
    if scrub_osd_sha:overrides['skin.asterhome/1080i/VideoOSD.xml']=scrub_osd_sha
overlay_count=len(overrides)
overrides.update(canonical_overrides)
overrides.update(books_overrides)
if search_home_sha:overrides['skin.asterhome/1080i/Home.xml']=search_home_sha
integration_file=Path('/storage/.aster-checkpoints/aster-music-integration-20261024/active-manifest.json')
integration_count=0
if integration_file.exists():
    _require(len(sys.argv) in (5,6,7,8,9),'integration-manifest-proof-required')
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
    _require(len(sys.argv) in (6,7,8,9),'rail-manifest-proof-required')
    _require(hashlib.sha256(rail_file.read_bytes()).hexdigest()==sys.argv[5],'rail-manifest-hash')
    rail=json.loads(rail_file.read_text())
    _require(rail.get('schema')==1 and rail.get('kind')=='hp-floating-rail' and rail.get('path')=='1080i/IncludesHub.xml','rail-target')
    _require(hashlib.sha256((addons/'skin.asterhome'/rail['path']).read_bytes()).hexdigest()==rail['sha256'],'rail-member-hash')
    overrides['skin.asterhome/'+rail['path']]=rail['sha256'];rail_count=1
series_file=Path('/storage/.aster-checkpoints/aster-series-integration-20261024/active-manifest.json')
series_count=0
if series_file.exists():
    import re
    _require(len(sys.argv) in (7,8,9) and hashlib.sha256(series_file.read_bytes()).hexdigest()==sys.argv[6],'series-manifest-proof')
    series=json.loads(series_file.read_text())
    _require(series.get('schema')==1 and series.get('kind')=='hp-series-integration','series-kind')
    _require(len(series['files'])==2 and {r['path'] for r in series['files']}=={'tools/select_dispatch.py','tools/aster_v2_series.py'},'series-targets')
    for row in series['files']:
        expected_member=row['sha256']
        if row['path']=='tools/select_dispatch.py' and search_dispatch_sha:
            _require(row['sha256']==search_manifest['dispatcher_before_sha256'],'search-series-predecessor')
            expected_member=search_dispatch_sha
        _require(hashlib.sha256((addons/'skin.asterhome'/row['path']).read_bytes()).hexdigest()==expected_member,'series-member-hash')
        overrides['skin.asterhome/'+row['path']]=expected_member
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
sys.path.insert(0,str(Path(__file__).resolve().parent))
from av_preservation import verify as verify_av
av_details=verify_av(values,json.loads(Path('/storage/.aster-checkpoints/aster-music-expanded-trial-20261023/before-candidate14/av-baseline.json').read_text()),
    rpc('XBMC.GetInfoLabels',{'labels':['System.ScreenWidth','System.ScreenHeight','System.ScreenResolution']}))
connection=sqlite3.connect('file:/storage/.kodi/userdata/Database/MyMusic83.db?mode=ro',uri=True)
try:
    _require((connection.execute('SELECT count(*) FROM song s WHERE NOT EXISTS(SELECT 1 FROM song_artist sa WHERE sa.idSong=s.idSong AND sa.idRole=1)').fetchone()[0]==0), ('native-check-failed'))
    _require((connection.execute('PRAGMA integrity_check').fetchall()==[('ok',)]), ('native-check-failed'))
finally:connection.close()
video=sqlite3.connect('file:/storage/.kodi/userdata/Database/MyVideos131.db?mode=ro',uri=True)
try:_require(video.execute('PRAGMA integrity_check').fetchall()==[('ok',)],'video-database-integrity')
finally:video.close()
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
               'approved_video_scrub_files_verified':scrub_count,
               'prepared_video_scrub_dialog_verified':prepared_scrub,
               'approved_search_details_files_verified':search_count,
               'approved_canonical_sound_files_verified':canonical_count,
               'approved_books_sync_files_verified':books_count,
               'av_language_settings_verified':len(values),
               'av_preservation_details':av_details,
               'database_integrity':'ok','missing_primary_artist_links':0,
               'video_database_integrity':'ok',
               'no_player':True,'original_empty_queue':True,'capability_removed':True,
               'all_lab_windows_closed':True,'approved_normal_playback':normal},handle)
output.chmod(0o600)
