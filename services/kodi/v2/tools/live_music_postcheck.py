"""Read-only in-process HP preservation check after a native Music trial.

RunScript(path,candidate-number,expected-archive-sha256). No queue writes,
credential reads, settings changes or production-host support.
"""


def _require(condition,message="native-check-failed"):
    """Unlike assert, this check remains active in Kodi optimized Python."""
    if not condition:raise AssertionError(message)

import hashlib,json,os,re,sqlite3,sys,time
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
keys.extend('Window(Home).Property(AsterDigest.'+name+')' for name in ('PlayerWindow','PreviewWindow','ReaderWindow'))
keys.append('Window(Home).Property(AsterHome.PreviewWindow)')
keys.append('Window(Home).Property(AsterNetwork.PreviewWindow)')
keys.append('Window(Home).Property(AsterNetwork.MenuOpen)')
keys.append('Window(Home).Property(AsterIdle.Window)')
keys.extend('Window(Home).Property(AsterSearch.'+name+')' for name in ('Open','DetailOpen','Ready'))
keys.append('Window(Home).Property(AsterSearch.Handoff)')
keys.extend('Window(Home).Property(AsterMovie.'+name+')' for name in ('Window','Ready','Phase'))
_require(not Path('/storage/.aster-checkpoints/aster-movie-playback-20261024/unresolved-start.json').exists(),'movie-recovery-required')
_require(not Path('/storage/.aster-checkpoints/aster-global-search-20261024/handoff-pending.json').exists(),'search-handoff-recovery-required')
_require(not Path('/storage/.aster-checkpoints/aster-series-playback-20261024/unresolved-start.json').exists(),'series-recovery-required')
_require(not Path('/storage/.aster-checkpoints/aster-video-scrub-20261024/unresolved-seek.json').exists(),'scrub-recovery-required')
_require((not any(rpc('XBMC.GetInfoLabels',{'labels':keys}).values())), ('live-or-recovery-window-retained'))
stage=Path('/storage/.aster-staging');addons=Path('/storage/.kodi/addons')
idle_pilot_count=0
if Path('/storage/.aster-checkpoints/aster-idle-presentation2/state.json').exists():
    import importlib.util
    idle_stage=stage/'aster-idle-presentation2'
    idle_pin='f6af15135f9321eb7fc602696051a22b4a07ff8a2b057fd2eef359e1c420dc83'
    raw=(idle_stage/'manifest.json').read_bytes()
    _require(hashlib.sha256(raw).hexdigest()==idle_pin,'idle-pilot-manifest-pin')
    for name,digest in json.loads(raw)['helpers'].items():
        _require(hashlib.sha256((idle_stage/name).read_bytes()).hexdigest()==digest,'idle-pilot-helper-pin')
    spec=importlib.util.spec_from_file_location('accepted_idle_pilot',idle_stage/'idle_screensaver_install.py')
    sys.path.insert(0,str(idle_stage));validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)
    _,idle_baseline,idle_state=validator.verify_files(idle_stage,Path('/storage'),idle_pin)
    _require(idle_state in ('registered','disabled'),'idle-pilot-incomplete-registration')
    _require(not (Path('/storage/.aster-checkpoints/aster-idle-presentation2')/'trial-restore-pending.json').exists(),
        'idle-pilot-trial-restoration-required')
    idle_settings={k:rpc('Settings.GetSettingValue',{'setting':k})['value'] for k in idle_baseline['settings']}
    _require(idle_settings==idle_baseline['settings'],'idle-pilot-original-settings')
    inventory={r['addonid']:{'enabled':r['enabled'],'version':r['version']} for r in
        rpc('Addons.GetAddons',{'enabled':'all','properties':['enabled','version']})['addons']}
    _require({k:v for k,v in inventory.items() if k!='screensaver.asterhome.v2lab'}==idle_baseline['inventory'],
        'idle-pilot-other-addons-changed')
    _require(inventory.get('screensaver.asterhome.v2lab')=={'enabled':idle_state=='registered','version':'0.1.0'},
        'idle-pilot-enabled-state')
    connection=sqlite3.connect('file:/storage/.kodi/userdata/Database/Addons33.db?mode=ro',uri=True)
    try:_require(connection.execute('PRAGMA integrity_check').fetchall()==[('ok',)],'addon-database-integrity')
    finally:connection.close()
    idle_pilot_count=7
baseline=json.loads((stage/'aster-artist-repair-v1-baseline-20261023.json').read_text())
rows=[row for archive in baseline['archives'] for row in archive['files']]
_require((len(rows)==153), ('native-check-failed'))
base_paths={row['path'] for row in rows}
search_file=Path('/storage/.aster-checkpoints/aster-global-search-20261024/active-manifest.json')
search_dispatch_sha=None;search_count=0;search_home_sha=None
if search_file.exists():
    _require(len(sys.argv) in (9,10,11) and hashlib.sha256(search_file.read_bytes()).hexdigest()==sys.argv[8],'search-manifest-proof')
    search_manifest=json.loads(search_file.read_text())
    search_linked=search_manifest.get('kind')=='hp-search-playerlinks'
    _require(search_manifest.get('kind') in ('hp-search-details','hp-search-playerlinks')
        and len(search_manifest['files'])==((13 if search_manifest.get('movie_page')==11130 else 10 if search_manifest.get('artist_native_window')==11129 else 9 if search_manifest.get('artist_albums') is True else 8) if search_linked else 6),'search-details-kind')
    _require(search_manifest.get('dispatcher_before_sha256')=='466b69269e56d8699838aabbe72ae533a580909603855850a047bf02e76d1a0e','search-dispatch-predecessor')
    search_stages=[stage/name for name in ('aster-global-search-ui3','aster-global-search-ui4','aster-global-search-ui5','aster-global-search-ui6','aster-global-search-ui7','aster-global-search-ui8','aster-global-search-ui9','aster-global-search-ui10','aster-global-search-ui11','aster-global-search-ui12','aster-global-search-ui13','aster-global-search-ui14','aster-global-search-ui15','aster-global-search-ui16','aster-global-search-ui17','aster-global-search-ui18','aster-global-search-ui19','aster-global-search-ui20','aster-global-search-ui21','aster-global-search-ui22')
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
        'aster-books-sync6':'dd502b6770ec6c0f76e4c2fb4182c54c4b84e4c5162a70e0c0dd2a205a643dd7',
        'aster-books-sync7':'0def99963e27add62f7b13c13568bdfcf8d6ea7669fec9a389e1098797b9269c',
        'aster-books-sync8':'ee8701d57dff69cb9290e246c04ce08cd54a0b9289652fac323b5abe65b24c2d',
        'aster-books-sync9':'7b0a8f7cb34de064970f54857d8c005bcbc7cd1fcf04a04a4f0a06c6a5bb282b',
        'aster-books-sync10':'59eea94d12ddd2e3495a475d71933ba5e1f5a8fd213565c7edc4f50c32058913',
        'aster-books-sync11':'793acb6f1b49cb5e95e81b156939e4c499ed687ae89c9c070cd4f89b9a981d31',
        'aster-books-sync12':'39105d0b69c628c8faffac9dc0ffa2273a98e5a66dfdbe578ebd410f83f81238',
        'aster-books-sync13':'fa1208744f1d12c9915c19f60876dfa47bfd836a7a9f3bc773680bea1db85e8d'}
    books_name=books.get('stage');_require(books_name in accepted_books and hashlib.sha256(books_file.read_bytes()).hexdigest()==accepted_books[books_name],'books-sync-manifest')
    expected_books_count=13 if books_name in ('aster-books-sync6','aster-books-sync7','aster-books-sync8','aster-books-sync9','aster-books-sync10','aster-books-sync11','aster-books-sync12','aster-books-sync13') else 9
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
    effective_sounds=canonical_expected
    balanced_file=Path('/storage/.aster-checkpoints/aster-balanced-clicks-20261025/verified.json')
    if balanced_file.exists():
        balanced=json.loads(balanced_file.read_text())
        effective_sounds=dict(zip(('back.wav','nav-down.wav','nav-left.wav','nav-right.wav','nav-up.wav','notify.wav','select.wav'),(
            '6c2edc8e86279053e99e49cfac37649aee1e3250049f9beff279d6b74dc65026',
            'f458261b3e8dfbc3521e642fda5f9f175af6ccb7c335e7bf9ad88fede474cd89',
            'f22d1b475eb698dff16dcd7a03110203aa739248d6daddc6ab3f8bcf32a7723e',
            'b75da71b1a94b42fabdd34b5082840890d0950886534b0c2731221edae345a08',
            '3e0118c141031dd4ca2b6628d1fdcef0359749b8daba293d5e2733fc35ed33f7',
            'deff80a6905c64329c3d2813cf228fac73308bfa9cd70c87f879f063caa239b9',
            '0bd67a6b86e0c18c5451a7ad5effcee5d9bd6906a3908195a84e333bd7cceab4')))
        _require(balanced.get('host')=='AsterTV' and balanced.get('assets')==effective_sounds and balanced.get('installed') is True
            and balanced.get('settings_unchanged') is True and balanced.get('transform',{}).get('left_gain')==0.6227221498528474,'balanced-sound-adoption')
        for n,d in canonical_expected.items():
            _require(hashlib.sha256((balanced_file.parent/n).read_bytes()).hexdigest()==d,'balanced-sound-recovery')
    for name,expected_sha in effective_sounds.items():
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
    _require(len(sys.argv) in (8,9,10,11) and hashlib.sha256(scrub_file.read_bytes()).hexdigest()==sys.argv[7],'scrub-manifest-proof')
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
review10_expected={}
reading_news_count=0
if Path('/storage/.aster-checkpoints/aster-digest-read-news1/state.json').exists():
    import importlib.util
    _require(len(sys.argv)==11 and re.fullmatch('[0-9a-f]{64}',sys.argv[10]),'reading-news-proof-required')
    reading_stage=stage/'aster-digest-read-news1'
    reading_raw=(reading_stage/'manifest.json').read_bytes()
    _require(hashlib.sha256(reading_raw).hexdigest()==sys.argv[10],'reading-news-manifest-pin')
    reading_manifest=json.loads(reading_raw)
    for name,digest in reading_manifest['helpers'].items():
        _require(hashlib.sha256((reading_stage/name).read_bytes()).hexdigest()==digest,'reading-news-helper-pin')
    spec=importlib.util.spec_from_file_location('accepted_reading_news',reading_stage/'digest_read_news_install.py')
    sys.path.insert(0,str(reading_stage))
    validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)
    reading_overrides=validator.accepted_overrides(reading_stage,Path('/storage'),sys.argv[10])
    _require(not reading_overrides or set(reading_overrides)=={'.kodi/addons/skin.asterhome/1080i/custom_1111_digest.xml'},'reading-news-exact-target')
    review10_expected.update(reading_overrides);reading_news_count=len(reading_overrides)
review10_marker=Path('/storage/.aster-checkpoints/aster-review10-20261025/installed.json')
if review10_marker.exists():
    review10_sha='3b2662f81d0b7202dda23b93c7ff50fbec6a8dbcb4d6a1e3c4106a7bbf8f595a'
    review10_raw=(stage/'aster-review10/manifest.json').read_bytes()
    _require(hashlib.sha256(review10_raw).hexdigest()==review10_sha,'review10-manifest')
    _require(json.loads(review10_marker.read_text()).get('manifest_sha256')==review10_sha,'review10-installation')
    settings_repair=Path('/storage/.aster-checkpoints/aster-branding-settings-repair-20261025/verified.json')
    if settings_repair.exists():
        repair=json.loads(settings_repair.read_text());digest='c587268c5c972f15f4d1f169db90f3aea48428010fc93d3e68ac0c1f81f4234a'
        _require(repair.get('passed') is True and repair.get('sha256')==digest and repair.get('member')=='Settings.xml','settings-caption-repair')
        review10_expected['.kodi/addons/skin.asterhome/1080i/Settings.xml']=digest
    disabled_repair=Path('/storage/.aster-checkpoints/aster-branding-settings-disabled-20261025/verified.json')
    if disabled_repair.exists():
        repair=json.loads(disabled_repair.read_text());digest='09a98be3b9ecddf185f61fdfb561bf9e68c4be123816e4f78ecc34210e136ab4'
        _require(repair.get('passed') is True and repair.get('sha256')==digest and repair.get('member')=='Settings.xml','settings-disabled-captions')
        review10_expected['.kodi/addons/skin.asterhome/1080i/Settings.xml']=digest
    if Path('/storage/.aster-checkpoints/aster-network-settings3/state.json').exists():
        import importlib.util
        network_settings_stage=stage/'aster-network-settings3'
        network_settings_pin='10a4d833a12b30995f963d95859943085a2492e9bad148f5496420a95343a3f8'
        raw=(network_settings_stage/'manifest.json').read_bytes()
        _require(hashlib.sha256(raw).hexdigest()==network_settings_pin,'network-settings-manifest-pin')
        for name,digest in json.loads(raw)['helpers'].items():
            _require(hashlib.sha256((network_settings_stage/name).read_bytes()).hexdigest()==digest,'network-settings-helper-pin')
        spec=importlib.util.spec_from_file_location('accepted_network_settings',network_settings_stage/'network_settings_install.py')
        sys.path.insert(0,str(network_settings_stage))
        validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)
        overrides=validator.accepted_overrides(network_settings_stage,Path('/storage'),network_settings_pin)
        _require(not overrides or set(overrides)=={'.kodi/addons/skin.asterhome/1080i/Settings.xml'},'network-settings-exact-overlay')
        review10_expected.update(overrides)
    for r in json.loads(review10_raw)['files']:
        review10_member_sha=review10_expected.get(r['path'],r['sha256'])
        _require(hashlib.sha256((Path('/storage')/r['path']).read_bytes()).hexdigest()==review10_member_sha,'review10-installed-member')
        review10_expected[r['path']]=review10_member_sha
review9_expected={}
review9_marker=Path('/storage/.aster-checkpoints/aster-review9-20261025/installed.json')
if review9_marker.exists():
    review9_sha='70c5661d2305e332655ef10ebf19cce883c4d221c60001b54ff19b2d0c34ae78'
    review9_raw=(stage/'aster-review9/manifest.json').read_bytes()
    _require(hashlib.sha256(review9_raw).hexdigest()==review9_sha,'review9-manifest')
    _require(json.loads(review9_marker.read_text()).get('manifest_sha256')==review9_sha,'review9-installation')
    for r in json.loads(review9_raw)['files']:
        _require(hashlib.sha256((Path('/storage')/r['path']).read_bytes()).hexdigest()==review10_expected.get(r['path'],r['sha256']),'review9-installed-member')
        review9_expected[r['path']]=review10_expected.get(r['path'],r['sha256'])
    repair=Path('/storage/.aster-checkpoints/aster-branding-search-repair-20261025/verified.json')
    if repair.exists():
        proof=json.loads(repair.read_text());digest='6f1fbe60d9d1ef9187ad0524602268145c9412c5d2c886c104243103b692e55e'
        _require(proof.get('passed') is True and proof.get('sha256')==digest,'review9-search-repair-proof')
        n='.kodi/addons/skin.asterhome/1080i/custom_1127_search.xml'
        _require(hashlib.sha256((Path('/storage')/n).read_bytes()).hexdigest()==digest,'review9-search-repair-member')
        review9_expected[n]=digest
review9_expected.update(review10_expected)
review8_expected={}
review8_marker=Path('/storage/.aster-checkpoints/aster-review8-20261025/installed.json')
if review8_marker.exists():
    review8_sha='1593f1f8982be294c19ec0ad3d51b7879428abc08a1fb6a6f78a5818f230155d'
    review8_raw=(stage/'aster-review8/manifest.json').read_bytes()
    _require(hashlib.sha256(review8_raw).hexdigest()==review8_sha,'review8-manifest')
    _require(json.loads(review8_marker.read_text()).get('manifest_sha256')==review8_sha,'review8-installation')
    for r in json.loads(review8_raw)['files']:
        _require(hashlib.sha256((Path('/storage')/r['path']).read_bytes()).hexdigest()==review9_expected.get(r['path'],r['sha256']),'review8-installed-member')
        review8_expected[r['path']]=review9_expected.get(r['path'],r['sha256'])
review8_expected.update(review9_expected)
review7_expected={}
review7_marker=Path('/storage/.aster-checkpoints/aster-review7-20261025/installed.json')
if review7_marker.exists():
    review7_sha='0e08428ee0342a4e6d957352b4936681803243c556fe4fbdc43839983462a6a3'
    review7_raw=(stage/'aster-review7/manifest.json').read_bytes()
    _require(hashlib.sha256(review7_raw).hexdigest()==review7_sha,'review7-manifest')
    _require(json.loads(review7_marker.read_text()).get('manifest_sha256')==review7_sha,'review7-installation')
    for r in json.loads(review7_raw)['files']:
        _require(hashlib.sha256((Path('/storage')/r['path']).read_bytes()).hexdigest()==review8_expected.get(r['path'],r['sha256']),'review7-installed-member')
        review7_expected[r['path']]=review8_expected.get(r['path'],r['sha256'])
review7_expected.update(review8_expected)
review6_expected={}
review6_marker=Path('/storage/.aster-checkpoints/aster-review6-20261025/installed.json')
if review6_marker.exists():
    review6_sha='abcdf6a8deb7d8907ec34745877d05fcaeebce47c1a7a78e3628558765731472'
    review6_raw=(stage/'aster-review6/manifest.json').read_bytes()
    _require(hashlib.sha256(review6_raw).hexdigest()==review6_sha,'review6-manifest')
    _require(json.loads(review6_marker.read_text()).get('manifest_sha256')==review6_sha,'review6-installation')
    for r in json.loads(review6_raw)['files']:
        _require(hashlib.sha256((Path('/storage')/r['path']).read_bytes()).hexdigest()==review7_expected.get(r['path'],r['sha256']),'review6-installed-member')
        review6_expected[r['path']]=review7_expected.get(r['path'],r['sha256'])
review6_expected.update(review7_expected)
review5_expected={}
review5_marker=Path('/storage/.aster-checkpoints/aster-review5-20261025/installed.json')
if review5_marker.exists():
    review5_sha='76e97d657eb6a1ef07d61e2f0f7cbe907fe8ec705631d314e906126d2c3d4966'
    review5_raw=(stage/'aster-review5/manifest.json').read_bytes()
    _require(hashlib.sha256(review5_raw).hexdigest()==review5_sha,'review5-manifest')
    _require(json.loads(review5_marker.read_text()).get('manifest_sha256')==review5_sha,'review5-installation')
    for r in json.loads(review5_raw)['files']:
        _require(hashlib.sha256((Path('/storage')/r['path']).read_bytes()).hexdigest()==review6_expected.get(r['path'],r['sha256']),'review5-installed-member')
        review5_expected[r['path']]=review6_expected.get(r['path'],r['sha256'])
review5_expected.update(review6_expected)
review4_expected={}
review4_marker=Path('/storage/.aster-checkpoints/aster-review4-20261025/installed.json')
if review4_marker.exists():
    review4_sha='0f3bffbaf0a23749bf014726fc854b8cbd7ce4d7e76bea9d23392e593a394e6a'
    review4_raw=(stage/'aster-review4/manifest.json').read_bytes()
    _require(hashlib.sha256(review4_raw).hexdigest()==review4_sha,'review4-manifest')
    _require(json.loads(review4_marker.read_text()).get('manifest_sha256')==review4_sha,'review4-installation')
    for r in json.loads(review4_raw)['files']:
        _require(hashlib.sha256((Path('/storage')/r['path']).read_bytes()).hexdigest()==review5_expected.get(r['path'],r['sha256']),'review4-installed-member')
        review4_expected[r['path']]=review5_expected.get(r['path'],r['sha256'])
review4_expected.update(review5_expected)
review3_expected={}
review3_marker=Path('/storage/.aster-checkpoints/aster-review3-20261025/installed.json')
if review3_marker.exists():
    review3_sha='7c8809174b1123765822ada12ea4a28bb534703a4baed5cb21a1c30236c2ea11'
    review3_raw=(stage/'aster-review3/manifest.json').read_bytes()
    _require(hashlib.sha256(review3_raw).hexdigest()==review3_sha,'review3-manifest')
    _require(json.loads(review3_marker.read_text()).get('manifest_sha256')==review3_sha,'review3-installation')
    for r in json.loads(review3_raw)['files']:
        _require(hashlib.sha256((Path('/storage')/r['path']).read_bytes()).hexdigest()==review4_expected.get(r['path'],r['sha256']),'review3-installed-member')
        review3_expected[r['path']]=review4_expected.get(r['path'],r['sha256'])
review3_expected.update(review4_expected)
if overlay_file.exists():
    overlay=json.loads(overlay_file.read_text())
    _require((overlay['sha256']=='591cc32b4f9c3a621e395df744d3a8c3b5f7d178623ff8094fda072fa79a16d0'), ('native-check-failed'))
    overrides={'skin.asterhome/'+r['path']:r['sha256'] for r in overlay['files'] if r['path'].startswith('1080i/')}
    _require((len(overrides)==4), ('native-check-failed'))
    _require((all(hashlib.sha256((addons/'skin.asterhome'/r['path']).read_bytes()).hexdigest()==
        review3_expected.get('.kodi/addons/skin.asterhome/'+r['path'],books_overrides.get('skin.asterhome/'+r['path'],scrub_osd_sha if scrub_osd_sha and r['path']=='1080i/VideoOSD.xml' else r['sha256'])) for r in overlay['files'])), ('native-check-failed'))
    if scrub_osd_sha:overrides['skin.asterhome/1080i/VideoOSD.xml']=scrub_osd_sha
overlay_count=len(overrides)
overrides.update(canonical_overrides)
overrides.update(books_overrides)
# The second visual-review bundle intentionally changes keyboard and button
# surfaces outside the older four-player overlay. Verify the entire exact
# checkpoint before accepting any of its source overrides.
review_marker=Path('/storage/.aster-checkpoints/aster-review2-20261025/installed.json')
if review_marker.exists():
    review_sha='e82560124c0d61fb997edac12e158bed3fba95c5d3d5cf4e476909e5bd57929f'
    review_root=stage/'aster-review2';review_raw=(review_root/'manifest.json').read_bytes()
    _require(hashlib.sha256(review_raw).hexdigest()==review_sha,'review2-manifest')
    _require(json.loads(review_marker.read_text()).get('manifest_sha256')==review_sha,'review2-installation')
    review=json.loads(review_raw)
    for r in review['files']:
        _require(hashlib.sha256((Path('/storage')/r['path']).read_bytes()).hexdigest()==review3_expected.get(r['path'],r['sha256']),'review2-installed-member')
        if r['path'].startswith('.kodi/addons/'):
            overrides[r['path'][len('.kodi/addons/'):]]=r['sha256']
overrides.update({n[len('.kodi/addons/'):]:d for n,d in review3_expected.items() if n.startswith('.kodi/addons/')})
if search_home_sha:overrides['skin.asterhome/1080i/Home.xml']=search_home_sha
integration_file=Path('/storage/.aster-checkpoints/aster-music-integration-20261024/active-manifest.json')
integration_count=0
if integration_file.exists():
    _require(len(sys.argv) in (5,6,7,8,9,10,11),'integration-manifest-proof-required')
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
    _require(len(sys.argv) in (6,7,8,9,10,11),'rail-manifest-proof-required')
    _require(hashlib.sha256(rail_file.read_bytes()).hexdigest()==sys.argv[5],'rail-manifest-hash')
    rail=json.loads(rail_file.read_text())
    _require(rail.get('schema')==1 and rail.get('kind')=='hp-floating-rail' and rail.get('path')=='1080i/IncludesHub.xml','rail-target')
    _require(hashlib.sha256((addons/'skin.asterhome'/rail['path']).read_bytes()).hexdigest()==rail['sha256'],'rail-member-hash')
    overrides['skin.asterhome/'+rail['path']]=rail['sha256'];rail_count=1
series_file=Path('/storage/.aster-checkpoints/aster-series-integration-20261024/active-manifest.json')
series_count=0
if series_file.exists():
    import re
    _require(len(sys.argv) in (7,8,9,10,11) and hashlib.sha256(series_file.read_bytes()).hexdigest()==sys.argv[6],'series-manifest-proof')
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
digest_news_count=0
digest_state=Path('/storage/.aster-checkpoints/aster-digest-news1/state.json')
if digest_state.exists():
    # Exact successor, not a skipped baseline member: external manifest pin,
    # known two targets, exact predecessor/private backup, full player payload.
    import importlib.util
    _require(len(sys.argv) in (10,11) and re.fullmatch('[0-9a-f]{64}',sys.argv[9]),'digest-news-proof-required')
    digest_stage=stage/'aster-digest-news1'
    digest_raw=(digest_stage/'manifest.json').read_bytes()
    _require(hashlib.sha256(digest_raw).hexdigest()==sys.argv[9],'digest-news-manifest-pin')
    digest_manifest=json.loads(digest_raw)
    helper=digest_stage/'digest_news_install.py'
    _require(hashlib.sha256(helper.read_bytes()).hexdigest()==digest_manifest['helpers']['digest_news_install.py'],'digest-news-validator-pin')
    spec=importlib.util.spec_from_file_location('accepted_digest_news',helper)
    validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)
    digest_overrides=validator.accepted_overrides(digest_stage,Path('/storage'),sys.argv[9])
    _require(not digest_overrides or set(digest_overrides)=={'skin.asterhome/tools/hub_data.py','skin.asterhome/tools/aster_v2_digest.py'},'digest-news-exact-targets')
    overrides.update(digest_overrides);digest_news_count=len(digest_overrides)
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
               'approved_digest_news_files_verified':digest_news_count,
               'approved_reading_news_files_verified':reading_news_count,
               'approved_idle_pilot_files_verified':idle_pilot_count,
               'av_language_settings_verified':len(values),
               'av_preservation_details':av_details,
               'database_integrity':'ok','missing_primary_artist_links':0,
               'video_database_integrity':'ok',
               'no_player':True,'original_empty_queue':True,'capability_removed':True,
               'all_lab_windows_closed':True,'approved_normal_playback':normal},handle)
output.chmod(0o600)
