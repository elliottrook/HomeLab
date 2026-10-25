"""Compose the third visual review from the exact installed review2 package."""
import argparse,hashlib,json,zipfile,stat
from pathlib import Path
import xml.etree.ElementTree as ET
from review3_ui import top_pills,media_header,shorter_rail,shorter_browser_rail,lighter_menus,books_clock,keyboard
HERE=Path(__file__).resolve().parent
SKIN='.kodi/addons/skin.asterhome/'
PREVIOUS='e82560124c0d61fb997edac12e158bed3fba95c5d3d5cf4e476909e5bd57929f'
BOOKS='0def99963e27add62f7b13c13568bdfcf8d6ea7669fec9a389e1098797b9269c'
RAIL='3c167d9d8db5098abe8d87aaa99cc755692292fa31d6e634359e63baea662b45'
def sha(data):return hashlib.sha256(data).hexdigest()
def raw(value):return (json.dumps(value,indent=2)+'\n').encode()
def rows(files):return [dict(path=n,bytes=len(d),sha256=sha(d)) for n,d in sorted(files.items())]
def build(previous,snapshot,books,output,*,current=None):
    previous,snapshot,books,output=map(Path,(previous,snapshot,books,output))
    if output.exists():raise ValueError('immutable-review3')
    if sha((previous/'manifest.json').read_bytes())!=PREVIOUS or sha((books/'manifest.json').read_bytes())!=BOOKS:raise ValueError('exact-review-predecessors')
    old=json.loads((previous/'manifest.json').read_text());before={};files={}
    generation=4 if current else 3
    current_manifest=None
    if current:
        current=Path(current)
        digest=sha((current/'manifest.json').read_bytes())
        if digest not in ('7c8809174b1123765822ada12ea4a28bb534703a4baed5cb21a1c30236c2ea11','0f3bffbaf0a23749bf014726fc854b8cbd7ce4d7e76bea9d23392e593a394e6a','76e97d657eb6a1ef07d61e2f0f7cbe907fe8ec705631d314e906126d2c3d4966','abcdf6a8deb7d8907ec34745877d05fcaeebce47c1a7a78e3628558765731472','0e08428ee0342a4e6d957352b4936681803243c556fe4fbdc43839983462a6a3'):raise ValueError('exact-caption-predecessor')
        if digest=='0f3bffbaf0a23749bf014726fc854b8cbd7ce4d7e76bea9d23392e593a394e6a':generation=5
        if digest=='76e97d657eb6a1ef07d61e2f0f7cbe907fe8ec705631d314e906126d2c3d4966':generation=6
        if digest=='abcdf6a8deb7d8907ec34745877d05fcaeebce47c1a7a78e3628558765731472':generation=7
        if digest=='0e08428ee0342a4e6d957352b4936681803243c556fe4fbdc43839983462a6a3':generation=8
        current_manifest=json.loads((current/'manifest.json').read_text())
    music_stage='aster-music-v2lab-0.1.0-candidate'+str(64+generation)
    series_stage='aster-series-preview'+str(16+generation)
    search_stage='aster-global-search-ui'+str(13+generation)
    books_stage='aster-books-sync'+str(5+generation)
    for r in old['files']:
        data=(previous/'payload'/r['path']).read_bytes()
        if sha(data)!=r['sha256']:raise ValueError('previous-payload-drift')
        files[r['path']]=data;before[r['path']]=r['sha256']
    def oldstage(name):
        prefix='.aster-staging/'+name+'/'
        return {n[len(prefix):]:d for n,d in files.items() if n.startswith(prefix)}
    changed={};payload={}
    def put(n,d,prior=None):payload[n]=d;changed[n]=prior if prior is not None else before.get(n)
    def skin(n,d):
        target=SKIN+n;source=snapshot/'skin-before'/Path(n).name
        put(target,d,before.get(target) or sha(source.read_bytes()))
    def stage(name,objects,metadata):
        metadata=dict(metadata,files=rows(objects));data=raw(metadata)
        for n,d in objects.items():put('.aster-staging/'+name+'/'+n,d)
        put('.aster-staging/'+name+'/manifest.json',data);return data
    def active(name,data):put('.aster-checkpoints/'+name+'/active-manifest.json',data)
    # Consistent native page headers. Keep OSD transport XML entirely untouched.
    pages={}
    for p in (snapshot/'skin-before').glob('*.xml'):
        if p.name.startswith('.'):continue  # macOS copy metadata, not Kodi source.
        if p.name in ('Home.xml','VideoOSD.xml','IncludesHub.xml','MyMusicNav.xml','DialogKeyboard.xml','DialogSelect.xml'):continue
        data=p.read_bytes();root=ET.fromstring(data)
        has_top=any(c.get('type')=='button' and c.findtext('top','').isdecimal() and int(c.findtext('top'))<=100
            and c.findtext('left','').isdecimal() and int(c.findtext('left'))>=300 for c in root.iter('control'))
        template=any(i.get('name') in ('AsterTopCategoryButton','AsterMusicPillButton') for i in root.findall('include'))
        if has_top or template:pages['1080i/'+p.name]=top_pills(data)
    pages['1080i/DialogKeyboard.xml']=keyboard((snapshot/'skin-before/DialogKeyboard.xml').read_bytes())
    pages['1080i/DialogSelect.xml']=lighter_menus((snapshot/'skin-before/DialogSelect.xml').read_bytes())
    for n,d in pages.items():skin(n,d)
    for n in ('tools/compact_menu.py','resources/skins/Default/1080i/CompactMenu.xml'):
        d=files[SKIN+n]
        if n.endswith('.xml'):d=lighter_menus(d)
        if d!=files[SKIN+n]:put(SKIN+n,d)
    # Short shared navigation rail, retaining all focus-entry/route IDs.
    rail_raw=(snapshot/'rail-before.json').read_bytes()
    if sha(rail_raw)!=RAIL:raise ValueError('rail-predecessor')
    rail=json.loads(rail_raw);rail_xml=(snapshot/'skin-before/IncludesHub.xml').read_bytes()
    if sha(rail_xml)!=rail['sha256']:raise ValueError('rail-source-drift')
    rail_new=shorter_rail(rail_xml);skin('1080i/IncludesHub.xml',rail_new)
    put('.aster-checkpoints/aster-floating-rail-20261024/active-manifest.json',raw(dict(rail,before_sha256=rail['sha256'],sha256=sha(rail_new),previous_manifest_sha256=RAIL)),RAIL)
    # Music67: only its internal browser header/rail changes; queue engine stays byte-identical.
    music_prefix='.kodi/addons/script.astermusic.v2lab/'
    music={n[len('.kodi/addons/'):]:d for n,d in files.items() if n.startswith(music_prefix)}
    name='script.astermusic.v2lab/resources/skins/Default/1080i/MusicLab.xml'
    music[name]=shorter_browser_rail(top_pills(music[name]))
    output.mkdir();archive=output/'script.astermusic.v2lab-0.1.0.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for n,d in sorted(music.items()):
            info=zipfile.ZipInfo(n,(2026,10,23,1,0,0));info.create_system=3;info.external_attr=(stat.S_IFREG|0o644)<<16
            z.writestr(info,d,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
            if d!=files['.kodi/addons/'+n]:put('.kodi/addons/'+n,d)
    old_music=json.loads(files['.aster-staging/aster-music-v2lab-0.1.0-candidate66/manifest.json'])
    music_meta=raw(dict(old_music,sha256=sha(archive.read_bytes()),files=rows(music)))
    put('.aster-staging/'+music_stage+'/manifest.json',music_meta)
    put('.aster-staging/'+music_stage+'/'+archive.name,archive.read_bytes())
    # Series19: bounded five-row season slice plus lighter backdrop.
    series=oldstage('aster-series-preview18');series_meta=json.loads(series.pop('manifest.json'))
    series['default.py']=(HERE/'series_preview/default.py').read_bytes()
    series['resources/skins/Default/1080i/SeriesPreview.xml']=lighter_menus((HERE/'series_preview/resources/skins/Default/1080i/SeriesPreview.xml').read_bytes())
    series_raw=stage(series_stage,series,series_meta)
    route=files[SKIN+'tools/aster_v2_series.py'].replace(b'aster-series-preview18',series_stage.encode()).replace(old['series'].encode(),sha(series_raw).encode())
    put(SKIN+'tools/aster_v2_series.py',route)
    si_name='.aster-checkpoints/aster-series-integration-20261024/active-manifest.json'
    si=json.loads(files[si_name]);si.update(series_stage=series_stage,series_manifest_sha256=sha(series_raw))
    for r in si['files']:
        if r['path']=='tools/aster_v2_series.py':r.update(sha256=sha(route),bytes=len(route))
    put(si_name,raw(si))
    mi_name='.aster-checkpoints/aster-music-integration-20261024/active-manifest.json'
    mi=json.loads(files[mi_name]);mi['player_sha_at_deploy']=sha(archive.read_bytes())
    for r in mi['files']:
        data=payload.get(SKIN+r['path'],files[SKIN+r['path']]);r.update(sha256=sha(data),bytes=len(data))
    put(mi_name,raw(mi))
    # Search16 retains the direct-link behavior and its exact child checks.
    search=oldstage('aster-global-search-ui15');search_meta=json.loads(search.pop('manifest.json'))
    old_search=current_manifest['search'] if current_manifest else sha(files['.aster-staging/aster-global-search-ui15/manifest.json'])
    for n in list(search):
        if n.endswith(('.py','.xml')):search[n]=search[n].replace(b'aster-global-search-ui15',search_stage.encode()).replace(b'aster-series-preview18',series_stage.encode()).replace(b'aster-music-v2lab-0.1.0-candidate66',music_stage.encode())
    search['overlay/Home.xml']=media_header(search['overlay/Home.xml'])
    search['resources/lib/search_handoff.py']=search['resources/lib/search_handoff.py'].replace(old['series'].encode(),sha(series_raw).encode()).replace(old['music_manifest'].encode(),sha(music_meta).encode())
    search['resources/lib/movie_player.py']=search['resources/lib/movie_player.py'].replace(search_meta['previous_manifest_sha256'].encode(),old_search.encode())
    search_raw=stage(search_stage,search,dict(search_meta,stage=search_stage,previous_manifest_sha256=old_search))
    active('aster-global-search-20261024',search_raw);skin('1080i/Home.xml',search['overlay/Home.xml'])
    from movie_player import TARGETS
    for source,target in TARGETS.items():skin(target,search[source])
    # Books8 is a colour-only successor; no service, progress, bookmark or playback logic change.
    book_meta=json.loads((books/'manifest.json').read_text());book_objects={r['path']:(books/'payload'/r['path']).read_bytes() for r in book_meta['files']}
    book_path=SKIN+'1080i/MyMusicNav.xml';book_objects[book_path]=books_clock(book_objects[book_path])
    skin('1080i/MyMusicNav.xml',book_objects[book_path])
    prior_book={r['path']:r['sha256'] for r in book_meta['files']}
    book_previous=current_manifest['books'] if current_manifest else BOOKS
    if current_manifest:
        old_book_path=current/('payload/.aster-staging/aster-books-sync'+str(4+generation)+'/manifest.json')
        prior_book={r['path']:r['sha256'] for r in json.loads(old_book_path.read_text())['files']}
    book_new=dict(book_meta,stage=books_stage,previous_manifest_sha256=book_previous,
        files=[dict(path=n,sha256=sha(d),before_sha256=prior_book[n]) for n,d in sorted(book_objects.items())])
    for n,d in book_objects.items():put('.aster-staging/'+books_stage+'/payload/'+n,d)
    book_raw=raw(book_new);put('.aster-staging/'+books_stage+'/manifest.json',book_raw)
    put('.aster-checkpoints/aster-books-sync-20261025/active-manifest.json',book_raw,BOOKS)
    records=[]
    actual=dict(before)
    if generation>=5:
        ancestor=current.parent/'candidate3/manifest.json'
        if sha(ancestor.read_bytes())!='7c8809174b1123765822ada12ea4a28bb534703a4baed5cb21a1c30236c2ea11':raise ValueError('exact-caption-ancestor')
        actual.update({r['path']:r['sha256'] for r in json.loads(ancestor.read_text())['files']})
    if generation>=6:
        ancestor=current.parent/'captionfix1/manifest.json'
        if sha(ancestor.read_bytes())!='0f3bffbaf0a23749bf014726fc854b8cbd7ce4d7e76bea9d23392e593a394e6a':raise ValueError('exact-ring-ancestor')
        actual.update({r['path']:r['sha256'] for r in json.loads(ancestor.read_text())['files']})
    if generation>=7:
        ancestor=current.parent/'ringfix1/manifest.json'
        if sha(ancestor.read_bytes())!='76e97d657eb6a1ef07d61e2f0f7cbe907fe8ec705631d314e906126d2c3d4966':raise ValueError('exact-season-ancestor')
        actual.update({r['path']:r['sha256'] for r in json.loads(ancestor.read_text())['files']})
    if generation==8:
        ancestor=current.parent/'seasonfix1/manifest.json'
        if sha(ancestor.read_bytes())!=current_manifest['previous_manifest_sha256']:raise ValueError('exact-button-ancestor')
        actual.update({r['path']:r['sha256'] for r in json.loads(ancestor.read_text())['files']})
    if current_manifest:actual.update({r['path']:r['sha256'] for r in current_manifest['files']})
    for n,d in sorted(payload.items()):
        expected=actual.get(n,changed[n])
        if expected==sha(d):continue
        target=output/'payload'/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(d)
        records.append(dict(path=n,sha256=sha(d),before_sha256=expected))
    manifest=dict(kind='hp-review'+str(generation),name='aster-review'+str(generation),previous_manifest_sha256=sha((current/'manifest.json').read_bytes()) if current_manifest else PREVIOUS,files=records,
        music_archive=sha(archive.read_bytes()),music_manifest=sha(music_meta),series=sha(series_raw),
        series_integration=sha(raw(si)),music_integration=sha(raw(mi)),search=sha(search_raw),books=sha(book_raw),
        rail=sha(raw(dict(rail,before_sha256=rail['sha256'],sha256=sha(rail_new),previous_manifest_sha256=RAIL))),scrub=old['scrub'])
    (output/'manifest.json').write_bytes(raw(manifest));return sha(raw(manifest))
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for arg in ('previous','snapshot','books','output'):p.add_argument('--'+arg,required=True)
    p.add_argument('--current')
    a=p.parse_args();print(build(a.previous,a.snapshot,a.books,a.output,current=a.current))
