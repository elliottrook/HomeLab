"""Claim one reservation and execute the fixed Lab Hours transaction once."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from lab_hours_reservations import ReservationError, ReservationStore
from lab_hours_workloads import workload


PILOT = Path("/usr/local/libexec/local-ai-lease/full-inference-pilot")
STATE_ROOT = Path("/var/lib/local-ai-lab")
RESERVATIONS = STATE_ROOT / "reservations"
ATTEMPTS = STATE_ROOT / "lab-hours-attempts"
MANIFEST = PILOT / "lab_hours_release_manifest.json"
LOCAL_ZONE = ZoneInfo("America/Vancouver")
MODEL_SHA = "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13"
BINARY_SHA = "0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5"
UNIT_SHA = "a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3"
PROCESS_MARKERS = ("vzdump", "zstd -t", "f2_preflight", "f3_from_f2",
                   "stream_a_evaluation_evidence", "full_aster_first_screen",
                   "m3_joint_semantic_35b")
REGISTERED_RUNNER_KINDS = frozenset({
    "full-inference-pilot",
    "owner-loss-exercise",
    "sa3-expanded-quality",
    "m3-joint-semantic-35b",
})


class RunError(RuntimeError): pass


def call(command: tuple[str, ...], timeout: float = 30.0):
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)


def atomic_json(path: Path, value: dict[str, object]) -> None:
    tmp = path.with_suffix(f".tmp-{os.getpid()}")
    fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        os.write(fd, (json.dumps(value, sort_keys=True) + "\n").encode())
        os.fsync(fd)
    finally: os.close(fd)
    os.replace(tmp, path)


def load_manifest() -> dict[str, str]:
    st = MANIFEST.lstat()
    if (not MANIFEST.is_file() or MANIFEST.is_symlink() or st.st_uid != 0
            or st.st_nlink != 1 or st.st_size > 16_384):
        raise RunError("MANIFEST_CUSTODY_INVALID")
    value = json.loads(MANIFEST.read_text())
    pins = value.get("pins") if isinstance(value, dict) else None
    if not isinstance(pins, dict) or not pins:
        raise RunError("MANIFEST_INVALID")
    for name, expected in pins.items():
        path = PILOT / name
        if (not path.is_file() or path.is_symlink()
                or hashlib.sha256(path.read_bytes()).hexdigest() != expected):
            raise RunError(f"INSTALLED_PIN_DRIFT:{name}")
    return pins


def require_quiet() -> None:
    for path in (STATE_ROOT / "full-inference-drain.json",
                 STATE_ROOT / "full-inference-drain.lock",
                 Path("/run/local-ai-lab-operation.lock")):
        if path.exists(): raise RunError("SHARED_STATE_OR_LOCK_PRESENT")
    lease = call(("/usr/local/sbin/local-ai-lease", "status"), 10)
    try: lease_value = json.loads(lease.stdout)
    except json.JSONDecodeError: lease_value = None
    if lease.returncode != 0 or lease_value not in ("ready", {"state": "ready"}):
        raise RunError("LEASE_NOT_READY")
    for proc in Path("/proc").glob("[0-9]*"):
        if proc.name == str(os.getpid()): continue
        try: command = proc.joinpath("cmdline").read_bytes().replace(b"\0", b" ").decode()
        except (OSError, UnicodeDecodeError): continue
        marker = next((m for m in PROCESS_MARKERS if m in command), None)
        if marker: raise RunError(f"COMPETING_PROCESS:{marker}")


def commands(booking: dict[str, object], claimant: str, start: int):
    spec = workload(str(booking["workload"]))
    cycle = datetime.fromtimestamp(start, LOCAL_ZONE).strftime("%Y_%m_%d")
    owner_unit = f"aster-local-ai-pilot-owner-{claimant}.scope"
    guardian_unit = f"aster-local-ai-pilot-guardian-{claimant}.service"
    end = int(booking["end_epoch"])
    rescue = min(start + spec.rescue_after_seconds, end)
    hard = end + 900
    if spec.runner_kind == "m3-joint-semantic-35b":
        guardian_script = PILOT / "m3_joint_semantic_35b_guardian.py"
        guardian = ("systemd-run", "--quiet", "--collect", f"--unit={guardian_unit}",
            "--property=User=root", "--property=Restart=no", "/usr/bin/python3", "-B",
            str(guardian_script), "--owner-id", claimant, "--owner-unit", owner_unit,
            "--cycle", cycle, "--rescue-at", str(rescue),
            "--hard-deadline", str(hard), "--effect-authorized")
    else:
        guardian = ("systemd-run", "--quiet", "--collect", f"--unit={guardian_unit}",
            "--property=User=root", "--property=Restart=no", "/usr/bin/python3", "-B",
            str(PILOT / "full_inference_lab_deadline_guardian.py"), "--state-root", str(STATE_ROOT),
            "--owner-id", claimant, "--owner-unit", owner_unit, "--cycle", cycle,
            "--model-sha256", MODEL_SHA, "--binary-sha256", BINARY_SHA,
            "--unit-sha256", UNIT_SHA, "--rescue-at", str(rescue),
            "--hard-deadline", str(hard), "--effect-authorized")
    owner = ("systemd-run", "--quiet", "--collect", "--scope", f"--unit={owner_unit}",
        "/usr/bin/python3", "-B", str(PILOT / "full_inference_lab_runtime.py"),
        "--phase", "pilot", "--owner-id", claimant, "--owner-unit", owner_unit,
        "--admin-path-evidence", f"reserved:{booking['booking_id']}", "--cycle", cycle,
        "--session-start-epoch", str(start), "--model-sha256", MODEL_SHA,
        "--binary-sha256", BINARY_SHA, "--unit-sha256", UNIT_SHA,
        "--workload-profile", str(booking["workload"]),
        "--retain-root", str(ATTEMPTS / f"reservation-{booking['booking_id']}"),
        "--effect-authorized", "--news-overlap-authorized")
    return guardian_unit, owner_unit, guardian, owner


def postcheck(owner_unit: str) -> None:
    sys.path.insert(0, str(PILOT))
    from full_inference_lab_sources import AcceptedBaseline
    from full_inference_lab_validator import LocalProxmoxFullDrainValidator
    require_quiet()
    cycle = datetime.now(LOCAL_ZONE).strftime("%Y_%m_%d")
    def runner(command, timeout):
        result = call(tuple(command), timeout); return result.returncode, result.stdout
    validator = LocalProxmoxFullDrainValidator(
        runner, AcceptedBaseline(MODEL_SHA, BINARY_SHA, UNIT_SHA), cycle=cycle)
    if not validator(): raise RunError("PRODUCTION_RESTORATION_INVALID")
    if call(("systemctl", "is-active", owner_unit), 10).returncode == 0:
        raise RunError("OWNER_SCOPE_REMAINS_ACTIVE")


def settle_guardian(guardian_unit: str) -> None:
    """Remove the expected guardian from quiet-host checks after recovery."""
    if ((STATE_ROOT / "full-inference-drain.json").exists()
            or (STATE_ROOT / "full-inference-drain.lock").exists()):
        return
    call(("systemctl", "stop", guardian_unit), 30)
    call(("systemctl", "reset-failed", guardian_unit), 10)


def run(booking_id: str) -> int:
    started = int(time.time())
    claimant = f"lh-{hashlib.sha256(booking_id.encode()).hexdigest()[:20]}"
    store = ReservationStore(RESERVATIONS); phase = "claim"; restored = True
    evidence = ATTEMPTS / f"reservation-{booking_id}"
    guardian_unit = None
    try:
        if os.geteuid() != 0: raise RunError("ROOT_REQUIRED")
        booking = store.claim(booking_id, claimant=claimant)
        pins = load_manifest()
        spec = workload(str(booking.get("workload")))
        if spec.runner_kind not in REGISTERED_RUNNER_KINDS:
            raise RunError("WORKLOAD_RUNNER_NOT_REGISTERED")
        if evidence.exists(): raise RunError("ATTEMPT_ALREADY_EXISTS")
        evidence.mkdir(mode=0o700, parents=True)
        phase = "static-preflight"; require_quiet()
        start = int(time.time()) + 60
        guardian_unit, owner_unit, guardian, owner = commands(booking, claimant, start)
        atomic_json(evidence / "attempt.json", {"schema":"aster-lab-hours-booked-attempt.v1",
            "booking_id":booking_id,"claimant":claimant,"start_epoch":start,
            "end_epoch":booking["end_epoch"],"candidate_pins":pins})
        phase = "guardian-arm"
        if call(guardian, 30).returncode != 0: raise RunError("GUARDIAN_DID_NOT_ARM")
        phase = "owner-transaction"; restored = False
        if booking["workload"] == "accepted-9b-owner-loss-exercise-v1":
            process = subprocess.Popen(owner, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True)
            state_deadline = min(start + 180, int(booking["end_epoch"]))
            while time.time() <= state_deadline and not (STATE_ROOT/"full-inference-drain.json").exists():
                if process.poll() is not None: break
                time.sleep(1)
            if not (STATE_ROOT/"full-inference-drain.json").exists():
                process.terminate(); stdout,stderr=process.communicate(timeout=30)
                raise RunError("OWNER_LOSS_EXERCISE_NEVER_DRAINED")
            phase="owner-loss-fence"
            call(("systemctl","stop",owner_unit),30)
            stdout,stderr=process.communicate(timeout=60)
            deadline=int(booking["end_epoch"])+900
            while time.time() <= deadline and (STATE_ROOT/"full-inference-drain.json").exists():
                time.sleep(2)
            result=type("Result",(),{"returncode":0,"stdout":stdout,"stderr":stderr})()
            phase="guardian-recovery-postcheck"; postcheck(owner_unit); restored=True
            receipt={"effects":"guardian-rescued","receipt":{"exit_status":0,
                "profile":"accepted-9b-owner-loss-exercise-v1","request_count":0}}
        else:
            result = call(owner, max(60, int(booking["end_epoch"]) + 900 - int(time.time())))
            try: receipt=json.loads(result.stdout)
            except json.JSONDecodeError: receipt={}
        for name, content in (("owner.stdout", result.stdout), ("owner.stderr", result.stderr)):
            path=evidence/name; path.write_text(content); os.chmod(path,0o600)
        settle_guardian(guardian_unit)
        if result.returncode != 0:
            deadline = int(booking["end_epoch"]) + 900
            while time.time() <= deadline and (STATE_ROOT/"full-inference-drain.json").exists():
                time.sleep(5)
            postcheck(owner_unit); restored=True
            raise RunError("OWNER_TRANSACTION_FAILED_RESTORED")
        phase="production-postcheck"; postcheck(owner_unit); restored=True
        expected_requests=spec.request_count
        expected_effect=("guardian-rescued" if expected_requests==0 else
                         ("sa3-expanded-quality-complete"
                          if spec.runner_kind=="sa3-expanded-quality" else
                          ("m3-joint-semantic-public-complete"
                           if spec.runner_kind=="m3-joint-semantic-35b" else "pilot-complete")))
        receipt_body=receipt.get("receipt")
        receipt_valid=(isinstance(receipt_body,dict)
            and receipt_body.get("exit_status")==0
            and receipt_body.get("profile")==booking["workload"]
            and receipt_body.get("request_count")==expected_requests)
        if spec.runner_kind=="sa3-expanded-quality":
            receipt_valid=(receipt_valid
                and set(receipt)=={"effects","production_restored","receipt"}
                and set(receipt_body)=={"exit_status","profile","request_count",
                                        "prediction_sha256","error_count"}
                and receipt.get("production_restored") is True
                and receipt_body.get("error_count")==0
                and isinstance(receipt_body.get("prediction_sha256"),str)
                and len(receipt_body["prediction_sha256"])==64
                and all(c in "0123456789abcdef"
                        for c in receipt_body["prediction_sha256"]))
        elif spec.runner_kind=="m3-joint-semantic-35b":
            receipt_valid=(receipt_valid
                and set(receipt)=={"effects","production_restored","receipt"}
                and set(receipt_body)=={"exit_status","profile","request_count",
                                        "result_sha256","exact","public_pass"}
                and receipt.get("production_restored") is True
                and isinstance(receipt_body.get("result_sha256"),str)
                and len(receipt_body["result_sha256"])==64
                and all(c in "0123456789abcdef" for c in receipt_body["result_sha256"])
                and type(receipt_body.get("exact")) is int
                and 0 <= receipt_body["exact"] <= 24
                and type(receipt_body.get("public_pass")) is bool)
        elif set(receipt_body or {}) != {"exit_status","profile","request_count"}:
            receipt_valid=False
        if receipt.get("effects")!=expected_effect or not receipt_valid:
            raise RunError("OWNER_RECEIPT_INCOMPLETE")
        settle_guardian(guardian_unit)
        atomic_json(evidence/"terminal.json",{"schema":"aster-lab-hours-booked-result.v1",
            "state":"complete","booking_id":booking_id,"started_epoch":started,
            "finished_epoch":int(time.time()),"request_count":expected_requests,
            "workload":booking["workload"],"production_restored":True})
        store.finish(booking_id,claimant=claimant,success=True,result_code="COMPLETE")
        return 0
    except BaseException as exc:
        if (restored and guardian_unit
                and not (STATE_ROOT / "full-inference-drain.json").exists()
                and not (STATE_ROOT / "full-inference-drain.lock").exists()):
            call(("systemctl", "stop", guardian_unit), 30)
            call(("systemctl", "reset-failed", guardian_unit), 10)
        evidence.mkdir(mode=0o700,parents=True,exist_ok=True)
        code=str(exc) if isinstance(exc,(RunError,ReservationError)) else type(exc).__name__
        atomic_json(evidence/"terminal.json",{"schema":"aster-lab-hours-booked-result.v1",
            "state":"no_go","booking_id":booking_id,"started_epoch":started,
            "finished_epoch":int(time.time()),"first_failure_phase":phase,
            "failure_code":code,"production_restored":restored})
        try: store.finish(booking_id,claimant=claimant,success=False,result_code="NO_GO")
        except ReservationError: pass
        return 1


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--booking-id",required=True)
    return run(p.parse_args().booking_id)


if __name__=="__main__": raise SystemExit(main())
