#!/usr/bin/env python3
"""Install the bounded production TV queue/season fix with a full checkpoint."""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path('/storage/.kodi/addons')
RUNTIME = ROOT/'script.asterruntime'
SERIES = RUNTIME/'aster-series-preview24'
SEARCH = RUNTIME/'aster-global-search-ui22'
DEFAULT = SERIES/'default.py'
PLAYBACK = SERIES/'resources/lib/series_playback.py'
SERIES_MANIFEST = SERIES/'manifest.json'
LAUNCHER = ROOT/'skin.asterhome/tools/aster_v2_series.py'
HANDOFF = SEARCH/'resources/lib/search_handoff.py'
SEARCH_MANIFEST = SEARCH/'manifest.json'
FAMILY = RUNTIME/'family-manifest.json'
CHECKPOINT = Path('/storage/.aster-checkpoints/astertv-series-parked-queue-20261028')
PAYLOAD_DEFAULT = Path('/tmp/astertv-series-default-v2.py')
PAYLOAD_PLAYBACK = Path('/tmp/astertv-series-playback-v2.py')

PREVIOUS = {
    DEFAULT: '207a185c0792c64b86a35fa0ee7eaacdd8174ffec5d0ca5de015cf240d1713c4',
    PLAYBACK: 'f15013232c4319e3e410784eb75bd3d4d3295dcd096d270bdd4ccf554dbd487b',
    SERIES_MANIFEST: '66b6303f2dab9162e0f1fe305dcd173aae90fa7c1c6be395ba6b8f4a7e6ed9ae',
    FAMILY: 'ebb5e65b87990b3343e59bb6cd0669a9d03882ab107c3cb3ec77c76876f8a53c',
}

def sha(raw): return hashlib.sha256(raw).hexdigest()
def encoded(value): return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
def require(value, code):
    if not value: raise RuntimeError(code)

def atomic(path, raw):
    fd,name=tempfile.mkstemp(prefix='.aster-series-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.chmod(name,path.stat().st_mode & 0o777)
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

def pinned(raw,pattern,old,new):
    values=re.findall(pattern,raw)
    require(values==[old.encode()],'embedded-pin-predecessor')
    return raw.replace(old.encode(),new.encode(),1)

def main():
    require(os.uname().nodename=='AsterTVProd','production-only')
    require(not CHECKPOINT.exists(),'checkpoint-exists')
    paths=(DEFAULT,PLAYBACK,SERIES_MANIFEST,LAUNCHER,HANDOFF,SEARCH_MANIFEST,FAMILY)
    require(all(path.is_file() and not path.is_symlink() for path in paths),'unexpected-file')
    before={path:path.read_bytes() for path in paths}
    for path,digest in PREVIOUS.items():require(sha(before[path])==digest,'predecessor:'+str(path))
    require(subprocess.run(['systemctl','is-active','--quiet','kodi']).returncode!=0,'kodi-still-running')

    default=PAYLOAD_DEFAULT.read_bytes();playback=PAYLOAD_PLAYBACK.read_bytes()
    old_guard=b"if os.uname().nodename!='AsterTV':return"
    new_guard=b"if os.uname().nodename not in ('AsterTV','AsterTVProd'):return"
    require(default.count(old_guard)==2,'production-host-guard')
    default=default.replace(old_guard,new_guard)
    require(b'release_parked_video_queue' in default and b'release_parked_video_queue' in playback,'payload-boundary')
    series=json.loads(before[SERIES_MANIFEST]);require(series['component']=='aster-series-preview24','series-component')
    rows={row['path']:row for row in series['files']}
    for name,path,raw in (('default.py',DEFAULT,default),('resources/lib/series_playback.py',PLAYBACK,playback)):
        require(rows[name]['sha256']==sha(before[path]),'series-row-predecessor')
        rows[name].update(bytes=len(raw),sha256=sha(raw))
    series_after=encoded(series);series_pin=sha(series_after);old_pin=sha(before[SERIES_MANIFEST])
    launcher=pinned(before[LAUNCHER],rb"MANIFEST_SHA='([0-9a-f]{64})'",old_pin,series_pin)
    handoff=pinned(before[HANDOFF],rb"SERIES_SHA='([0-9a-f]{64})'",old_pin,series_pin)
    search=json.loads(before[SEARCH_MANIFEST]);require(search['component']=='aster-global-search-ui22','search-component')
    search_rows=[row for row in search['files'] if row['path']=='resources/lib/search_handoff.py']
    require(len(search_rows)==1 and search_rows[0]['sha256']==sha(before[HANDOFF]),'search-row-predecessor')
    search_rows[0].update(bytes=len(handoff),sha256=sha(handoff))
    search_after=encoded(search)
    family=json.loads(before[FAMILY]);require(family['components']['aster-series-preview24']['manifest_sha256']==old_pin,'family-series-predecessor')
    require(family['components']['aster-global-search-ui22']['manifest_sha256']==sha(before[SEARCH_MANIFEST]),'family-search-predecessor')
    require(family['skin']['tools/aster_v2_series.py']==sha(before[LAUNCHER]),'family-launcher-predecessor')
    family['components']['aster-series-preview24']['manifest_sha256']=series_pin
    family['components']['aster-global-search-ui22']['manifest_sha256']=sha(search_after)
    family['skin']['tools/aster_v2_series.py']=sha(launcher)
    after={DEFAULT:default,PLAYBACK:playback,SERIES_MANIFEST:series_after,LAUNCHER:launcher,HANDOFF:handoff,SEARCH_MANIFEST:search_after,FAMILY:encoded(family)}
    CHECKPOINT.mkdir(mode=0o700,parents=True)
    for path,raw in before.items():
        target=CHECKPOINT/'before'/path.relative_to(ROOT)
        target.parent.mkdir(mode=0o700,parents=True,exist_ok=True);target.write_bytes(raw)
    (CHECKPOINT/'state.json').write_text('{"state":"prepared"}\n')
    try:
        for path,raw in after.items():atomic(path,raw)
        require(all(path.read_bytes()==raw for path,raw in after.items()),'install-verification')
        (CHECKPOINT/'state.json').write_text('{"state":"installed"}\n')
    except Exception:
        for path,raw in before.items():atomic(path,raw)
        (CHECKPOINT/'state.json').write_text('{"state":"rolled-back"}\n')
        raise
    print(json.dumps(dict(installed=True,series_pin=series_pin,family_sha256=sha(after[FAMILY]),checkpoint=str(CHECKPOINT)),sort_keys=True))

if __name__=='__main__':main()
