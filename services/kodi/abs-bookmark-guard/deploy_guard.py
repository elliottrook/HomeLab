"""Bounded TrueNAS checkpoint/activation. No credential output or DB rollback.

Operator approval is required. Exact pinned image and five source files only.
Private recovery keeps configuration/secrets on their original host.
"""
import argparse,hashlib,json,os,re,shutil,sqlite3,subprocess,tempfile,time,urllib.request
from pathlib import Path
import yaml
from verify_guard import verify
from build_guard import EXPECTED,IMAGE_ID

COMPOSE=Path('/mnt/Media/appdata/dockge/unified-media-shadow/compose.yaml')
CONFIG=Path('/mnt/Media/appdata/unified-media-shadow/audiobookshelf')
STAGE=Path('/mnt/Media/appdata/aster-bookmark-linuxcheck-20261025/candidate')
CHECKPOINT=Path('/mnt/Media/appdata/aster-bookmark-guard-checkpoint-20261025')
DIGEST='a489b3b041ef7652467952774a80082f3c4abd8721cd575adc184dc04792fdcb'
CONTAINER='unified-audiobookshelf-shadow'
SERVICE='audiobookshelf'
_COMPOSE_ENV=None
def compose_env():
    """Recover only non-secret path substitutions from their live mounts.

    This stack has no saved .env. Do not guess required worker paths or read
    another stack's credentials just to render the unchanged definition.
    """
    global _COMPOSE_ENV
    if _COMPOSE_ENV is not None:return _COMPOSE_ENV
    definition=yaml.safe_load(COMPOSE.read_bytes());values={}
    # Only this service is recreated. Required substitutions belonging to a
    # retired Calibre worker are neither guessed nor used to start that worker.
    required=set(re.findall(r'\$\{(UNIFIED_[A-Z_]+):\?',yaml.safe_dump(definition['services'][SERVICE])))
    needed=required|{'UNIFIED_CONFIG_PATH','UNIFIED_AUDIOBOOKS_PATH','UNIFIED_PODCASTS_PATH'}
    pattern=re.compile(r'^\$\{(UNIFIED_[A-Z_]+)(?::-[^}]+|:\?[^}]*)?\}([^:]*):([^:]+)(?::(?:ro|rw))?$')
    for service in definition['services'].values():
        name=service.get('container_name')
        if not isinstance(name,str) or not name.startswith('unified-'):continue
        result=subprocess.run(['docker','inspect',name],capture_output=True,timeout=15)
        if result.returncode:continue
        info=json.loads(result.stdout)[0]
        for volume in service.get('volumes',[]):
            match=pattern.fullmatch(volume) if isinstance(volume,str) else None
            if not match:continue
            variable,suffix,destination=match.groups()
            if variable not in needed:continue
            mounts=[m for m in info['Mounts'] if m['Destination']==destination and m['Type']=='bind']
            if len(mounts)!=1:continue
            source=mounts[0]['Source']
            if suffix and not source.endswith(suffix):continue
            value=source[:-len(suffix)] if suffix else source
            require(value.startswith('/mnt/Media/') and (variable not in values or values[variable]==value),'ambiguous-compose-path-'+variable)
            values[variable]=value
    actual=dict(item.split('=',1) for item in inspect()['Config']['Env'])
    if 'TZ' in actual:values['TZ']=actual['TZ']
    require(required<=set(values),'required-live-path-not-derived')
    _COMPOSE_ENV=dict(os.environ,**values);return _COMPOSE_ENV
def require(value,code):
    if not value:raise RuntimeError(code)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def command(args):
    # Captured output may contain private Compose/environment details. Never
    # expose exceptions/stdout from subprocesses to the operator channel.
    result=subprocess.run(args,capture_output=True,timeout=120,
                          env=compose_env() if args[:2]==['docker','compose'] else None)
    require(result.returncode==0,'private-command-failed');return result.stdout
def atomic(path,data):
    fd,name=tempfile.mkstemp(prefix='.aster-guard-',dir=path.parent)
    with os.fdopen(fd,'wb') as output:output.write(data);output.flush();os.fsync(output.fileno())
    os.chmod(name,0o600);os.replace(name,path)
def private_json(path,value):atomic(path,(json.dumps(value,indent=2)+'\n').encode())
def inspect():return json.loads(command(['docker','inspect',CONTAINER]))[0]
def focused_compose(path=COMPOSE):
    definition=yaml.safe_load(path.read_bytes())
    definition['services']={SERVICE:definition['services'][SERVICE]}
    require(not definition['services'][SERVICE].get('depends_on'),'unexpected-service-dependency')
    project=inspect()['Config']['Labels']['com.docker.compose.project']
    require(project=='unified-media-shadow','known-compose-project')
    definition['name']=project
    data=yaml.safe_dump(definition,sort_keys=False).encode()
    target=COMPOSE.with_name('.aster-guard-target-'+hashlib.sha256(data).hexdigest()[:16]+'.yaml')
    if target.exists():require(target.read_bytes()==data,'focused-compose-drift')
    else:atomic(target,data)
    return target
def rendered(path=COMPOSE):
    return json.loads(command(['docker','compose','-p','unified-media-shadow','-f',str(focused_compose(path)),'config','--format','json']))
def original_sources():
    for path,digest in EXPECTED.items():
        code=command(['docker','exec',CONTAINER,'node','-e',
            "process.stdout.write(require('crypto').createHash('sha256').update(require('fs').readFileSync('/app/"+path+"')).digest('hex'))"])
        require(code.decode()==digest,'original-code-drift')
def coherent(path):
    require(path.name=='absdatabase.sqlite' and path.parent in (CHECKPOINT/'config-backup',CHECKPOINT/'isolated-restore'),'isolated-backup-only')
    # TrueNAS Python SQLite3.40 cannot parse ABS's ORDER BY aggregate triggers.
    # Validate with the pinned service's newer SQLite, never alter the schema.
    code="""const s=require('sqlite3');const db=new s.Database('/proof/absdatabase.sqlite',s.OPEN_READONLY);
const all=q=>new Promise((ok,no)=>db.all(q,(e,r)=>e?no(e):ok(r)));
(async()=>{const i=await all('PRAGMA integrity_check');if(i.length!==1||i[0].integrity_check!=='ok')throw Error('integrity');
if((await all('PRAGMA foreign_key_check')).length)throw Error('foreign-key');
const t=await all(\"SELECT count(*) AS n FROM sqlite_master WHERE type='table'\");
process.stdout.write(JSON.stringify({ok:true,tables:t[0].n}));db.close()})().catch(()=>process.exit(1));"""
    data=command(['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL',
        '--security-opt','no-new-privileges','--memory','256m','--pids-limit','64',
        '--tmpfs','/tmp:rw,nosuid,nodev,size=32m','--mount','type=bind,src='+str(path.parent)+',dst=/proof,readonly',
        '--workdir','/app','--entrypoint','node',IMAGE_ID,'-e',code])
    value=json.loads(data);require(value.get('ok') is True,'backup-integrity-failed');return value['tables']
def checkpoint():
    require(os.geteuid()==0 and not CHECKPOINT.exists(),'new-root-private-checkpoint-required')
    verify(STAGE,DIGEST);live=inspect()
    require(live['Image']==IMAGE_ID and live['State']['Running'],'pinned-running-service-required')
    original_sources();definition=rendered()
    require(definition['services'][SERVICE]['container_name']==CONTAINER,'compose-container-identity')
    # Decline a live/Compose environment mismatch before recreation can change it.
    actual=dict(item.split('=',1) for item in live['Config']['Env'])
    require(all(actual.get(k)==str(v) for k,v in definition['services'][SERVICE].get('environment',{}).items()),'live-compose-environment-drift')
    volume_rows=definition['services'][SERVICE]['volumes']
    expected={(v['source'],v['target'],not v.get('read_only',False)) for v in volume_rows}
    require(expected=={(m['Source'],m['Destination'],m['RW']) for m in live['Mounts']},'live-compose-mount-drift')
    CHECKPOINT.mkdir(mode=0o700)
    atomic(CHECKPOINT/'compose.before.yaml',COMPOSE.read_bytes())
    private_json(CHECKPOINT/'container.before.json',live);private_json(CHECKPOINT/'rendered.before.json',definition)
    require(not any(p.is_symlink() for p in CONFIG.rglob('*')),'config-symlink-refused')
    backup=CHECKPOINT/'config-backup'
    shutil.copytree(CONFIG,backup,ignore=lambda d,n:[s for s in n if s.startswith('absdatabase.sqlite')])
    with sqlite3.connect('file:'+str(CONFIG/'absdatabase.sqlite')+'?mode=ro',uri=True) as source:
        with sqlite3.connect(backup/'absdatabase.sqlite') as target:source.backup(target)
    return finish_checkpoint()
def finish_checkpoint():
    require(CHECKPOINT.is_dir() and not (CHECKPOINT/'checkpoint.json').exists(),'unfinished-checkpoint-required')
    require(COMPOSE.read_bytes()==(CHECKPOINT/'compose.before.yaml').read_bytes(),'checkpoint-compose-drift')
    require(inspect()['Image']==IMAGE_ID,'checkpoint-image-drift')
    original_sources()
    backup=CHECKPOINT/'config-backup';tables=coherent(backup/'absdatabase.sqlite')
    restored=CHECKPOINT/'isolated-restore';shutil.copytree(backup,restored)
    require(coherent(restored/'absdatabase.sqlite')==tables,'restore-table-drift')
    files=[p for p in backup.rglob('*') if p.is_file()]
    require(all(sha(p)==sha(restored/p.relative_to(backup)) for p in files),'restore-copy-drift')
    for base in (backup,restored):
        for p in (base,*base.rglob('*')):os.chmod(p,0o700 if p.is_dir() else 0o600)
    result=dict(checkpointed=True,backup_integrity=True,isolated_restore=True,files=len(files),tables=tables,
                compose_sha256=sha(COMPOSE),candidate_sha256=DIGEST)
    private_json(CHECKPOINT/'checkpoint.json',result);return result
def patch_compose(data):
    text=data.decode();match=re.search(r'^  audiobookshelf:.*?(?=^  [a-zA-Z0-9_-]+:|^[a-zA-Z0-9_-]+:|\Z)',text,re.M|re.S)
    require(match is not None,'service-text-anchor')
    block=match.group();anchor=re.search(r'^    volumes:\s*\n',block,re.M)
    require(anchor is not None,'volume-text-anchor')
    tail=block[anchor.end():];boundary=re.search(r'^    [a-zA-Z0-9_-]+:',tail,re.M)
    offset=anchor.end()+(boundary.start() if boundary else len(tail))
    manifest=json.loads((STAGE/'manifest.json').read_text())
    additions=''.join('      - '+str(STAGE/'payload'/r['path'])+':/app/'+r['path']+':ro\n' for r in manifest['files'])
    block=block[:offset].rstrip()+'\n'+additions+block[offset:]
    changed=(text[:match.start()]+block+text[match.end():]).encode()
    old=yaml.safe_load(data);new=yaml.safe_load(changed)
    added=[str(STAGE/'payload'/r['path'])+':/app/'+r['path']+':ro' for r in manifest['files']]
    new['services'][SERVICE]['volumes']=new['services'][SERVICE]['volumes'][:-5]
    require(new==old and yaml.safe_load(changed)['services'][SERVICE]['volumes'][-5:]==added,'compose-narrow-change-required')
    return changed
def recreate():command(['docker','compose','-p','unified-media-shadow','-f',str(focused_compose()),'up','-d','--no-deps','--no-build','--pull','never',SERVICE])
def activate():
    require((CHECKPOINT/'checkpoint.json').exists() and not (CHECKPOINT/'activated.json').exists(),'checkpoint-once-required')
    verify(STAGE,DIGEST);original_sources();before=json.loads((CHECKPOINT/'container.before.json').read_text())
    require(inspect()['Image']==IMAGE_ID and COMPOSE.read_bytes()==(CHECKPOINT/'compose.before.yaml').read_bytes(),'activation-predecessor-drift')
    changed=patch_compose(COMPOSE.read_bytes())
    atomic(CHECKPOINT/'compose.candidate.yaml',changed)
    # Render beside the real Compose to preserve its .env/project-relative inputs.
    candidate=COMPOSE.with_name('aster-guard-candidate.yaml')
    require(not candidate.exists(),'candidate-path-exists');atomic(candidate,changed)
    after_render=rendered(candidate);old_render=rendered()
    new_service=after_render['services'][SERVICE];old_service=old_render['services'][SERVICE]
    require(len(new_service['volumes'])==len(old_service['volumes'])+5,'five-added-mounts')
    new_service['volumes']=new_service['volumes'][:-5]
    require(after_render==old_render,'rendered-compose-drift')
    atomic(COMPOSE,changed)
    try:
        recreate();after=inspect()
        require(after['Image']==IMAGE_ID and after['State']['Running'],'guard-service-not-running')
        for k in ('Env','Entrypoint','Cmd','User','WorkingDir'):
            require(after['Config'][k]==before['Config'][k],'runtime-config-changed')
        require(after['HostConfig']['PortBindings']==before['HostConfig']['PortBindings'],'ports-changed')
        for k in ('NetworkMode','RestartPolicy','ExtraHosts','CapAdd','CapDrop','SecurityOpt','ReadonlyRootfs','Privileged','Devices','Dns'):
            a,b=after['HostConfig'].get(k),before['HostConfig'].get(k)
            if k in ('ExtraHosts','CapAdd','CapDrop','SecurityOpt','Devices','Dns'):a,b=a or [],b or []
            require(a==b,'runtime-host-settings-changed')
        a,b=after['NetworkSettings']['Networks'],before['NetworkSettings']['Networks']
        require(set(a)==set(b) and all(a[k]['NetworkID']==b[k]['NetworkID'] for k in b),'runtime-networks-changed')
        original={(m['Source'],m['Destination'],m['RW']) for m in before['Mounts']}
        actual={(m['Source'],m['Destination'],m['RW']) for m in after['Mounts']}
        require(original<=actual and len(actual)==len(original)+5,'runtime-mounts-changed')
        manifest=json.loads((STAGE/'manifest.json').read_text())
        for row in manifest['files']:
            require((str(STAGE/'payload'/row['path']),'/app/'+row['path'],False) in actual,'readonly-guard-mount')
            value=command(['docker','exec',CONTAINER,'node','-e',"process.stdout.write(require('crypto').createHash('sha256').update(require('fs').readFileSync('/app/"+row['path']+"')).digest('hex'))"])
            require(value.decode()==row['sha256'],'running-code-drift')
        healthy=False
        for _ in range(30):
            try:
                with urllib.request.urlopen('http://192.168.20.40:30067/ping',timeout=2) as response:healthy=response.status==200
            except Exception:pass
            if healthy:break
            time.sleep(1)
        require(healthy,'service-health-failed')
        result=dict(activated=True,files_verified=5,original_mounts_preserved=True,ports_environment_preserved=True,
                    backup_integrity=True,isolated_restore=True,candidate_sha256=DIGEST)
        private_json(CHECKPOINT/'activated.json',result);return result
    except Exception:
        require(COMPOSE.read_bytes()==changed,'unknown-compose-drift-no-automatic-restore')
        atomic(COMPOSE,(CHECKPOINT/'compose.before.yaml').read_bytes());recreate()
        private_json(CHECKPOINT/'rolled-back.json',dict(code_only=True,database_restored=False));raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('checkpoint','finish-checkpoint','activate'));a=p.parse_args()
    try:print(json.dumps({'checkpoint':checkpoint,'finish-checkpoint':finish_checkpoint,'activate':activate}[a.mode]()))
    except Exception as error:
        print(json.dumps(dict(failed=True,code=str(error) if type(error) is RuntimeError else type(error).__name__)))
        raise SystemExit(1)
