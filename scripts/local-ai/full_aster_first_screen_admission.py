"""Build and write the workload-specific full-Aster first-screen admission."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat


PATH = Path("/var/lib/local-ai-lab/full-aster-first-screen-admission.json")
SCHEMA = "aster-full-path-first-screen-admission.v1"
CONTRACT_SHA256 = "023939fd25e61e47af9418387ee6fe82163fac394511472a8bf64eaaab40382c"
ARTIFACT_SHA256 = "671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7"
ARTIFACT_BYTES = 20_419_565_568
BASELINE_MODEL_SHA256 = "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13"
RUNTIME_SHA256 = "0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5"
UNIT_SHA256 = "a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3"
_LEASE = re.compile(r"^aster-full-screen-owner-[0-9a-f]{16}:[0-9]+$")


class AdmissionError(ValueError): pass


def _canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(",",":"))+"\n").encode()


def build(*, cycle_date: str, lease_id: str, created_epoch: int,
          expires_epoch: int, f2_bytes: bytes, f3_bytes: bytes,
          f4_bytes: bytes, f5_bytes: bytes) -> dict[str, object]:
    if (not re.fullmatch(r"20[0-9]{2}-[01][0-9]-[0-3][0-9]",cycle_date)
            or _LEASE.fullmatch(lease_id) is None
            or type(created_epoch) is not int or type(expires_epoch) is not int
            or not created_epoch < expires_epoch <= created_epoch+900
            or any(not isinstance(raw,bytes) or not raw for raw in
                   (f2_bytes,f3_bytes,f4_bytes,f5_bytes))):
        raise AdmissionError("first-screen admission inputs are invalid")
    try:
        f4=json.loads(f4_bytes); f5=json.loads(f5_bytes)
    except (UnicodeError,json.JSONDecodeError) as error:
        raise AdmissionError("F4/F5 bytes are invalid") from error
    digests={name:hashlib.sha256(raw).hexdigest() for name,raw in
             (("f2",f2_bytes),("f3",f3_bytes),("f4",f4_bytes),("f5",f5_bytes))}
    if (f4.get("receipt",{}).get("lease_id")!=lease_id
            or f4.get("receipt",{}).get("generation")!=1
            or f5.get("f2_result_sha256")!=digests["f2"]
            or f5.get("f3_receipt_sha256")!=digests["f3"]
            or f5.get("f4_receipt_sha256")!=digests["f4"]):
        raise AdmissionError("F2-F5 cross-binding is invalid")
    return {"schema":SCHEMA,"cycle_date":cycle_date,"lease_id":lease_id,
        "generation":1,"created_epoch":created_epoch,"expires_epoch":expires_epoch,
        "evidence_sha256":digests,"contract_sha256":CONTRACT_SHA256,
        "artifact":{"sha256":ARTIFACT_SHA256,"bytes":ARTIFACT_BYTES,
                    "host_root_custody":True,"read_only_guest_mount":True},
        "baseline":{"model_sha256":BASELINE_MODEL_SHA256,
                    "runtime_sha256":RUNTIME_SHA256,"unit_sha256":UNIT_SHA256},
        "workload":{"name":"qwen36-35b-first-screen","requests":2,
                    "timeout_seconds_each":60,"reasoning":"on",
                    "speculation":"off","retries":0},
        "live_effect_authorized":False,"authority":"external-owner-approval-required"}


def write_new(value: dict[str,object], path: Path=PATH) -> str:
    if os.geteuid()!=0 or os.path.lexists(path): raise AdmissionError("admission target is not new")
    parent=path.parent.stat()
    if parent.st_uid!=0 or stat.S_IMODE(parent.st_mode)!=0o700:
        raise AdmissionError("admission parent custody is weak")
    raw=_canonical(value)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,"O_NOFOLLOW",0),0o600)
    with os.fdopen(fd,"wb") as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return hashlib.sha256(raw).hexdigest()
