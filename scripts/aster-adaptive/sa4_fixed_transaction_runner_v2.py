"""Fixed no-argument entry point for one SA4 canary transaction."""
from __future__ import annotations
import hashlib, os, stat, sys, time
from pathlib import Path
import sa4_authenticated_authority_v1 as authority
import sa4_observer_file_exchange_v1 as exchange
import sa4_one_shot_transaction_controller_v2 as controller
import sa4_one_use_grant_ledger_v1 as ledger_module
import sa4_root_transaction_owner_v2 as root_owner
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry

INPUT_DIR=Path("/var/lib/aster/sa4/transaction-input-v1")
EVIDENCE_DIR=Path("/var/lib/aster/sa4/transaction-evidence-v1")
LEDGER_ROOT=Path("/var/lib/aster/sa4/one-use-ledger")
EXPECTED_UID=0
OPERATION_ID="sa4-canary-first-operation-v1"
FILES=("plan","approval","approval_proof","grant","grant_proof","candidate")
EVIDENCE_NAMES=frozenset({
    "measurement","checkpoint","source","claim","admission","terminal",
    "postcheck","postcheck_proof","rollback_terminal","rollback_receipt",
    "rollback_proof","reconciliation",
})
SUCCESS_EVIDENCE=frozenset({
    "measurement","checkpoint","source","claim","admission","terminal",
    "postcheck","postcheck_proof","reconciliation",
})
ROLLBACK_EVIDENCE=SUCCESS_EVIDENCE|frozenset({
    "rollback_terminal","rollback_receipt","rollback_proof",
})

def _directory(path,create=False):
    if create: path.mkdir(mode=0o700,parents=True,exist_ok=True)
    data=path.lstat()
    if not stat.S_ISDIR(data.st_mode) or stat.S_ISLNK(data.st_mode) or data.st_uid!=EXPECTED_UID or stat.S_IMODE(data.st_mode)!=0o700:
        raise ValueError("SA4 runner directory custody changed")

def _read(name,max_bytes=65536):
    path=INPUT_DIR/name
    fd=os.open(path,os.O_RDONLY|getattr(os,"O_NOFOLLOW",0))
    try:
        data=os.fstat(fd); raw=os.read(fd,max_bytes+1)
        if not stat.S_ISREG(data.st_mode) or data.st_uid!=EXPECTED_UID or stat.S_IMODE(data.st_mode)!=0o600 or data.st_nlink!=1 or not 1<=len(raw)<=max_bytes:
            raise ValueError("SA4 runner input custody changed")
        return raw
    finally: os.close(fd)

def _write_evidence(name,raw):
    if name not in EVIDENCE_NAMES or not isinstance(raw,bytes) or not raw:
        raise ValueError("SA4 runner evidence changed")
    path=EVIDENCE_DIR/f"{name}.json"
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,"O_NOFOLLOW",0),0o600)
    try: os.write(fd,raw); os.fsync(fd)
    finally: os.close(fd)
    directory=os.open(EVIDENCE_DIR,os.O_RDONLY)
    try: os.fsync(directory)
    finally: os.close(directory)

def _write_result(raw):
    path=EVIDENCE_DIR/"terminal-result.json"
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,"O_NOFOLLOW",0),0o600)
    try: os.write(fd,raw); os.fsync(fd)
    finally: os.close(fd)
    directory=os.open(EVIDENCE_DIR,os.O_RDONLY)
    try: os.fsync(directory)
    finally: os.close(directory)

def _require_evidence(branch,result_sha256):
    expected=(SUCCESS_EVIDENCE if branch=="postcheck-complete"
              else ROLLBACK_EVIDENCE if branch=="rollback" else None)
    if expected is None or set(path.stem for path in EVIDENCE_DIR.iterdir())!=expected:
        raise ValueError("SA4 runner retained evidence set changed")
    for name in expected:
        path=EVIDENCE_DIR/f"{name}.json"; data=path.lstat()
        if (not stat.S_ISREG(data.st_mode) or stat.S_ISLNK(data.st_mode)
                or data.st_uid!=EXPECTED_UID or stat.S_IMODE(data.st_mode)!=0o600
                or data.st_nlink!=1 or not 1<=data.st_size<=65536):
            raise ValueError("SA4 runner retained evidence custody changed")
    reconciliation=(EVIDENCE_DIR/"reconciliation.json").read_bytes()
    if hashlib.sha256(reconciliation).hexdigest()!=result_sha256:
        raise ValueError("SA4 runner reconciliation evidence changed")

def _close_exchange(count):
    rows=[]
    for sequence in range(1,count+1):
        request=exchange.EXCHANGE_DIR/f"request-{sequence}.json"
        response=exchange.EXCHANGE_DIR/f"response-{sequence}.signature"
        request_raw=request.read_bytes(); exchange.validate_statement(request_raw)
        signature=exchange._read_signature(response)
        rows.append({"sequence":sequence,"request_sha256":hashlib.sha256(request_raw).hexdigest(),"response_sha256":hashlib.sha256((signature+"\n").encode()).hexdigest()})
    for sequence in range(1,count+1):
        (exchange.EXCHANGE_DIR/f"response-{sequence}.signature").unlink()
        (exchange.EXCHANGE_DIR/f"request-{sequence}.json").unlink()
    exchange.EXCHANGE_DIR.rmdir()
    return rows

def execute(now_epoch:int):
    if type(now_epoch) is not int or now_epoch<1: raise ValueError("SA4 runner time changed")
    _directory(INPUT_DIR); _directory(EVIDENCE_DIR,True)
    values={name:_read(name,4096 if name=="candidate" else 65536) for name in FILES}
    plan=contract.validate_plan(values["plan"]); grant=contract.decode_unique_json(values["grant"])
    authenticated=authority.verify(values["plan"],values["approval"],values["approval_proof"],values["grant"],values["grant_proof"],now_epoch)
    if authenticated["grant_id"]!=grant["grant_id"] or now_epoch+8>=grant["expires_epoch"] or hashlib.sha256(values["candidate"]).hexdigest()!=plan["change"]["artifact_sha256"]:
        raise ValueError("SA4 runner authority or candidate changed")
    target=registry.resolve_production(plan["target_id"])
    ledger=ledger_module.OneUseLedger(LEDGER_ROOT,expected_uid=EXPECTED_UID)
    ledger.initialize(grant_id=grant["grant_id"],plan_sha256=hashlib.sha256(values["plan"]).hexdigest(),grant_sha256=hashlib.sha256(values["grant"]).hexdigest(),target_registration_sha256=registry.registration_sha256(target),target_sha256=plan["precondition"]["expected_sha256"],now_epoch=now_epoch,expires_epoch=grant["expires_epoch"])
    exchange.EXCHANGE_DIR.mkdir(mode=0o700)
    owner=root_owner.RootTransactionOwner(ledger,operation_id=OPERATION_ID)
    sequence=0
    def sign(statement):
        nonlocal sequence; sequence+=1
        return exchange.request_signature(statement,sequence)
    epochs={"measurement":now_epoch,"checkpoint":now_epoch+1,"claim":now_epoch+2,"claim_deadline":min(now_epoch+600,grant["expires_epoch"]),"effect":now_epoch+3,"observation":now_epoch+4,"rollback":now_epoch+5,"rollback_observation":now_epoch+6,"finish":now_epoch+7}
    result=controller.run(owner,{name:values[name] for name in ("plan","approval","approval_proof","grant","grant_proof")},values["candidate"],epochs,observer_signer=sign,evidence_writer=_write_evidence)
    if result.get("observer_signatures")!=sequence or sequence not in (1,2):
        raise ValueError("SA4 runner observer sequence changed")
    _require_evidence(result.get("branch"),result.get("terminal_result_sha256"))
    exchange_rows=_close_exchange(sequence)
    terminal=contract.canonical({**result,"grant_id":grant["grant_id"],"plan_sha256":hashlib.sha256(values["plan"]).hexdigest(),"signatures_requested":sequence,"exchange_evidence":exchange_rows,"runtime_exchange_removed":True,"evidence_retained":True})
    _write_result(terminal)
    return contract.decode_unique_json(terminal)

def main(arguments):
    if arguments: raise ValueError("SA4 runner accepts no arguments")
    execute(int(time.time())); return 0

if __name__=="__main__":
    try: raise SystemExit(main(sys.argv[1:]))
    except (OSError,ValueError,RuntimeError) as error:
        print(f"error: {error}",file=sys.stderr); raise SystemExit(1)
