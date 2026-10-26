"""Approved VM103/Core delivery provisioning. Private key never leaves HA."""
import argparse
import base64
import json
from pathlib import Path
import shlex
import subprocess

HOSTKEY='192.168.1.140 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILkgcDkazx1+OSykeQg5F5wpZx71VX+O5r9QqKbib+BB\n'
SOURCE=r'''
import asyncio,base64,hashlib,importlib.util,json,os,stat,sys,tempfile
from pathlib import Path
import asyncssh
P=Path('/config/custom_components/aster_home_registry')
ROOT=Path('/config/.aster-home-delivery')
CP=Path('/config/aster-checkpoints/home-delivery-20261026')
OLD='17cf54d2d064f5c2ca66dff9bad504cc5caf4aebbae241fb0619475099a11eb1'
mode=sys.argv[1];bundle=json.loads(base64.b64decode(sys.argv[2]))
data={name:base64.b64decode(value) for name,value in bundle.items()}
def require(ok,code):
    if not ok:raise RuntimeError(code)
def digest(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_nlink==1,'delivery-source-file')
    return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,raw):
    fd,tmp=tempfile.mkstemp(prefix='.delivery.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.chmod(tmp,0o600);os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def load():
    spec=importlib.util.spec_from_file_location('delivery_operator_check',P/'delivery.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);return module
try:
    require(set(data)=={'__init__.py','delivery.py','home_status_model.py','known_hosts'},'delivery-source-bundle')
    for name in ('__init__.py','delivery.py','home_status_model.py'):compile(data[name],name,'exec')
    if mode=='prepare':
        require(not ROOT.exists() and not CP.exists() and not (P/'delivery.py').exists(),'delivery-source-already-prepared')
        require(digest(P/'__init__.py')==OLD,'delivery-source-predecessor')
        CP.mkdir(mode=0o700,parents=True)
        for name,path in (('__init__.py',P/'__init__.py'),('configuration.yaml',Path('/config/configuration.yaml'))):
            atomic(CP/name,path.read_bytes());require(digest(CP/name)==digest(path),'delivery-source-checkpoint')
        with tempfile.TemporaryDirectory(prefix='restore-',dir=CP) as folder:
            for name in ('__init__.py','configuration.yaml'):
                out=Path(folder)/name;out.write_bytes((CP/name).read_bytes())
                require(digest(out)==digest(CP/name),'delivery-source-isolated-restore')
        ROOT.mkdir(mode=0o700)
        key=asyncssh.generate_private_key('ssh-ed25519')
        atomic(ROOT/'id_ed25519',key.export_private_key('openssh'))
        public=' '.join(key.export_public_key().decode().split()[:2])
        atomic(ROOT/'id_ed25519.pub',(public+'\n').encode())
        atomic(ROOT/'known_hosts',data['known_hosts']);atomic(ROOT/'home_status_model.py',data['home_status_model.py'])
        identity=dict(model_sha256=hashlib.sha256(data['home_status_model.py']).hexdigest(),
            hostkey_sha256=hashlib.sha256(data['known_hosts']).hexdigest(),public_fingerprint=key.get_fingerprint())
        atomic(ROOT/'identity.json',json.dumps(identity,sort_keys=True).encode())
        record=dict(before=OLD,config_sha256=digest(CP/'configuration.yaml'),
                    candidate={n:hashlib.sha256(data[n]).hexdigest() for n in ('__init__.py','delivery.py')})
        atomic(CP/'state.json',json.dumps(record,sort_keys=True).encode())
        atomic(P/'delivery.py',data['delivery.py']);atomic(P/'__init__.py',data['__init__.py'])
    record=json.loads((CP/'state.json').read_text())
    require(digest(CP/'__init__.py')==OLD and digest(Path('/config/configuration.yaml'))==record['config_sha256'],'delivery-source-recovery-drift')
    require(record['candidate']=={n:hashlib.sha256(data[n]).hexdigest() for n in ('__init__.py','delivery.py')},'delivery-source-candidate-drift')
    for name,wanted in record['candidate'].items():
        require(digest(P/name)==(OLD if mode=='reapply' and name=='__init__.py' else wanted),'delivery-source-code-drift')
    if mode=='reapply':atomic(P/'__init__.py',data['__init__.py'])
    identity=json.loads((ROOT/'identity.json').read_text())
    require(digest(ROOT/'known_hosts')==identity['hostkey_sha256'] and digest(ROOT/'home_status_model.py')==identity['model_sha256'],'delivery-source-runtime-drift')
    keyinfo=(ROOT/'id_ed25519').lstat()
    require(not (ROOT/'id_ed25519').is_symlink() and stat.S_IMODE(keyinfo.st_mode)==0o600 and keyinfo.st_nlink==1,'delivery-source-key-mode')
    if mode in ('enable','disable'):
        atomic(ROOT/'enabled.json',json.dumps(dict(enabled=mode=='enable',interval_seconds=300,target='hp-only')).encode())
    if mode=='rollback':atomic(P/'__init__.py',(CP/'__init__.py').read_bytes());atomic(ROOT/'enabled.json',b'{"enabled":false,"interval_seconds":300,"target":"hp-only"}')
    result=dict(passed=True,mode=mode,checkpoint_verified=True,isolated_restore_verified=True,
                configuration_unchanged=True,private_key_exported=False,fingerprint=identity['public_fingerprint'])
    if mode in ('prepare','verify'):result['public_key']=(ROOT/'id_ed25519.pub').read_text().strip()
    if mode=='publish':result['publication']=asyncio.run(load().publish())
    if mode in ('bad-command','bad-payload','bad-forward','bad-hostkey'):
        async def negative():
            known=(('192.168.1.140 '+(ROOT/'id_ed25519.pub').read_text()).encode() if mode=='bad-hostkey' else str(ROOT/'known_hosts'))
            try:
                async with asyncssh.connect('192.168.1.140',port=22,username='root',client_keys=[str(ROOT/'id_ed25519')],
                    known_hosts=known,config=[],agent_path=None,preferred_auth=['publickey'],
                    disable_trivial_auth=True,connect_timeout=7,login_timeout=7) as conn:
                    if mode=='bad-forward':
                        try:
                            reader,writer=await conn.open_connection('127.0.0.1',22)
                        except asyncssh.ChannelOpenError:return dict(denied=True)
                        writer.close();raise RuntimeError('delivery-source-forward-not-denied')
                    reply=await conn.run('id' if mode=='bad-command' else 'aster-home-publish-v1',input=b'not-json',encoding=None,timeout=12,check=False)
            except asyncssh.HostKeyNotVerifiable:
                require(mode=='bad-hostkey','delivery-source-unexpected-hostkey');return dict(denied=True)
            require(mode!='bad-hostkey','delivery-source-hostkey-not-denied')
            require(reply.exit_status!=0 and len(reply.stdout)<=4096 and json.loads(reply.stdout).get('ok') is False,'delivery-source-negative-not-denied')
            return dict(denied=True)
        result['negative']=asyncio.run(negative())
    if mode=='health':
        result['enabled']=load().enabled();result['health']=json.loads((ROOT/'health.json').read_text())
    atomic(CP/(mode+'-proof.json'),json.dumps(result,sort_keys=True).encode())
    print(json.dumps(result))
except Exception as error:
    code=str(error);print(json.dumps(dict(passed=False,code=code if isinstance(error,RuntimeError) and code.startswith('delivery-source-') else type(error).__name__)))
    raise SystemExit(1)
'''

def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('prepare','verify','enable','disable','rollback','reapply','publish','bad-command','bad-payload','bad-forward','bad-hostkey','health'))
    args=parser.parse_args();base=Path(__file__).parent
    files={name:(base/'custom_components/aster_home_registry'/name).read_bytes() for name in ('__init__.py','delivery.py')}
    files['home_status_model.py']=(base.parents[1]/'kodi/v2/home_status_model.py').read_bytes()
    files['known_hosts']=HOSTKEY.encode()
    bundle=base64.b64encode(json.dumps({n:base64.b64encode(v).decode() for n,v in files.items()}).encode()).decode()
    require_ascii=SOURCE.isascii()
    if not require_ascii:raise ValueError('delivery-source-command-encoding')
    cmd=shlex.join(['qm','guest','exec','103','--','docker','exec','homeassistant','python3','-c',SOURCE,args.mode,bundle])
    reply=subprocess.run(['ssh','-o','BatchMode=yes','proxmox',cmd],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=45,check=True)
    if len(reply.stdout)>16000:raise ValueError('delivery-source-result-size')
    guest=json.loads(reply.stdout)
    if guest.get('out-truncated')!=0:raise ValueError('delivery-source-truncated')
    result=json.loads(guest.get('out-data','{}'));print(json.dumps(result))
    if guest.get('exitcode')!=0 or result.get('passed') is not True:raise SystemExit(1)

if __name__=='__main__':main()
