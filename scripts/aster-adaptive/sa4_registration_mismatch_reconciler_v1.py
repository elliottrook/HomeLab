"""Reconcile exact v9 registry mismatch after checkpoint but before claim."""
from __future__ import annotations
import fcntl, hashlib, json, os, stat, time
from pathlib import Path
import sa4_single_file_repair_contract_v1 as contract

PLAN_ID="sa4-canary-v2-third-repair-v1"
PLAN_SHA256="3eb9c300c636388212a25a9a9f13cdcc72c000a09a98781321d5e07f39e4a4ab"
GRANT_ID="sa4-canary-v2-fifth-grant-v1-20261106"
TARGET_SHA256="a9831e6295abd632ad0646b38a253fce71c29f76850d918d1761685c40824da0"
MEASURED_REGISTRATION="0f4eda2e26d75638388806d62a78e2bbb505cfcf0f6c209bc8623cc1096e13e1"
LEDGER_REGISTRATION="8e724aa0697c7108666253bb3d7d53e583aecf155406325623f3eb9a1922b717"
EVIDENCE=Path("/var/lib/aster/sa4/transaction-evidence-v6")
LEDGER=Path("/var/lib/aster/sa4/one-use-ledger-v6/records/sa4-canary-v2-fifth-grant-v1-20261106.json")
TARGET=Path("/var/lib/aster/sa4/canary-adapter-v2.json")
CHECKPOINT=Path("/var/lib/aster/sa4/checkpoints/sa4-canary-v2-third-repair-v1.original")
EXCHANGE=Path("/run/aster-sa4-observer-exchange")
LOCK=Path("/run/aster-sa4-operation.lock"); STOP=Path("/run/aster-sa4-emergency-stop")
RECEIPT=EVIDENCE/"registration-mismatch-reconciliation.json"

def _read(path,mode,maximum=65536):
    fd=os.open(path,os.O_RDONLY|getattr(os,"O_NOFOLLOW",0))
    try:
        s=os.fstat(fd); raw=os.read(fd,maximum+1)
        if not stat.S_ISREG(s.st_mode) or s.st_uid or s.st_gid or s.st_nlink!=1 or stat.S_IMODE(s.st_mode)!=mode or not 1<=len(raw)<=maximum or os.read(fd,1): raise ValueError("SA4 registration reconciliation custody changed")
        return raw
    finally: os.close(fd)
def _json(raw):
    pairs=json.loads(raw.decode(),object_pairs_hook=lambda v:v); value={}
    for k,v in pairs:
        if k in value: raise ValueError("SA4 registration reconciliation JSON ambiguous")
        value[k]=v
    if raw!=contract.canonical(value): raise ValueError("SA4 registration reconciliation JSON noncanonical")
    return value
def _dir(path,names):
    s=path.lstat()
    if not stat.S_ISDIR(s.st_mode) or stat.S_ISLNK(s.st_mode) or s.st_uid or s.st_gid or stat.S_IMODE(s.st_mode)!=0o700 or {p.name for p in path.iterdir()}!=set(names): raise ValueError("SA4 registration reconciliation directory changed")
    return s
def _control(path,expected):
    fd=os.open(path,os.O_RDWR|os.O_NOFOLLOW); s=os.fstat(fd); p=path.lstat()
    if (s.st_dev,s.st_ino)!=(p.st_dev,p.st_ino) or s.st_uid or s.st_gid or s.st_nlink!=1 or stat.S_IMODE(s.st_mode)!=0o600: raise ValueError("SA4 registration control custody changed")
    fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if os.read(fd,4097)!=expected: raise ValueError("SA4 registration control content changed")
    return fd,s
def reconcile(observed_epoch):
    if type(observed_epoch)is not int or observed_epoch<1: raise ValueError("SA4 registration reconciliation time changed")
    _dir(EVIDENCE,{"measurement.json","checkpoint.json"}); exchange_stat=_dir(EXCHANGE,set())
    measurement=_json(_read(EVIDENCE/"measurement.json",0o600)); checkpoint=_json(_read(EVIDENCE/"checkpoint.json",0o600)); ledger=_json(_read(LEDGER,0o600,16384))
    target=_read(TARGET,0o644,4096); saved=_read(CHECKPOINT,0o600,4096)
    if hashlib.sha256(target).hexdigest()!=TARGET_SHA256 or saved!=target or measurement.get("plan_sha256")!=PLAN_SHA256 or measurement.get("target_registration_sha256")!=MEASURED_REGISTRATION or measurement.get("repair_effects")!=0 or checkpoint.get("plan_sha256")!=PLAN_SHA256 or checkpoint.get("target_registration_sha256")!=MEASURED_REGISTRATION or checkpoint.get("checkpoint_created")is not True or checkpoint.get("grant_claimed")is not False or checkpoint.get("repair_effects")!=0 or ledger.get("grant_id")!=GRANT_ID or ledger.get("plan_sha256")!=PLAN_SHA256 or ledger.get("target_registration_sha256")!=LEDGER_REGISTRATION or ledger.get("state")!="ready" or ledger.get("use_count")!=0: raise ValueError("SA4 registration mismatch evidence changed")
    expected_lock=contract.canonical({"schema":"aster-sa4-operation-lock.v1","plan_id":PLAN_ID,"plan_sha256":PLAN_SHA256}); expected_stop=contract.canonical({"schema":"aster-sa4-emergency-stop.v1","plan_id":PLAN_ID,"plan_sha256":PLAN_SHA256,"state":"armed"})
    lock_fd=stop_fd=-1
    try:
        lock_fd,lock_stat=_control(LOCK,expected_lock); stop_fd,stop_stat=_control(STOP,expected_stop)
        receipt=contract.canonical({"schema":"aster-sa4-registration-mismatch-reconciliation.v1","observed_epoch":observed_epoch,"plan_id":PLAN_ID,"plan_sha256":PLAN_SHA256,"grant_id":GRANT_ID,"failure_class":"RUNNER_REGISTRY_ALIAS_MISMATCH","measurement_registration_sha256":MEASURED_REGISTRATION,"ledger_registration_sha256":LEDGER_REGISTRATION,"ledger_state":"ready","use_count":0,"checkpoint_created":True,"grant_claimed":False,"repair_effects":0,"observer_requests":0,"target_sha256":TARGET_SHA256,"checkpoint_sha256":TARGET_SHA256,"runtime_controls_released":True,"runtime_exchange_removed":True,"automatic_retry":False,"retained_evidence":True})
        for path,s in ((STOP,stop_stat),(LOCK,lock_stat)):
            p=path.lstat()
            if (p.st_dev,p.st_ino)!=(s.st_dev,s.st_ino): raise ValueError("SA4 registration control identity changed")
        if (EXCHANGE.lstat().st_dev,EXCHANGE.lstat().st_ino)!=(exchange_stat.st_dev,exchange_stat.st_ino): raise ValueError("SA4 exchange identity changed")
        EXCHANGE.rmdir()
        fd=os.open(RECEIPT,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        try: os.write(fd,receipt); os.fsync(fd)
        finally: os.close(fd)
        STOP.unlink(); LOCK.unlink(); return receipt
    finally:
        for fd in (stop_fd,lock_fd):
            if fd>=0: os.close(fd)
def main(args):
    if args: raise ValueError("SA4 registration reconciler accepts no arguments")
    os.write(1,reconcile(int(time.time()))); return 0
if __name__=="__main__":
    try: raise SystemExit(main(os.sys.argv[1:]))
    except (OSError,ValueError,RuntimeError,json.JSONDecodeError) as e: print(f"error: {e}",file=os.sys.stderr); raise SystemExit(1)
