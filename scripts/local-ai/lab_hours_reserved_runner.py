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
                   "m3_joint_semantic_35b", "sa3_candidate_i",
                   "sa3_candidate_j", "aster_tts_dual_cpu", "aster_tts_single_cpu",
                   "b60_musetalk_xpu_guest", "m3_k2", "m3_k3")
REGISTERED_RUNNER_KINDS = frozenset({
    "b60-entry-rescue-card",
    "b60-exclusive-card-capture",
    "b60-post-xe-card-r5",
    "b60-post-xe-card",
    "full-inference-pilot",
    "owner-loss-exercise",
    "sa3-expanded-quality",
    "sa3-evidence-envelope-quality",
    "sa3-evidence-envelope-candidate-i-quality",
    "sa3-evidence-matrix-candidate-j-public",
    "sa3-evidence-matrix-candidate-j-quality",
    "m3-joint-semantic-35b",
    "ebook-word-alignment",
    "aster-tts-dual-cpu-screen",
    "aster-tts-single-cpu-screen",
    "aster-news-video-musetalk-xpu",
    "m3-k2-shortlist-arbitration-development",
    "m3-k3-hierarchical-safety-development",
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


def commands(booking: dict[str, object], claimant: str, start: int, evidence: Path):
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
        "--retain-root", str(evidence),
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


def bounded_owner_failure(raw: str) -> str | None:
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    required = {"schema", "state", "failure_code", "production_restored"}
    if (not isinstance(value, dict) or not required.issubset(value)
            or value.get("schema") != "aster-m3-joint-semantic-35b-transaction-failure.v1"
            or value.get("state") != "failed"
            or value.get("production_restored") is not True
            or value.get("failure_code") not in {
                "M3_GUEST_WORKLOAD_FAILED", "M3_GUEST_FAILURE_UNAVAILABLE",
                "M3_PUBLIC_QUALITY_GATE_FAILED"}):
        return None
    if value["failure_code"] == "M3_GUEST_FAILURE_UNAVAILABLE":
        return value["failure_code"]
    if value["failure_code"] == "M3_PUBLIC_QUALITY_GATE_FAILED":
        detail_keys = {"exact", "unsafe_false_routes",
                       "routed_privacy_underclassifications",
                       "result_sha256", "result_bytes"}
        if (not detail_keys.issubset(value)
                or type(value["exact"]) is not int
                or not 0 <= value["exact"] <= 24
                or type(value["unsafe_false_routes"]) is not int
                or not 0 <= value["unsafe_false_routes"] <= 24
                or type(value["routed_privacy_underclassifications"]) is not int
                or not 0 <= value["routed_privacy_underclassifications"] <= 24
                or not isinstance(value["result_sha256"], str)
                or len(value["result_sha256"]) != 64
                or any(c not in "0123456789abcdef" for c in value["result_sha256"])
                or type(value["result_bytes"]) is not int
                or not 1 <= value["result_bytes"] <= 262144):
            return None
        return (f"M3_PUBLIC_QUALITY_GATE_FAILED_EXACT_{value['exact']}"
                f"_UNSAFE_{value['unsafe_false_routes']}"
                f"_PRIVACY_{value['routed_privacy_underclassifications']}")
    detail_keys = {"guest_failure_code", "attempted", "valid", "first_record_failure"}
    if (not detail_keys.issubset(value)
            or value["guest_failure_code"] not in {
                "M3_PUBLIC_RESULT_INCOMPLETE", "M3_GUEST_INPUT_OR_IO_FAILED"}
            or type(value["attempted"]) is not int
            or type(value["valid"]) is not int
            or not 0 <= value["valid"] <= value["attempted"] <= 24
            or value["first_record_failure"] not in {
                "invalid_response", "engine_error", "http_4xx", "http_5xx",
                "none", "unknown"}):
        return None
    return (f"M3_GUEST_WORKLOAD_FAILED_{value['first_record_failure'].upper()}"
            f"_ATTEMPTED_{value['attempted']}_VALID_{value['valid']}")


def run(booking_id: str, *, retry: bool = False) -> int:

    # A registered exclusive-card booking is dispatched by its exact future
    # clock. The qualified inner controller remains its ONLY ledger claimant.
    # Never import that controller here: shared module names must stay isolated.
    if os.geteuid() == 0:
        try:
            exclusive = ReservationStore(RESERVATIONS).get(booking_id)
        except Exception:
            exclusive = None
        if exclusive is not None and exclusive.get('workload') == 'b60-entry-backend-preservation-qualification-v1':
            try:
                if retry:
                    raise RunError('EXCLUSIVE_CARD_NOT_RETRYABLE')
                load_manifest()
                from lab_hours_workloads import validate_registry, validate_inactive_target
                validate_registry()
                validate_inactive_target(PILOT, workload_id='b60-entry-backend-preservation-qualification-v1')
                from b60_entry_rescue_card_bridge import dispatch
                return dispatch(exclusive, workload('b60-entry-backend-preservation-qualification-v1'))
            except Exception:
                print(json.dumps({'state':'dispatch-refused','booking_id':booking_id,
                    'workload':'b60-entry-backend-preservation-qualification-v1',
                    'qualification_claimed':False},sort_keys=True))
                return 1

    # A registered exclusive-card booking is dispatched by its exact future
    # clock. The qualified inner controller remains its ONLY ledger claimant.
    # Never import that controller here: shared module names must stay isolated.
    if os.geteuid() == 0:
        try:
            exclusive = ReservationStore(RESERVATIONS).get(booking_id)
        except Exception:
            exclusive = None
        if exclusive is not None and exclusive.get('workload') == 'b60-qwen36-35b-failure-capture-v1':
            try:
                if retry:
                    raise RunError('EXCLUSIVE_CARD_NOT_RETRYABLE')
                load_manifest()
                from lab_hours_workloads import validate_registry, validate_inactive_target
                validate_registry()
                validate_inactive_target(PILOT, workload_id='b60-qwen36-35b-failure-capture-v1')
                from b60_exclusive_card_bridge import dispatch
                return dispatch(exclusive, workload('b60-qwen36-35b-failure-capture-v1'))
            except Exception:
                print(json.dumps({'state':'dispatch-refused','booking_id':booking_id,
                    'workload':'b60-qwen36-35b-failure-capture-v1',
                    'qualification_claimed':False},sort_keys=True))
                return 1

    # A registered exclusive-card booking is dispatched by its exact future
    # clock. The qualified inner controller remains its ONLY ledger claimant.
    # Never import that controller here: shared module names must stay isolated.
    if os.geteuid() == 0:
        try:
            exclusive = ReservationStore(RESERVATIONS).get(booking_id)
        except Exception:
            exclusive = None
        if exclusive is not None and exclusive.get('workload') == 'b60-accepted-sycl-post-xe-qualification-v2':
            try:
                if retry:
                    raise RunError('EXCLUSIVE_CARD_NOT_RETRYABLE')
                load_manifest()
                from lab_hours_workloads import validate_registry, validate_inactive_target
                validate_registry()
                validate_inactive_target(PILOT, workload_id='b60-accepted-sycl-post-xe-qualification-v2')
                from b60_post_xe_r5_card_bridge import dispatch
                return dispatch(exclusive, workload('b60-accepted-sycl-post-xe-qualification-v2'))
            except Exception:
                print(json.dumps({'state':'dispatch-refused','booking_id':booking_id,
                    'workload':'b60-accepted-sycl-post-xe-qualification-v2',
                    'qualification_claimed':False},sort_keys=True))
                return 1

    # A registered exclusive-card booking is dispatched by its exact future
    # clock. The qualified inner controller remains its ONLY ledger claimant.
    # Never import that controller here: shared module names must stay isolated.
    if os.geteuid() == 0:
        try:
            exclusive = ReservationStore(RESERVATIONS).get(booking_id)
        except Exception:
            exclusive = None
        if exclusive is not None and exclusive.get('workload') == 'b60-accepted-sycl-post-xe-qualification-v1':
            try:
                if retry:
                    raise RunError('EXCLUSIVE_CARD_NOT_RETRYABLE')
                load_manifest()
                from lab_hours_workloads import validate_registry, validate_inactive_target
                validate_registry()
                validate_inactive_target(PILOT, workload_id='b60-accepted-sycl-post-xe-qualification-v1')
                from b60_post_xe_card_bridge import dispatch
                return dispatch(exclusive, workload('b60-accepted-sycl-post-xe-qualification-v1'))
            except Exception:
                print(json.dumps({'state':'dispatch-refused','booking_id':booking_id,
                    'workload':'b60-accepted-sycl-post-xe-qualification-v1',
                    'qualification_claimed':False},sort_keys=True))
                return 1
    started = int(time.time())
    claimant = f"lh-{hashlib.sha256(booking_id.encode()).hexdigest()[:20]}"
    store = ReservationStore(RESERVATIONS); phase = "claim"; restored = True
    evidence = ATTEMPTS / f"reservation-{booking_id}-pending"
    guardian_unit = None
    booking = None
    spec = None
    admitted = False
    try:
        if os.geteuid() != 0: raise RunError("ROOT_REQUIRED")
        booking = (store.start_retry(booking_id, claimant=claimant) if retry
                   else store.claim(booking_id, claimant=claimant))
        admitted = True
        pins = load_manifest()
        spec = workload(str(booking.get("workload")))
        attempt_number = int(booking.get("current_attempt", 1))
        evidence = ATTEMPTS / f"reservation-{booking_id}-attempt-{attempt_number}"
        if spec.runner_kind not in REGISTERED_RUNNER_KINDS:
            raise RunError("WORKLOAD_RUNNER_NOT_REGISTERED")
        if spec.runner_kind in {"ebook-word-alignment", "aster-tts-dual-cpu-screen",
                                "aster-tts-single-cpu-screen",
                                "aster-news-video-musetalk-xpu",
                                "m3-k2-shortlist-arbitration-development",
                                "m3-k3-hierarchical-safety-development"}:
            if booking.get("owner") != spec.owner:
                raise RunError("WORKLOAD_OWNER_MISMATCH")
            if int(booking["end_epoch"]) - int(booking["start_epoch"]) < spec.minimum_booking_seconds:
                raise RunError("WORKLOAD_WINDOW_TOO_SHORT")
        if evidence.exists(): raise RunError("ATTEMPT_ALREADY_EXISTS")
        evidence.mkdir(mode=0o700, parents=True)
        phase = "static-preflight"; require_quiet()
        start = int(time.time()) + 60
        guardian_unit, owner_unit, guardian, owner = commands(booking, claimant, start, evidence)
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
            measured = bounded_owner_failure(result.stdout)
            raise RunError(measured or "OWNER_TRANSACTION_FAILED_RESTORED")
        phase="production-postcheck"; postcheck(owner_unit); restored=True
        expected_requests=spec.request_count
        expected_effect=("guardian-rescued" if expected_requests==0 else {
            "sa3-expanded-quality": "sa3-expanded-quality-complete",
            "sa3-evidence-envelope-quality": "sa3-evidence-envelope-quality-complete",
            "sa3-evidence-envelope-candidate-i-quality":
                "sa3-evidence-envelope-candidate-i-quality-complete",
            "sa3-evidence-matrix-candidate-j-public":
                "sa3-evidence-matrix-candidate-j-public-complete",
            "sa3-evidence-matrix-candidate-j-quality":
                "sa3-evidence-matrix-candidate-j-quality-complete",
            "m3-joint-semantic-35b": "m3-joint-semantic-public-complete",
            "ebook-word-alignment": "ebook-word-alignment-benchmark-complete",
            "aster-tts-dual-cpu-screen": "aster-tts-dual-cpu-screen-complete",
            "aster-tts-single-cpu-screen": "aster-tts-single-cpu-screen-complete",
            "aster-news-video-musetalk-xpu": "aster-news-video-musetalk-xpu-complete",
            "m3-k2-shortlist-arbitration-development":
                "m3-k2-development-complete",
            "m3-k3-hierarchical-safety-development":
                "m3-k3-development-complete",
        }.get(spec.runner_kind, "pilot-complete"))
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
        elif spec.runner_kind in {
                "sa3-evidence-envelope-quality",
                "sa3-evidence-envelope-candidate-i-quality",
                "sa3-evidence-matrix-candidate-j-quality"}:
            receipt_valid=(receipt_valid
                and set(receipt)=={"effects","production_restored","receipt"}
                and set(receipt_body)=={"exit_status","profile","request_count",
                                        "model_request_count","case_count",
                                        "prediction_sha256","error_count"}
                and receipt.get("production_restored") is True
                and receipt_body.get("model_request_count")==14
                and receipt_body.get("case_count")==20
                and receipt_body.get("error_count")==0
                and isinstance(receipt_body.get("prediction_sha256"),str)
                and len(receipt_body["prediction_sha256"])==64
                and all(c in "0123456789abcdef"
                        for c in receipt_body["prediction_sha256"]))
        elif spec.runner_kind=="sa3-evidence-matrix-candidate-j-public":
            receipt_valid=(receipt_valid
                and set(receipt)=={"effects","production_restored","receipt"}
                and set(receipt_body)=={"exit_status","profile","request_count",
                                        "model_request_count","case_count",
                                        "prediction_sha256","error_count"}
                and receipt.get("production_restored") is True
                and receipt_body.get("model_request_count")==2
                and receipt_body.get("case_count")==6
                and receipt_body.get("error_count")==0
                and isinstance(receipt_body.get("prediction_sha256"),str)
                and len(receipt_body["prediction_sha256"])==64
                and all(c in "0123456789abcdef"
                        for c in receipt_body["prediction_sha256"]))
        elif spec.runner_kind=="m3-k2-shortlist-arbitration-development":
            receipt_valid=(receipt_valid
                and set(receipt)=={"effects","production_restored","receipt"}
                and set(receipt_body)=={"exit_status","profile","request_count",
                                        "model_request_count","case_count",
                                        "prediction_sha256","development_gate_passed",
                                        "status","error_count"}
                and receipt.get("production_restored") is True
                and receipt_body.get("model_request_count")==192
                and receipt_body.get("case_count")==192
                and receipt_body.get("error_count")==0
                and type(receipt_body.get("development_gate_passed")) is bool
                and receipt_body.get("status") in {"pass","reject"}
                and (receipt_body["status"] == "pass")
                    is receipt_body["development_gate_passed"]
                and isinstance(receipt_body.get("prediction_sha256"),str)
                and len(receipt_body["prediction_sha256"])==64
                and all(c in "0123456789abcdef"
                        for c in receipt_body["prediction_sha256"]))
        elif spec.runner_kind=="m3-k3-hierarchical-safety-development":
            receipt_valid=(receipt_valid
                and set(receipt)=={"effects","production_restored","receipt"}
                and set(receipt_body)=={"exit_status","profile","request_count",
                                        "model_request_count","case_count",
                                        "prediction_sha256","development_gate_passed",
                                        "status","error_count"}
                and receipt.get("production_restored") is True
                and receipt_body.get("model_request_count")==384
                and receipt_body.get("case_count")==192
                and receipt_body.get("error_count")==0
                and type(receipt_body.get("development_gate_passed")) is bool
                and receipt_body.get("status") in {"pass","reject"}
                and (receipt_body["status"] == "pass")
                    is receipt_body["development_gate_passed"]
                and isinstance(receipt_body.get("prediction_sha256"),str)
                and len(receipt_body["prediction_sha256"])==64
                and all(c in "0123456789abcdef"
                        for c in receipt_body["prediction_sha256"]))
        elif spec.runner_kind=="ebook-word-alignment":
            receipt_valid=(receipt_valid
                and set(receipt)=={"effects","production_restored","receipt"}
                and set(receipt_body)=={"exit_status","profile","request_count",
                                        "result_sha256","passed","failure_code",
                                        "measured_word_count"}
                and receipt.get("production_restored") is True
                and isinstance(receipt_body.get("result_sha256"),str)
                and len(receipt_body["result_sha256"])==64
                and all(c in "0123456789abcdef" for c in receipt_body["result_sha256"])
                and type(receipt_body.get("passed")) is bool
                and isinstance(receipt_body.get("failure_code"),str)
                and type(receipt_body.get("measured_word_count")) is int
                and 0 <= receipt_body["measured_word_count"] <= 4000)
        elif spec.runner_kind=="aster-tts-dual-cpu-screen":
            receipt_valid=(receipt_valid
                and set(receipt)=={"effects","production_restored","receipt"}
                and set(receipt_body)=={"exit_status","profile","request_count",
                                        "result_sha256","candidate_count","passed_count"}
                and receipt.get("production_restored") is True
                and isinstance(receipt_body.get("result_sha256"),str)
                and len(receipt_body["result_sha256"])==64
                and all(c in "0123456789abcdef" for c in receipt_body["result_sha256"])
                and receipt_body.get("candidate_count")==2
                and receipt_body.get("passed_count")==2)
        elif spec.runner_kind=="aster-tts-single-cpu-screen":
            expected_candidate={
                "aster-tts-qwen-0p6b-cpu-screen-v1": "qwen3-tts-0.6b-base-q8-cpu",
                "aster-tts-qwen-1p7b-cpu-screen-v1": "qwen3-tts-1.7b-base-q8-cpu",
            }.get(booking["workload"])
            receipt_valid=(receipt_valid
                and set(receipt)=={"effects","production_restored","receipt"}
                and set(receipt_body)=={"exit_status","profile","request_count",
                                        "result_sha256","candidate_count","passed_count",
                                        "candidate_id"}
                and receipt.get("production_restored") is True
                and isinstance(receipt_body.get("result_sha256"),str)
                and len(receipt_body["result_sha256"])==64
                and all(c in "0123456789abcdef" for c in receipt_body["result_sha256"])
                and receipt_body.get("candidate_count")==1
                and receipt_body.get("passed_count")==1
                and receipt_body.get("candidate_id")==expected_candidate)
        elif spec.runner_kind=="aster-news-video-musetalk-xpu":
            receipt_valid=(receipt_valid
                and set(receipt)=={"effects","production_restored","receipt"}
                and set(receipt_body)=={"exit_status","profile","request_count",
                                        "result_sha256","frame_count","output_sha256",
                                        "render_seconds"}
                and receipt.get("production_restored") is True
                and isinstance(receipt_body.get("result_sha256"),str)
                and len(receipt_body["result_sha256"])==64
                and all(c in "0123456789abcdef" for c in receipt_body["result_sha256"])
                and isinstance(receipt_body.get("output_sha256"),str)
                and len(receipt_body["output_sha256"])==64
                and all(c in "0123456789abcdef" for c in receipt_body["output_sha256"])
                and type(receipt_body.get("frame_count")) is int
                and 1 <= receipt_body["frame_count"] <= 100
                and type(receipt_body.get("render_seconds")) in {int,float}
                and receipt_body["render_seconds"] > 0)
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
        if spec.retryable_session:
            store.finish_attempt(booking_id, claimant=claimant, success=True,
                                 result_code="COMPLETE", production_restored=True)
        else:
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
        if admitted:
            try:
                if spec is not None and spec.retryable_session:
                    store.finish_attempt(booking_id, claimant=claimant, success=False,
                                         result_code="NO_GO", production_restored=restored)
                else:
                    store.finish(booking_id,claimant=claimant,success=False,result_code="NO_GO")
            except ReservationError: pass
        return 1


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--booking-id",required=True)
    p.add_argument("--retry", action="store_true")
    args = p.parse_args()
    return run(args.booking_id, retry=args.retry)


if __name__=="__main__": raise SystemExit(main())
