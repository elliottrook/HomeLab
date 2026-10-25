"""Exact-predecessor HP review bundle. Frozen v1 source remains unchanged."""
import argparse,hashlib,json,zipfile
from pathlib import Path
from build_lab import build as build_music
from build_series_preview import build as build_series
from review2_ui import quiet_buttons,search_focus,header,osd,keyboard,select_dialog
HERE=Path(__file__).resolve().parent
SKIN='.kodi/addons/skin.asterhome/'
PINS={'music-before.json':'bc1346a117b0356bdb343b1cbab1389c6af89df39c80082c3eef445b4904d915',
 'music-integration-before.json':'b5d5d866ee442b5fc38cccd51bc35bc6f753a450759082f03baaed12d3efc272',
 'series-integration-before.json':'a58433fe44d3317290753669d7ef87ac0fc846c02eda00b686fc91c43a9e88b6',
 'search-before.json':'732a89c3e3e9189022a1ee7c4fdb9f596c88486d2f13fb53d3832d47c7a46df4',
 'scrub-before.json':'def904ac4d6600fbbefb61d7d5dd450cd026853f820356185919d4e485097bfa'}
def sha(data):return hashlib.sha256(data).hexdigest()
def raw(value):return (json.dumps(value,indent=2)+'\n').encode()
def records(files):return [dict(path=n,bytes=len(d),sha256=sha(d)) for n,d in sorted(files.items())]

def build(snapshot,output):
    snapshot,output=Path(snapshot),Path(output)
    if output.exists():raise ValueError('immutable-review2')
    prior={}
    for name,digest in PINS.items():
        data=(snapshot/name).read_bytes()
        if sha(data)!=digest:raise ValueError('review-predecessor:'+name)
        prior[name]=json.loads(data)
    payload={};before={}
    def put(name,data,old=None):
        if name in payload and payload[name]!=data:raise ValueError('overlapping-review-target:'+name)
        payload[name]=data;before[name]=old
    def stage(name,files,manifest):
        manifest=dict(manifest,files=records(files));data=raw(manifest)
        for n,d in files.items():put('.aster-staging/'+name+'/'+n,d)
        put('.aster-staging/'+name+'/manifest.json',data)
        return data
    def skin(n,d):
        source=snapshot/'skin-before'/Path(n).name if n.startswith('1080i/') else snapshot/(Path(n).stem+'-before.py')
        put(SKIN+n,d,sha(source.read_bytes()))
    def active(folder,filename,data,old):put('.aster-checkpoints/'+folder+'/'+filename,data,old)
    output.mkdir();work=output/'build';work.mkdir()
    music=build_music(work/'music66');music_raw=(work/'music66/manifest.json').read_bytes()
    old_music={r['path']:r['sha256'] for r in prior['music-before.json']['files']}
    with zipfile.ZipFile(work/'music66'/music['archive']) as archive:
        for n in archive.namelist():put('.kodi/addons/'+n,archive.read(n),old_music[n])
    put('.aster-staging/aster-music-v2lab-0.1.0-candidate66/manifest.json',music_raw)
    put('.aster-staging/aster-music-v2lab-0.1.0-candidate66/'+music['archive'],(work/'music66'/music['archive']).read_bytes())
    series_sha=build_series(work/'series18');series=json.loads((work/'series18/manifest.json').read_text())
    stage('aster-series-preview18',{r['path']:(work/'series18'/r['path']).read_bytes() for r in series['files']},series)
    # Shared texture-only changes; never modify the accepted side rail.
    changed={}
    for path in sorted((snapshot/'skin-before').glob('*.xml')):
        if path.name in ('IncludesHub.xml','Home.xml','VideoOSD.xml'):continue
        data=path.read_bytes()
        if b'limestone' in data and b'texturenofocus' in data:changed['1080i/'+path.name]=quiet_buttons(data)
    changed['1080i/DialogKeyboard.xml']=keyboard((snapshot/'skin-before/DialogKeyboard.xml').read_bytes())
    changed['1080i/DialogSelect.xml']=select_dialog((snapshot/'skin-before/DialogSelect.xml').read_bytes())
    integration=prior['music-integration-before.json'];integration_rows=[]
    for row in integration['files']:
        name=row['path'];source=snapshot/'skin-before'/Path(name).name if name.startswith('1080i/') else snapshot/(Path(name).stem+'-before.py')
        old=source.read_bytes()
        if sha(old)!=row['sha256']:raise ValueError('music-integration-drift:'+name)
        data=changed.get(name,old);skin(name,data)
        integration_rows.append(dict(row,before_sha256=row['sha256'],bytes=len(data),sha256=sha(data)))
    integration_raw=raw(dict(integration,files=integration_rows,player_sha_at_deploy=music['sha256'],
        previous_manifest_sha256=PINS['music-integration-before.json']))
    active('aster-music-integration-20261024','active-manifest.json',integration_raw,PINS['music-integration-before.json'])
    for name,data in changed.items():
        if SKIN+name not in payload:skin(name,data)
    # Update the route and its integrity record together.
    route=(snapshot/'aster_v2_series-before.py').read_bytes().replace(b'aster-series-preview17',b'aster-series-preview18').replace(
        prior['series-integration-before.json']['series_manifest_sha256'].encode(),series_sha.encode())
    skin('tools/aster_v2_series.py',route)
    series_integration=dict(prior['series-integration-before.json'],series_stage='aster-series-preview18',series_manifest_sha256=series_sha)
    for row in series_integration['files']:
        if row['path']=='tools/aster_v2_series.py':row.update(bytes=len(route),sha256=sha(route))
    # Search dispatcher stays unchanged; all new direct links use the same owner checks.
    search_old=prior['search-before.json'];search_root=snapshot/'aster-global-search-ui14'
    search_files={r['path']:(search_root/r['path']).read_bytes() for r in search_old['files']}
    if any(sha(search_files[r['path']])!=r['sha256'] for r in search_old['files']):raise ValueError('search-member-drift')
    search_files['default.py']=(HERE/'search_native/default.py').read_bytes()
    search_files['overlay/Home.xml']=quiet_buttons(header(search_files['overlay/Home.xml'].replace(b'aster-global-search-ui14/',b'aster-global-search-ui15/')))
    for name in ('custom_1127_search.xml','custom_1129_artistalbums.xml'):
        search_files['overlay/'+name]=search_focus(search_files['overlay/'+name])
    search_files['resources/lib/search_handoff.py']=search_files['resources/lib/search_handoff.py'].replace(
        b'aster-series-preview17',b'aster-series-preview18').replace(b'aster-music-v2lab-0.1.0-candidate65',b'aster-music-v2lab-0.1.0-candidate66').replace(
        prior['series-integration-before.json']['series_manifest_sha256'].encode(),series_sha.encode()).replace(PINS['music-before.json'].encode(),sha(music_raw).encode())
    search_files['resources/lib/movie_player.py']=search_files['resources/lib/movie_player.py'].replace(
        b"MOVIE_STAGE='aster-global-search-ui14'",b"MOVIE_STAGE='aster-global-search-ui15'").replace(
        search_old['previous_manifest_sha256'].encode(),PINS['search-before.json'].encode())
    search_raw=stage('aster-global-search-ui15',search_files,dict(search_old,stage='aster-global-search-ui15',previous_manifest_sha256=PINS['search-before.json']))
    from movie_player import TARGETS
    for source,target in TARGETS.items():
        if SKIN+target in payload:
            # Home is not previously emitted by the quiet texture transform.
            raise ValueError('search-skin-overlap:'+target)
        skin(target,search_files[source]) if target.startswith('1080i/') else put(SKIN+target,search_files[source],next(r['sha256'] for r in search_old['files'] if r['path']==source))
    # Keep the dispatcher predecessor in the series record: Search owns the
    # composed dispatcher and verifies this exact predecessor independently.
    active('aster-series-integration-20261024','active-manifest.json',raw(series_integration),PINS['series-integration-before.json'])
    active('aster-global-search-20261024','active-manifest.json',search_raw,PINS['search-before.json'])
    scrub_old=prior['scrub-before.json'];scrub_root=snapshot/'aster-video-scrub4'
    scrub_files={r['path']:(scrub_root/r['path']).read_bytes() for r in scrub_old['files']}
    if any(sha(scrub_files[r['path']])!=r['sha256'] for r in scrub_old['files']):raise ValueError('scrub-member-drift')
    scrub_files['overlay/VideoOSD.xml']=osd(scrub_files['overlay/VideoOSD.xml'].replace(b'aster-video-scrub4/',b'aster-video-scrub5/'))
    scrub_raw=stage('aster-video-scrub5',scrub_files,dict(scrub_old,stage='aster-video-scrub5'))
    for name in ('VideoOSD.xml','custom_1126_videoscrub.xml'):skin('1080i/'+name,scrub_files['overlay/'+name])
    for name in ('active-manifest.json','prepared-native-manifest.json'):active('aster-video-scrub-20261024',name,scrub_raw,PINS['scrub-before.json'])
    for name in ('compact_menu.py','osd_choices.py'):put(SKIN+'tools/'+name,(HERE/name).read_bytes())
    put(SKIN+'resources/skins/Default/1080i/CompactMenu.xml',(HERE/'compact_menu/CompactMenu.xml').read_bytes())
    rows=[]
    for name,data in sorted(payload.items()):
        path=output/'payload'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        rows.append(dict(path=name,sha256=sha(data),before_sha256=before[name]))
    manifest=dict(kind='hp-review2',name='aster-review2',files=rows,music_archive=music['sha256'],music_manifest=sha(music_raw),
        music_integration=sha(integration_raw),series=series_sha,series_integration=sha(raw(series_integration)),search=sha(search_raw),scrub=sha(scrub_raw))
    (output/'manifest.json').write_bytes(raw(manifest));return sha(raw(manifest))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--snapshot',required=True);p.add_argument('--output',required=True)
    args=p.parse_args();print(build(args.snapshot,args.output))
