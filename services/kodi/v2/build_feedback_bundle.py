"""Compose immutable HP successors and an exact-file, recoverable activation plan."""
import argparse,hashlib,json,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
from build_lab import build as music_build
from build_series_preview import build as series_build
from build_music_integration import build as integration_build
from build_series_integration import build as series_integration_build
from floating_rail import build as rail_build
from feedback_refinements import media_header,video_osd,search_hero

HERE=Path(__file__).resolve().parent
def sha(data):return hashlib.sha256(data).hexdigest()
def raw_json(value):return (json.dumps(value,indent=2)+'\n').encode()
def rows(files):return [dict(path=p,bytes=len(v),sha256=sha(v)) for p,v in sorted(files.items())]
def build(snapshot,output):
    snapshot,output=Path(snapshot),Path(output)
    if output.exists():raise ValueError('immutable-feedback-bundle')
    output.mkdir();work=output/'build';work.mkdir()
    old_music=json.loads((snapshot/'music-before.json').read_text())
    old_integration=json.loads((snapshot/'music-integration-before.json').read_text())
    old_rail=json.loads((snapshot/'rail-before.json').read_text())
    old_series=json.loads((snapshot/'series-integration-before.json').read_text())
    search_before=(snapshot/'aster-global-search-ui12/manifest.json').read_bytes()
    search_old=json.loads(search_before)
    scrub_before=(snapshot/'aster-video-scrub3/manifest.json').read_bytes();scrub_old=json.loads(scrub_before)
    # Assert this exact accepted composition, not an arbitrary remote snapshot.
    expected={'music-before.json':'0c19d992a337bee55ec449423b16576962e7721e573a60a640e448d3fb220334',
        'music-integration-before.json':'9f79b4275612fc02192b9abeea0703aaaf3fc745076134f1f50c0784235a51ba',
        'rail-before.json':'c6a782daec7d665abe68968c3f90ff55c98f0540953ffdda73eb41ab24cd364c',
        'series-integration-before.json':'659d6631fbf660aa549f8aa1e123178173d559d58e8f668a50b311566e10d48b'}
    for name,digest in expected.items():
        if sha((snapshot/name).read_bytes())!=digest:raise ValueError('snapshot-drift:'+name)
    if sha(search_before)!='df09e4c45a9e67a18fdb0dc7fe5703766cec55e2674175dfb13727c185dca1a3':raise ValueError('search-predecessor')
    if sha(scrub_before)!='74624ebe0def3bd38f2183a6658afa363146b64cfc73c5e0a6f3cf318f8fde02':raise ValueError('scrub-predecessor')
    payload={};before={}
    def put(path,data):payload[path]=data
    def stage(name,files,manifest):
        manifest['files']=rows(files);raw=raw_json(manifest)
        for path,data in files.items():put('.aster-staging/'+name+'/'+path,data)
        put('.aster-staging/'+name+'/manifest.json',raw)
        return raw
    music=music_build(work/'music65')
    with zipfile.ZipFile(work/'music65'/music['archive']) as archive:
        music_files={name:archive.read(name) for name in archive.namelist()}
    for name,data in music_files.items():put('.kodi/addons/'+name,data)
    for row in old_music['files']:before['.kodi/addons/'+row['path']]=row['sha256']
    music_raw=(work/'music65/manifest.json').read_bytes()
    put('.aster-staging/aster-music-v2lab-0.1.0-candidate65/manifest.json',music_raw)
    put('.aster-staging/aster-music-v2lab-0.1.0-candidate65/'+music['archive'],(work/'music65'/music['archive']).read_bytes())
    series_sha=series_build(work/'series17')
    series_manifest=json.loads((work/'series17/manifest.json').read_text())
    stage('aster-series-preview17',{r['path']:(work/'series17'/r['path']).read_bytes() for r in series_manifest['files']},series_manifest)
    integration_sha=integration_build(work/'integration7',music['sha256'],snapshot/'music-integration-before.json')
    integration=json.loads((work/'integration7/manifest.json').read_text())
    for row in integration['files']:
        put('.kodi/addons/skin.asterhome/'+row['path'],(work/'integration7/files'/row['path']).read_bytes())
    for row in old_integration['files']:before['.kodi/addons/skin.asterhome/'+row['path']]=row['sha256']
    series_integration_sha=series_integration_build(work/'series-integration7','aster-series-preview17',series_sha)
    series_integration=json.loads((work/'series-integration7/manifest.json').read_text())
    for row in series_integration['files']:
        put('.kodi/addons/skin.asterhome/'+row['path'],(work/'series-integration7/files'/row['path']).read_bytes())
    for row in old_series['files']:before['.kodi/addons/skin.asterhome/'+row['path']]=row['sha256']
    rail_sha=rail_build(work/'rail4',snapshot/'rail-before.json')
    put('.kodi/addons/skin.asterhome/1080i/IncludesHub.xml',(work/'rail4/IncludesHub.xml').read_bytes())
    before['.kodi/addons/skin.asterhome/1080i/IncludesHub.xml']=old_rail['sha256']
    scrub_files={r['path']:(snapshot/'aster-video-scrub3'/r['path']).read_bytes() for r in scrub_old['files']}
    for row in scrub_old['files']:
        if sha(scrub_files[row['path']])!=row['sha256']:raise ValueError('scrub-member-drift')
    scrub_files['overlay/VideoOSD.xml']=video_osd(scrub_files['overlay/VideoOSD.xml'].replace(b'aster-video-scrub3/',b'aster-video-scrub4/'))
    root=ET.fromstring(scrub_files['overlay/custom_1126_videoscrub.xml'])
    root.find('.//control/texture').set('colordiffuse','7a000000')
    scrub_files['overlay/custom_1126_videoscrub.xml']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    scrub=dict(scrub_old,stage='aster-video-scrub4')
    scrub_raw=stage('aster-video-scrub4',scrub_files,scrub)
    for name in ('VideoOSD.xml','custom_1126_videoscrub.xml'):
        put('.kodi/addons/skin.asterhome/1080i/'+name,scrub_files['overlay/'+name])
        before['.kodi/addons/skin.asterhome/1080i/'+name]=next(r['sha256'] for r in scrub_old['files'] if r['path']=='overlay/'+name)
    files={r['path']:(snapshot/'aster-global-search-ui12'/r['path']).read_bytes() for r in search_old['files']}
    for row in search_old['files']:
        if sha(files[row['path']])!=row['sha256']:raise ValueError('search-member-drift')
    files['default.py']=(HERE/'search_native/default.py').read_bytes()
    files['resources/lib/search_details.py']=(HERE/'search_details.py').read_bytes()
    files['resources/lib/search_handoff.py']=(HERE/'search_handoff.py').read_bytes().replace(
        b'aster-series-preview16',b'aster-series-preview17').replace(b'aster-music-v2lab-0.1.0-candidate64',b'aster-music-v2lab-0.1.0-candidate65').replace(
        b'4c090e0b3a66b7b56679a07569453d668c372727eeb458f91d97d27ab772796d',series_sha.encode()).replace(
        b'0c19d992a337bee55ec449423b16576962e7721e573a60a640e448d3fb220334',sha(music_raw).encode())
    files['resources/lib/movie_player.py']=files['resources/lib/movie_player.py'].replace(b'aster-global-search-ui12',b'aster-global-search-ui13').replace(
        b'01e499b94aa5f819900fa311515a95a58ead1207f9e3e272fb287590d63b282e',sha(search_before).encode())
    files['overlay/Home.xml']=media_header(files['overlay/Home.xml'].replace(b'aster-global-search-ui12/',b'aster-global-search-ui13/'))
    files['overlay/custom_1128_searchdetails.xml']=search_hero(files['overlay/custom_1128_searchdetails.xml'])
    search=dict(search_old,stage='aster-global-search-ui13',previous_manifest_sha256=sha(search_before))
    search_raw=stage('aster-global-search-ui13',files,search)
    from movie_player import TARGETS
    for source,target in TARGETS.items():
        put('.kodi/addons/skin.asterhome/'+target,files[source])
        before['.kodi/addons/skin.asterhome/'+target]=next(r['sha256'] for r in search_old['files'] if r['path']==source)
    active={
        'aster-music-integration-20261024':((snapshot/'music-integration-before.json').read_bytes(),(work/'integration7/manifest.json').read_bytes()),
        'aster-series-integration-20261024':((snapshot/'series-integration-before.json').read_bytes(),(work/'series-integration7/manifest.json').read_bytes()),
        'aster-floating-rail-20261024':((snapshot/'rail-before.json').read_bytes(),(work/'rail4/manifest.json').read_bytes()),
        'aster-global-search-20261024':(search_before,search_raw),
        'aster-video-scrub-20261024':(scrub_before,scrub_raw)}
    for name,(old,new) in active.items():
        path='.aster-checkpoints/'+name+'/active-manifest.json';put(path,new);before[path]=sha(old)
    path='.aster-checkpoints/aster-video-scrub-20261024/prepared-native-manifest.json';put(path,scrub_raw);before[path]=sha(scrub_before)
    records=[]
    for path,data in sorted(payload.items()):
        target=output/'payload'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        records.append(dict(path=path,sha256=sha(data),before_sha256=before.get(path)))
    manifest=dict(schema=1,kind='hp-household-feedback',name='aster-feedback1',files=records,
        music_archive=music['sha256'],music_manifest=sha(music_raw),series_manifest=series_sha,
        music_integration=integration_sha,series_integration=series_integration_sha,rail=rail_sha,
        search=sha(search_raw),scrub=sha(scrub_raw))
    raw=raw_json(manifest);(output/'manifest.json').write_bytes(raw)
    return sha(raw)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--snapshot',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();print(build(args.snapshot,args.output))
