"""HA-held machine identity publishes only the approved display report to HP.

No key values or household data appear in status/logs. No broker/administrator
credential on TV. Explicit opt-in marker; no network activity when disabled.
"""
import asyncio
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile

ROOT=Path('/config/.aster-home-delivery')
REPORT=Path('/share/aster-home-registry/dashboard.json')
COMMAND='aster-home-publish-v1'
MODEL_PIN=''
_lock=asyncio.Lock()

def require(ok):
    if not ok:raise ValueError('home-delivery-contract')
def private(path,directory=False):
    info=path.lstat()
    require(not path.is_symlink() and info.st_uid==os.getuid() and
        (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode) and info.st_nlink==1) and
        stat.S_IMODE(info.st_mode)==(0o700 if directory else 0o600))
    return info
def enabled():
    try:
        private(ROOT,True);private(ROOT/'enabled.json')
        return json.loads((ROOT/'enabled.json').read_text())==dict(enabled=True,interval_seconds=300,target='hp-only')
    except (OSError,ValueError):return False
def write_status(result):
    private(ROOT,True)
    path=ROOT/'health.json';previous={}
    if path.exists():private(path);previous=json.loads(path.read_text())
    if result.get('ok'):
        previous.update(last_success_at=result['checked_at'],last_source_at=result['source_at'],last_sha256=result['sha256'])
    previous.update(result)
    fd,tmp=tempfile.mkstemp(prefix='.health.',dir=ROOT)
    try:
        with os.fdopen(fd,'w') as stream:json.dump(previous,stream,sort_keys=True);stream.flush();os.fsync(stream.fileno())
        os.chmod(tmp,0o600);os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def read_source():
    private(ROOT,True)
    for name in ('id_ed25519','known_hosts','home_status_model.py'):private(ROOT/name)
    config=json.loads((ROOT/'identity.json').read_text())
    require(set(config)=={'model_sha256','hostkey_sha256','public_fingerprint'})
    private(ROOT/'identity.json')
    require(hashlib.sha256((ROOT/'home_status_model.py').read_bytes()).hexdigest()==config['model_sha256'])
    require(hashlib.sha256((ROOT/'known_hosts').read_bytes()).hexdigest()==config['hostkey_sha256'])
    spec=importlib.util.spec_from_file_location('aster_home_delivery_model',ROOT/'home_status_model.py')
    model=importlib.util.module_from_spec(spec);sys.modules[spec.name]=model;spec.loader.exec_module(model)
    before=private(REPORT);require(0<before.st_size<=262144)
    raw=REPORT.read_bytes();after=REPORT.stat()
    require(all(getattr(before,k)==getattr(after,k) for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')))
    require(model.view(raw).state=='fresh')
    return raw

async def publish(*_args):
    if not enabled():return dict(ok=False,code='disabled')
    if _lock.locked():return dict(ok=False,code='busy')
    async with _lock:
        checked=datetime.now(timezone.utc).isoformat()
        result=dict(ok=False,code='delivery-unavailable',checked_at=checked)
        try:
            raw=await asyncio.to_thread(read_source)
            import asyncssh
            async with asyncio.timeout(22):
                async with asyncssh.connect('192.168.1.140',port=22,username='root',
                    client_keys=[str(ROOT/'id_ed25519')],known_hosts=str(ROOT/'known_hosts'),
                    config=[],agent_path=None,preferred_auth=['publickey'],disable_trivial_auth=True,
                    connect_timeout=7,login_timeout=7) as connection:
                    reply=await connection.run(COMMAND,input=raw,encoding=None,timeout=12,check=False)
            require(reply.exit_status==0 and isinstance(reply.stdout,bytes) and len(reply.stdout)<=4096)
            ack=json.loads(reply.stdout)
            pin=hashlib.sha256(raw).hexdigest();snapshot=json.loads(raw)
            require(ack.get('ok') is True and ack.get('sha256')==pin and ack.get('source_at')==snapshot['observed_at'])
            result.update(ok=True,code='published',sha256=pin,source_at=ack['source_at'],readings=len(snapshot['entities']))
        except Exception:
            # All transport/auth/model failures remain fixed non-secret status.
            pass
        try:await asyncio.to_thread(write_status,result)
        except (OSError,ValueError):return dict(ok=False,code='health-write-failed')
        return result
