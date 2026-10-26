"""Approved operator-only HA exporter checkpoint/install/verify/code rollback.

Fixed VM103/Core paths. No credentials, configuration edits, service calls or
restart in this helper; `ha core check` / Core restart are separate operations.
Source-local output is counts and verification facts, never household values.
"""
import argparse
import base64
import json
from pathlib import Path
import shlex
import subprocess

SOURCE=r'''
import base64,hashlib,json,os,stat,sys,tempfile,time
from pathlib import Path
from datetime import datetime,timezone
P=Path('/config/custom_components/aster_home_registry')
CP=Path('/config/aster-checkpoints/home-dashboard-20261026')
OLD='078ed576b4898765d61560644eca39137691f7f37ead942430c0a045fdf3f1e6'
CONTRACT='b6ba6d09f4d07864f005d134604ff9866f7ff982b6abdf9cc9f7d638132c1f3a'
mode=sys.argv[1];candidate=json.loads(base64.b64decode(sys.argv[2]))
def require(ok,code):
    if not ok:raise ValueError(code)
def digest(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_nlink==1,'exporter-file-type')
    return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,data):
    fd,tmp=tempfile.mkstemp(prefix='.aster-dashboard.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        os.chmod(tmp,0o600);os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
try:
    require(mode in ('prepare','verify','rollback'),'exporter-mode')
    require(set(candidate)=={'__init__.py','dashboard_contract.py'},'exporter-candidate-files')
    data={name:base64.b64decode(value) for name,value in candidate.items()}
    pins={name:hashlib.sha256(value).hexdigest() for name,value in data.items()}
    require(digest(P/'contract.py')==CONTRACT,'exporter-legacy-contract-drift')
    for name,value in data.items():compile(value,str(P/name),'exec')
    if mode=='prepare':
        require(digest(P/'__init__.py')==OLD,'exporter-predecessor-drift')
        require(not (P/'dashboard_contract.py').exists(),'exporter-new-file-exists')
        require(not Path('/share/aster-home-registry/dashboard.json').exists(),'exporter-report-already-exists')
        require(not CP.exists(),'exporter-checkpoint-already-exists')
        CP.mkdir(mode=0o700,parents=True)
        originals={'__init__.py':P/'__init__.py','contract.py':P/'contract.py',
            'configuration.yaml':Path('/config/configuration.yaml'),
            'legacy-home.json':Path('/share/aster-home-registry/latest.json'),
            'legacy-registry.json':Path('/share/aster-registry/latest.json')}
        backup={}
        for name,path in originals.items():
            wanted=digest(path);atomic(CP/name,path.read_bytes())
            require(digest(CP/name)==wanted,'exporter-checkpoint-copy')
            backup[name]=wanted
        for name in ('legacy-home.json','legacy-registry.json'):json.loads((CP/name).read_text())
        require(json.loads((CP/'legacy-home.json').read_text())['schema_version']==3,'exporter-legacy-schema')
        require(json.loads((CP/'legacy-registry.json').read_text())['schema_version']==1,'exporter-registry-schema')
        with tempfile.TemporaryDirectory(prefix='restore-',dir=CP) as folder:
            for name,wanted in backup.items():
                restored=Path(folder)/name;restored.write_bytes((CP/name).read_bytes())
                require(digest(restored)==wanted,'exporter-isolated-restore')
        record=dict(backup=backup,candidate=pins,prepared_at=time.time())
        atomic(CP/'state.json',json.dumps(record,sort_keys=True).encode())
        # No await/restart occurs between the two private atomic replacements.
        atomic(P/'dashboard_contract.py',data['dashboard_contract.py'])
        atomic(P/'__init__.py',data['__init__.py'])
    record=json.loads((CP/'state.json').read_text())
    require(record['candidate']==pins,'exporter-checkpoint-candidate-drift')
    for name,wanted in record['backup'].items():require(digest(CP/name)==wanted,'exporter-checkpoint-drift')
    require(digest(Path('/config/configuration.yaml'))==record['backup']['configuration.yaml'],'exporter-config-drift')
    for name,wanted in pins.items():require(digest(P/name)==wanted,'exporter-installed-code-drift')
    if mode=='rollback':
        atomic(P/'__init__.py',(CP/'__init__.py').read_bytes())
        # Retain the added module and report for recovery; restored legacy init
        # does not import it. Never restore old readings over current state.
        require(digest(P/'__init__.py')==OLD,'exporter-rollback-code')
    result=dict(passed=True,mode=mode,checkpoint_verified=True,isolated_restore_verified=True,
        configuration_unchanged=True,legacy_contract_unchanged=True,device_actions=False,credentials_added=False)
    if mode=='verify':
        report=Path('/share/aster-home-registry/dashboard.json')
        require(report.stat().st_size<=262144 and stat.S_IMODE(report.stat().st_mode)==0o600,'exporter-report-file')
        snapshot=json.loads(report.read_text())
        require(snapshot['schema_version']==4 and snapshot['snapshot_id']=='ha-home-dashboard-v4','exporter-new-schema')
        stamp=datetime.fromisoformat(snapshot['observed_at'])
        require(stamp.utcoffset() is not None and -10<=(datetime.now(timezone.utc)-stamp).total_seconds()<360,'exporter-report-age')
        rows=snapshot['entities'];require(isinstance(rows,list) and 0<len(rows)<=256,'exporter-report-rows')
        for path,schema in ((Path('/share/aster-home-registry/latest.json'),3),(Path('/share/aster-registry/latest.json'),1)):
            require(json.loads(path.read_text())['schema_version']==schema,'exporter-compatibility')
            require(stat.S_IMODE(path.stat().st_mode)==0o600,'exporter-compatibility-mode')
        result.update(counts={kind:sum(r['kind']==kind for r in rows) for kind in sorted({r['kind'] for r in rows})},
            unavailable=sum(r['availability']!='available' for r in rows),fresh_report=True)
    atomic(CP/(mode+'-proof.json'),json.dumps(result,sort_keys=True).encode())
    print(json.dumps(result))
except Exception as error:
    code=str(error)
    print(json.dumps(dict(passed=False,code=code if isinstance(error,ValueError) and code.startswith('exporter-') else type(error).__name__)))
    raise SystemExit(1)
'''

def command(mode):
    base=Path(__file__).parent/'custom_components/aster_home_registry'
    candidate={name:base64.b64encode((base/name).read_bytes()).decode() for name in ('__init__.py','dashboard_contract.py')}
    encoded=base64.b64encode(json.dumps(candidate).encode()).decode()
    if not SOURCE.isascii():raise ValueError('exporter-command-encoding')
    return shlex.join(['qm','guest','exec','103','--','docker','exec','homeassistant','python3','-c',SOURCE,mode,encoded])

def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('prepare','verify','rollback'))
    args=parser.parse_args()
    reply=subprocess.run(['ssh','-o','BatchMode=yes','proxmox',command(args.mode)],stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL,timeout=45,check=True)
    guest=json.loads(reply.stdout)
    if len(reply.stdout)>20000 or guest.get('out-truncated')!=0:raise ValueError('exporter-result-size')
    result=json.loads(guest.get('out-data','{}'))
    print(json.dumps(result))
    if guest.get('exitcode')!=0 or result.get('passed') is not True:raise SystemExit(1)

if __name__=='__main__':main()
