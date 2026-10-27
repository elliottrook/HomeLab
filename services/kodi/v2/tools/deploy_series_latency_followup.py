"""Install, verify or roll back the exact HP TV-series latency successor."""

import hashlib,json,os,re,shutil,sys,tempfile,time
from pathlib import Path
import xbmc,xbmcgui

STAGE=Path('/storage/.aster-staging/aster-series-latency1')
CHECKPOINT=Path('/storage/.aster-checkpoints/aster-series-latency1')

def require(value,code):
    if not value:raise RuntimeError(code)
def sha(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_nlink==1,'series-latency-file')
    return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,raw):
    require(not path.is_symlink() and not path.parent.is_symlink(),'series-latency-linked-target')
    handle,temporary=tempfile.mkstemp(prefix='.series-latency-',dir=path.parent)
    try:
        with os.fdopen(handle,'wb') as stream:
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.chmod(temporary,0o600);os.replace(temporary,path)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)
def idle():
    players=json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"}')).get('result',[])
    return not players and xbmcgui.getCurrentWindowId()==10000 and not xbmcgui.Window(10000).getProperty('AsterSeries.PreviewWindow')
def contract(pin):
    require(re.fullmatch('[0-9a-f]{64}',pin or ''),'series-latency-pin')
    require(sha(STAGE/'manifest.json')==pin,'series-latency-manifest-pin')
    value=json.loads((STAGE/'manifest.json').read_bytes())
    require(value.get('schema')==1 and value.get('kind')=='hp-series-latency-followup.v1'
        and value.get('production_changed') is False and len(value.get('files',[]))==5,
        'series-latency-contract')
    for row in value['files']:
        require(row['path'].startswith(('.kodi/addons/skin.asterhome/',
            '.kodi/addons/script.asterruntime/')) and sha(STAGE/'payload'/row['path'])==row['sha256'],
            'series-latency-payload')
    return value
def run(mode,pin):
    require(os.uname().nodename=='AsterTV' and os.getuid()==0,'series-latency-hp')
    require(mode in ('install','verify','rollback'),'series-latency-mode')
    value=contract(pin);require(idle(),'series-latency-home-idle')
    if mode=='install':
        require(not CHECKPOINT.exists(),'series-latency-checkpoint-exists')
        for row in value['files']:
            require(sha(Path('/storage')/row['path'])==row['before_sha256'],'series-latency-predecessor')
        CHECKPOINT.mkdir(mode=0o700,parents=True)
        for row in value['files']:
            source=Path('/storage')/row['path'];target=CHECKPOINT/row['path']
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
            require(sha(target)==row['before_sha256'],'series-latency-checkpoint')
        shutil.copyfile(STAGE/'manifest.json',CHECKPOINT/'manifest.json')
        for row in value['files']:atomic(Path('/storage')/row['path'],(STAGE/'payload'/row['path']).read_bytes())
    elif mode=='rollback':
        for row in value['files']:
            require(sha(Path('/storage')/row['path'])==row['sha256']
                and sha(CHECKPOINT/row['path'])==row['before_sha256'],'series-latency-rollback-ownership')
        for row in value['files']:atomic(Path('/storage')/row['path'],(CHECKPOINT/row['path']).read_bytes())
    expected='before_sha256' if mode=='rollback' else 'sha256'
    require(all(sha(Path('/storage')/row['path'])==row[expected] for row in value['files']) and idle(),
        'series-latency-final')
    return {'passed':True,'mode':mode,'files':len(value['files']),'home':True}
if __name__=='__main__':
    try:result=run(sys.argv[1],sys.argv[2])
    except (OSError,RuntimeError,ValueError,KeyError,IndexError) as error:
        code=str(error);result={'passed':False,'code':code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__}
    (STAGE/('result-'+str(time.time_ns())+'.json')).write_text(json.dumps(result,indent=2)+'\n')
