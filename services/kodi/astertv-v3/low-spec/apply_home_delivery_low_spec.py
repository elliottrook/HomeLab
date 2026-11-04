#!/usr/bin/env python3
"""Checkpoint and extend the HA display publisher to AsterTV-Jen via QGA."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import shlex
import subprocess


HERE = Path(__file__).resolve()
REPO = HERE.parents[4]
ACCEPTED = REPO / "services/kodi/astertv-v2/reconciliation/payload/home-delivery"
EXPECTED = {
    "delivery.py": "fd4c6c9b6ac1d70c0d67f480b7e3e087c851db47f8b91baf115e91f1f2a01df6",
    "known_hosts": "a36881ff9c8b32b5dc36b2ee21a50d5772ad638f72d999ad04f6e401d037eea6",
    "identity.json": "6dd95dd9de4bc91f73d00ca0f0eb703ac12871a39bed5601a43e4378627ede79",
    "enabled.json": "5f6638cfab9686aeab624f62ef11792fd12268dd29355102044774126a5e8e15",
}
JEN_HOSTKEY = (
    "192.168.1.180 ssh-ed25519 "
    "AAAAC3NzaC1lZDI1NTE5AAAAIELF5k/qf0Y3kAzuhO5AaHVa9yts8IzVc+ghUNixJHe6\n"
)

SOURCE = r'''
import asyncio,base64,hashlib,importlib.util,json,os,stat,sys,tempfile
from pathlib import Path
data={k:base64.b64decode(v) for k,v in json.loads(base64.b64decode(sys.argv[1])).items()}
expected=json.loads(base64.b64decode(sys.argv[2]))
root=Path('/config/.aster-home-delivery'); component=Path('/config/custom_components/aster_home_registry')
checkpoint=Path('/config/aster-checkpoints/home-delivery-low-spec-20261104')
paths={'delivery.py':component/'delivery.py','known_hosts':root/'known_hosts',
       'identity.json':root/'identity.json','enabled.json':root/'enabled.json','health.json':root/'health.json'}
def require(value,code):
    if not value:raise RuntimeError(code)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def private(path,directory=False):
    info=path.lstat();require(not path.is_symlink() and info.st_uid==os.getuid() and
        (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode) and info.st_nlink==1) and
        stat.S_IMODE(info.st_mode)==(0o700 if directory else 0o600),'low-spec-source-private')
def atomic(path,raw):
    fd,tmp=tempfile.mkstemp(prefix='.aster-low-spec.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.chmod(tmp,0o600);os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def load():
    spec=importlib.util.spec_from_file_location('aster_home_delivery_low_spec_runtime',component/'delivery.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);return module
try:
    require(set(data)=={'delivery.py','known_hosts'},'low-spec-source-arguments')
    private(root,True)
    for name,wanted in expected.items():require(sha(paths[name])==wanted,'low-spec-source-predecessor-'+name)
    compile(data['delivery.py'],'delivery.py','exec')
    known=data['known_hosts'].decode().splitlines()
    require(len(known)==3 and known[0].startswith('192.168.1.140 ssh-ed25519 ') and
            known[1].startswith('192.168.1.157 ssh-ed25519 ') and
            known[2].startswith('192.168.1.180 ssh-ed25519 '),'low-spec-source-hostkeys')
    require(not checkpoint.exists(),'low-spec-source-checkpoint-exists')
    checkpoint.mkdir(mode=0o700,parents=True)
    for name,path in paths.items():private(path);atomic(checkpoint/name,path.read_bytes())
    identity=json.loads(paths['identity.json'].read_text())
    require(set(identity)=={'model_sha256','hostkey_sha256','public_fingerprint'},'low-spec-source-identity')
    identity['hostkey_sha256']=hashlib.sha256(data['known_hosts']).hexdigest()
    try:
        atomic(paths['delivery.py'],data['delivery.py']);atomic(paths['known_hosts'],data['known_hosts'])
        atomic(paths['identity.json'],json.dumps(identity,sort_keys=True).encode())
        publication=asyncio.run(load().publish())
        require(publication.get('ok') is True and
                set(publication.get('targets',{}))=={'lab','production','low-spec'} and
                all(value.get('ok') is True for value in publication['targets'].values()),
                'low-spec-source-publication')
    except Exception:
        for name,path in paths.items():atomic(path,(checkpoint/name).read_bytes())
        raise
    result=dict(passed=True,checkpoint=str(checkpoint),private_key_unchanged=True,
                targets=sorted(publication['targets']),readings=publication.get('readings'),
                source_at=publication.get('source_at'),code=publication.get('code'))
    atomic(checkpoint/'apply-proof.json',json.dumps(result,sort_keys=True).encode())
    print(json.dumps(result))
except Exception as error:
    code=str(error);print(json.dumps(dict(passed=False,code=code if code.startswith('low-spec-') else type(error).__name__)))
    raise SystemExit(1)
'''


def main() -> None:
    delivery = (ACCEPTED / "delivery.py").read_text()
    assert hashlib.sha256(delivery.encode()).hexdigest() == EXPECTED["delivery.py"]
    delivery = delivery.replace(
        "TARGETS=(('lab','192.168.1.140'),('production','192.168.1.157'))",
        "TARGETS=(('lab','192.168.1.140'),('production','192.168.1.157'),('low-spec','192.168.1.180'))",
    ).replace(
        "set(targets)=={'lab','production'}",
        "set(targets)=={'lab','production','low-spec'}",
    ).replace("to the two named Aster clients", "to the three named Aster clients")
    assert delivery.count("192.168.1.180") == 1
    compile(delivery, "delivery.py", "exec")
    known_hosts = (ACCEPTED / "known_hosts").read_text() + JEN_HOSTKEY
    bundle = base64.b64encode(json.dumps({
        "delivery.py": base64.b64encode(delivery.encode()).decode(),
        "known_hosts": base64.b64encode(known_hosts.encode()).decode(),
    }).encode()).decode()
    expected = base64.b64encode(json.dumps(EXPECTED).encode()).decode()
    command = shlex.join(["qm", "guest", "exec", "103", "--", "docker", "exec",
                           "homeassistant", "python3", "-c", SOURCE, bundle, expected])
    reply = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "root@192.168.50.10", command],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=75, check=True,
    )
    guest = json.loads(reply.stdout)
    if guest.get("out-truncated") != 0 or guest.get("exitcode") != 0:
        print(guest.get("out-data", ""), end="")
        raise RuntimeError("low-spec-source-guest-failed")
    result = json.loads(guest.get("out-data", "{}"))
    print(json.dumps(result, sort_keys=True))
    if result.get("passed") is not True:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
