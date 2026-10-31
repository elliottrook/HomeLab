#!/usr/bin/env python3
"""Checkpoint and activate the two-client HA display publisher through QGA."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import shlex
import subprocess


PAYLOAD = Path(__file__).resolve().parent / "payload/home-delivery"
EXPECTED = {
    "delivery.py": "9d62762e8ef768d781a1e078088fdf72c55cce631496086a47d2a210682a44b2",
    "known_hosts": "d3e5303537c779453a65785680ec89fdec73581d37c0de2a5a5e3963ba46786a",
    "identity.json": "4a30622fecc79ae463d906647f4bc6b7bab2824e48e5eefe0ac8418c8fb4ef78",
    "enabled.json": "7419a9ad92261b7f2a82113e8358e022581000cf2df15a2da61144e8101ce44d",
}
SOURCE = r'''
import asyncio,base64,hashlib,importlib.util,json,os,stat,sys,tempfile
from pathlib import Path
mode=sys.argv[1];data={k:base64.b64decode(v) for k,v in json.loads(base64.b64decode(sys.argv[2])).items()}
root=Path('/config/.aster-home-delivery'); component=Path('/config/custom_components/aster_home_registry')
checkpoint=Path('/config/aster-checkpoints/home-delivery-prod-20261030')
expected=json.loads(base64.b64decode(sys.argv[3]))
paths={'delivery.py':component/'delivery.py','known_hosts':root/'known_hosts',
       'identity.json':root/'identity.json','enabled.json':root/'enabled.json','health.json':root/'health.json'}
def require(value,code):
    if not value:raise RuntimeError(code)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def private(path,directory=False):
    info=path.lstat();require(not path.is_symlink() and info.st_uid==os.getuid() and
        (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode) and info.st_nlink==1) and
        stat.S_IMODE(info.st_mode)==(0o700 if directory else 0o600),'dual-source-private')
def atomic(path,raw):
    fd,tmp=tempfile.mkstemp(prefix='.aster-dual.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.chmod(tmp,0o600);os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def load():
    spec=importlib.util.spec_from_file_location('aster_home_delivery_dual_runtime',component/'delivery.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);return module
try:
    require(mode=='apply' and set(data)=={'delivery.py','known_hosts'},'dual-source-arguments')
    private(root,True)
    for name,wanted in expected.items():require(sha(paths[name])==wanted,'dual-source-predecessor-'+name)
    compile(data['delivery.py'],'delivery.py','exec')
    known=data['known_hosts'].decode().splitlines()
    require(len(known)==2 and known[0].startswith('192.168.1.140 ssh-ed25519 ') and
            known[1].startswith('192.168.1.157 ssh-ed25519 '),'dual-source-hostkeys')
    if not checkpoint.exists():
        checkpoint.mkdir(mode=0o700,parents=True)
        for name,path in paths.items():atomic(checkpoint/name,path.read_bytes())
    else:
        private(checkpoint,True)
        for name,path in paths.items():
            private(checkpoint/name)
            if name!='health.json':
                require((checkpoint/name).read_bytes()==path.read_bytes(),'dual-source-checkpoint-drift')
    with tempfile.TemporaryDirectory(prefix='restore-',dir=checkpoint) as folder:
        for name in paths:
            restored=Path(folder)/name;restored.write_bytes((checkpoint/name).read_bytes())
            require(hashlib.sha256(restored.read_bytes()).digest()==hashlib.sha256((checkpoint/name).read_bytes()).digest(),
                    'dual-source-isolated-restore')
    identity=json.loads(paths['identity.json'].read_text())
    require(set(identity)=={'model_sha256','hostkey_sha256','public_fingerprint'},'dual-source-identity')
    identity['hostkey_sha256']=hashlib.sha256(data['known_hosts']).hexdigest()
    enabled=dict(enabled=True,interval_seconds=300,target='aster-clients')
    try:
        atomic(paths['delivery.py'],data['delivery.py']);atomic(paths['known_hosts'],data['known_hosts'])
        atomic(paths['identity.json'],json.dumps(identity,sort_keys=True).encode())
        atomic(paths['enabled.json'],json.dumps(enabled,sort_keys=True).encode())
        publication=asyncio.run(load().publish())
        if not (publication.get('ok') is True and set(publication.get('targets',{}))=={'lab','production'} and
                all(value.get('ok') is True for value in publication['targets'].values())):
            states={name:value.get('code') for name,value in publication.get('targets',{}).items()}
            raise RuntimeError('dual-source-publication-'+json.dumps(states,sort_keys=True,separators=(',',':')))
    except Exception:
        for name,path in paths.items():atomic(path,(checkpoint/name).read_bytes())
        raise
    result=dict(passed=True,checkpoint=str(checkpoint),private_key_unchanged=True,
                targets=sorted(publication['targets']),readings=publication.get('readings'),
                source_at=publication.get('source_at'),code=publication.get('code'))
    atomic(checkpoint/'apply-proof.json',json.dumps(result,sort_keys=True).encode())
    print(json.dumps(result))
except Exception as error:
    code=str(error);print(json.dumps(dict(passed=False,code=code if code.startswith('dual-source-') else type(error).__name__)))
    raise SystemExit(1)
'''


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    delivery = PAYLOAD / "delivery.py"
    known_hosts = PAYLOAD / "known_hosts"
    compile(delivery.read_bytes(), str(delivery), "exec")
    bundle = base64.b64encode(json.dumps({
        "delivery.py": base64.b64encode(delivery.read_bytes()).decode(),
        "known_hosts": base64.b64encode(known_hosts.read_bytes()).decode(),
    }).encode()).decode()
    expected = base64.b64encode(json.dumps(EXPECTED).encode()).decode()
    command = shlex.join(["qm", "guest", "exec", "103", "--", "docker", "exec",
                           "homeassistant", "python3", "-c", SOURCE, "apply", bundle, expected])
    reply = subprocess.run(["ssh", "-o", "BatchMode=yes", "root@192.168.50.10", command],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=75, check=True)
    if len(reply.stdout) > 16000:
        raise RuntimeError("dual-source-result-size")
    guest = json.loads(reply.stdout)
    if guest.get("out-truncated") != 0 or guest.get("exitcode") != 0:
        print(guest.get("out-data", ""), end="")
        raise RuntimeError("dual-source-guest-failed")
    result = json.loads(guest.get("out-data", "{}"))
    print(json.dumps(result, sort_keys=True))
    if result.get("passed") is not True:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
