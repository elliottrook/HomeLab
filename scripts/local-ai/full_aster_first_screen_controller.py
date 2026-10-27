"""Root owner transaction for the full-Aster two-request first screen."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import secrets
import stat
import subprocess
import sys
import tempfile
import time
from zoneinfo import ZoneInfo

for _path in (
    "/usr/local/libexec/local-ai-lease/stream-a-evaluation",
    "/usr/local/libexec/local-ai-lease/full-inference-pilot",
):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from full_aster_first_screen_candidate import (
    UNIT as CANDIDATE_UNIT, baseline_stop_command, start_command,
)
from full_aster_first_screen_guardian import ARMED, STATE
from full_aster_first_screen_observer import (
    BINARY_SHA256, MODEL_SHA256, UNIT_SHA256, FixedObserver,
)
from full_aster_first_screen_recovery import (
    HOST_MODEL, HOST_ROOT, MAPPED_GID, MAPPED_UID, MOUNT_KEY, MOUNT_VALUE,
    RecoveryIdentity, recover,
)
import full_aster_first_screen_admission as screen_admission
from cooperative_lab_host_adapter import CooperativeHostObserver
from full_inference_lab_session import (
    FullDrainPaths, FullInferenceDrainController, plan as build_full_drain_plan,
)
from full_inference_lab_sources import (
    AcceptedBaseline, LocalProxmoxFullDrainSourceProducer,
    TrustedOwnerAttestation,
)
from full_inference_lab_validator import LocalProxmoxFullDrainValidator
from stream_a_evaluation_f4_f5_root import (
    EvidencePaths, collect_fixed_sources, publish as publish_f4_f5,
)
from stream_a_evaluation_f4_f5_transaction import build_transaction


ZONE = ZoneInfo("America/Vancouver")
REQUESTS = "/usr/local/libexec/full-aster-first-screen-requests"
PYTHONPATH = "/usr/local/libexec/local-ai-lease/full-inference-pilot"
MAX_RESULT_BYTES = 64 * 1024


class ControllerError(RuntimeError):
    pass


def _canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _write_new(path: Path, value: dict) -> None:
    if os.geteuid() != 0 or os.path.lexists(path):
        raise ControllerError("durable state custody is invalid")
    parent = path.parent.stat()
    if parent.st_uid != 0 or stat.S_IMODE(parent.st_mode) != 0o700:
        raise ControllerError("durable state parent is not root-only")
    raw = _canonical(value)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                         | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def _replace(path: Path, value: dict) -> None:
    raw = _canonical(value)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(name, path)
    except BaseException:
        try: os.unlink(name)
        except FileNotFoundError: pass
        raise


def _run(command, timeout, *, allowed=(0,)) -> subprocess.CompletedProcess:
    value = subprocess.run(tuple(command), capture_output=True, text=True,
                           timeout=timeout, check=False,
                           env={**os.environ, "PYTHONPATH": PYTHONPATH})
    if value.returncode not in allowed or value.stderr:
        raise ControllerError("fixed transaction command failed")
    return value


def _json_result(result: subprocess.CompletedProcess) -> dict:
    raw = result.stdout.encode()
    if not 0 < len(raw) <= MAX_RESULT_BYTES:
        raise ControllerError("fixed transaction result is empty or oversized")
    try: value = json.loads(result.stdout)
    except json.JSONDecodeError as error: raise ControllerError("fixed transaction result is invalid") from error
    if not isinstance(value, dict): raise ControllerError("fixed transaction result is not an object")
    return value


def _set_phase(state: dict, phase: str) -> None:
    state["phase"] = phase
    _replace(STATE, state)


def _mount_add_command():
    return ("pct", "set", "110", f"--{MOUNT_KEY}", MOUNT_VALUE)


def _runner(command, timeout):
    _run(command, timeout)


def _source_runner(command, timeout):
    try:
        value = subprocess.run(tuple(command), capture_output=True, text=True,
                               timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return 124, ""
    return value.returncode, value.stdout


def _verify_host_artifact(observer: FixedObserver) -> None:
    if not observer.artifact_root_custody():
        raise ControllerError("staged artifact custody is not exact")
    result = _run(("sha256sum", HOST_MODEL), 300.0)
    if result.stdout.split()[:1] != [
            "671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7"]:
        raise ControllerError("staged artifact digest is not exact")


def _remove_pre_effect_files(paths: tuple[Path, ...], *, owner_uid: int = 0) -> None:
    """Remove only regular root-custodied files created by this invocation."""
    for path in reversed(paths):
        value = path.lstat()
        if (not stat.S_ISREG(value.st_mode) or value.st_uid != owner_uid
                or value.st_nlink != 1 or stat.S_IMODE(value.st_mode) != 0o600):
            raise ControllerError("pre-effect evidence custody is uncertain")
        path.unlink()


def execute(*, owner_id: str, owner_unit: str, observer: FixedObserver,
            now: callable = time.time, sleep: callable = time.sleep) -> dict:
    if (os.geteuid() != 0
            or not re.fullmatch(r"aster-full-screen-owner-[0-9a-f]{16}", owner_id)
            or owner_unit != owner_id + ".scope"):
        raise ControllerError("owner identity is invalid")
    try:
        guardian = json.loads(ARMED.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ControllerError("independent guardian is not armed") from error
    if (guardian.get("schema") != "aster-full-path-first-screen-guardian.v1"
            or guardian.get("state") != "armed"
            or guardian.get("owner_unit") != owner_unit
            or type(guardian.get("rescue_at")) is not int
            or type(guardian.get("hard_deadline")) is not int
            or guardian["hard_deadline"] - guardian["rescue_at"] < 900
            or guardian["rescue_at"] <= int(now())):
        raise ControllerError("independent guardian boundary is invalid")
    local = datetime.fromtimestamp(now(), ZONE)
    cycle_dash = local.strftime("%Y-%m-%d")
    cycle_under = local.strftime("%Y_%m_%d")
    state = {"schema":"aster-full-path-first-screen-live.v1", "phase":"armed",
             "owner_id":owner_id, "owner_unit":owner_unit, "cycle":cycle_under,
             "model_sha256":MODEL_SHA256, "binary_sha256":BINARY_SHA256,
             "unit_sha256":UNIT_SHA256,"admission_sha256":""}
    _write_new(STATE, state)
    lease_identity = None
    drain_attempted = False
    pre_effect_files: tuple[Path, ...] = ()
    try:
        _verify_host_artifact(observer)
        start_epoch = int(now()) + 120
        baseline = AcceptedBaseline(MODEL_SHA256, BINARY_SHA256, UNIT_SHA256)
        preflight = LocalProxmoxFullDrainSourceProducer(
            _source_runner, baseline,
            TrustedOwnerAttestation(owner_id, "batchmode-pinned-ed25519-proxmox-root"),
            wall_clock=now).collect(cycle=cycle_under,
                                    session_start_epoch=start_epoch,
                                    lab_seconds=30 * 60)
        sources = collect_fixed_sources(now_epoch=int(now()))
        evidence_paths=EvidencePaths()
        if any(os.path.lexists(path) for path in
               (evidence_paths.f4,evidence_paths.f5,screen_admission.PATH)):
            raise ControllerError("fresh screen evidence targets are not empty")
        evidence = build_transaction(
            cycle_date=sources.cycle_date, nonce=secrets.token_hex(8),
            observed_epoch=sources.observed_epoch,
            observed_minute=sources.observed_minute,
            f2_bytes=sources.f2_bytes, f3_bytes=sources.f3_bytes,
            backup_receipt=sources.backup_receipt,
            observation=sources.observation,
            lxc110_mirror_identity=sources.lxc110_mirror_identity,
            lease_id=preflight.lease_id)
        if not sources.unchanged():
            raise ControllerError("F2/F3 evidence changed before publication")
        publish_f4_f5(evidence, paths=evidence_paths, publish_admission=False)
        pre_effect_files = (evidence_paths.f4, evidence_paths.f5)
        if evidence.lease_id != preflight.lease_id:
            raise ControllerError("fresh F4/F5 evidence has a foreign lease identity")
        specific = screen_admission.build(
            cycle_date=sources.cycle_date, lease_id=preflight.lease_id,
            created_epoch=sources.observed_epoch,
            expires_epoch=sources.observed_epoch+900,
            f2_bytes=sources.f2_bytes, f3_bytes=sources.f3_bytes,
            f4_bytes=evidence.f4_bytes, f5_bytes=evidence.f5_bytes)
        state["admission_sha256"]=screen_admission.write_new(specific)
        pre_effect_files = (*pre_effect_files, screen_admission.PATH)
        _replace(STATE,state)
        remaining = start_epoch - now()
        if remaining < 0 or remaining > 120:
            raise ControllerError("preflight exceeded its effect-start window")
        if remaining: sleep(remaining)
        host_observer = CooperativeHostObserver(_source_runner)
        full_drain = FullInferenceDrainController(
            FullDrainPaths(Path("/var/lib/local-ai-lab")),
            lambda command: _runner(command, 30.0), observer=host_observer,
            validator=LocalProxmoxFullDrainValidator(
                _source_runner, baseline, cycle=cycle_under),
            owner_id=owner_id, allow_effects=True)
        plan = build_full_drain_plan(preflight)
        lease_identity = RecoveryIdentity(owner_id, plan.lease_id, plan.generation,
            cycle_under, MODEL_SHA256, BINARY_SHA256, UNIT_SHA256)
        drain_attempted = True
        full_drain.begin(preflight)
        _set_phase(state, "drained")

        if not observer.artifact_root_custody():
            raise ControllerError("staged artifact custody drifted before mapping")
        _run(("chown", f"{MAPPED_UID}:{MAPPED_GID}", HOST_ROOT), 30.0)
        _run(("chmod", "0700", HOST_ROOT), 30.0)
        _run(("chown", f"{MAPPED_UID}:{MAPPED_GID}", HOST_MODEL), 30.0)
        _run(("chmod", "0400", HOST_MODEL), 30.0)

        _run(("pct", "shutdown", "110", "--timeout", "60"), 75.0)
        if observer.guest_running(): raise ControllerError("LXC110 did not stop")
        if observer.mount_state() != "absent": raise ControllerError("mp0 is not free")
        _run(_mount_add_command(), 30.0)
        if observer.mount_state() != "exact": raise ControllerError("candidate mount is not exact")
        _run(("pct", "start", "110"), 90.0)
        if not observer.guest_running(): raise ControllerError("LXC110 did not start")
        _set_phase(state, "mounted")

        guest_model = "/opt/models/aster-first-screen/Qwen3.6-35B-A3B-Q4_K_M.gguf"
        stat_result = _run(("pct", "exec", "110", "--", "stat", "-c",
            "%u:%g:%a:%s:%h", guest_model), 30.0)
        if stat_result.stdout.strip() != "999:991:400:20419565568:1":
            raise ControllerError("guest candidate artifact custody is not exact")
        _run(("pct", "exec", "110", "--", "runuser", "-u", "ollama", "--",
              "test", "-r", guest_model), 30.0)
        guest_hash = _run(("pct", "exec", "110", "--", "sha256sum", guest_model), 300.0)
        if guest_hash.stdout.split()[:1] != [
                "671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7"]:
            raise ControllerError("guest candidate artifact digest is not exact")

        _run(baseline_stop_command(), 45.0)
        _run(start_command(), 30.0)
        _set_phase(state, "candidate")
        deadline = time.monotonic() + 330
        while True:
            result = _run(("pct", "exec", "110", "--", "systemctl", "is-active",
                           CANDIDATE_UNIT), 15.0, allowed=(0, 3, 4))
            if result.returncode == 0 and result.stdout.strip() == "active": break
            if time.monotonic() >= deadline: raise ControllerError("candidate did not become active")
            sleep(2.0)
        health_deadline = time.monotonic() + 330
        while True:
            code, _output = _source_runner(("pct", "exec", "110", "--", "curl",
                "-fsS", "--max-time", "5", "http://192.168.70.12:11435/health"), 10.0)
            if code == 0: break
            if time.monotonic() >= health_deadline:
                raise ControllerError("candidate health endpoint did not become ready")
            sleep(2.0)
        if not observer.candidate_resident():
            raise ControllerError("candidate GPU holder or host-memory residency is not exact")
        request_result = _json_result(_run(("pct", "exec", "110", "--",
            "/usr/bin/python3", "-B", REQUESTS, "--run-authorized"), 150.0))
        if (request_result.get("state") != "complete"
                or request_result.get("request_count") != 2
                or request_result.get("retries") != 0
                or request_result.get("answer_content_retained") is not False
                or request_result.get("hidden_reasoning_retained") is not False):
            raise ControllerError("two-request result is not exact")
        restore_lease = lambda: full_drain.restore(
            plan, now_epoch=int(now()), owner_present=True)
        recover(identity=lease_identity, observer=observer, runner=_runner,
                lease_restorer=restore_lease)
        STATE.unlink()
        return request_result
    except BaseException as error:
        if not drain_attempted:
            # No drain was accepted. Nothing live may have changed.
            try:
                _remove_pre_effect_files(pre_effect_files)
                STATE.unlink()
            except BaseException as cleanup_error:
                raise ControllerError(
                    "pre-effect cleanup is uncertain; files retained") from cleanup_error
            raise
        try:
            recover(identity=lease_identity, observer=observer, runner=_runner,
                    lease_restorer=lambda: full_drain.restore(
                        plan, now_epoch=int(now()), owner_present=True))
            STATE.unlink()
        except BaseException as recovery_error:
            raise ControllerError("first-screen recovery is uncertain; state retained") from recovery_error
        raise error


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-id", required=True)
    parser.add_argument("--owner-unit", required=True)
    parser.add_argument("--effect-authorized", action="store_true")
    args=parser.parse_args(argv)
    if not args.effect_authorized:
        print(json.dumps({"state":"disabled","effects":"not-attempted"},sort_keys=True)); return 0
    try: result=execute(owner_id=args.owner_id, owner_unit=args.owner_unit, observer=FixedObserver())
    except BaseException:
        print(json.dumps({"state":"failed","result_retained":False},sort_keys=True)); return 1
    print(json.dumps(result,sort_keys=True,separators=(",",":"))); return 0


if __name__ == "__main__": raise SystemExit(main())
