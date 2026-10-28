"""One-shot October 29 Lab Hours release-candidate transaction.

This runner is deliberately independent of F2/F3/F4/F5.  It requires only the
fresh completed Proxmox backup already enforced by the full-inference source
producer, the accepted production baseline, and a quiet shared host boundary.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo


CYCLE = "2026_10_29"
PILOT = Path("/usr/local/libexec/local-ai-lease/full-inference-pilot")
STATE_ROOT = Path("/var/lib/local-ai-lab")
EVIDENCE = STATE_ROOT / "lab-hours-attempts" / "night-rc1c-20261029"
TOKEN = "lh-night-rc1c-20261029"
OWNER_UNIT = f"aster-local-ai-pilot-owner-{TOKEN}.scope"
GUARDIAN_UNIT = f"aster-local-ai-pilot-guardian-{TOKEN}.service"
MODEL_SHA = "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13"
BINARY_SHA = "0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5"
UNIT_SHA = "a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3"
PINNED = {
    "cooperative_lab_host_adapter.py": "65151e7d7cb511c79afffa0544adb86ee9820e963330c0c5ae4a214e30f92d88",
    "full_inference_lab_deadline_guardian.py": "b7cbc3992868400b95e90cd783b26511e1c4f2a2f2b587b6f111c0a58dd4b96f",
    "full_inference_lab_install_preflight.py": "1ea2e37eb2ab8ea34251f4af1337cd2d7f94b00933eb60ff7433b6adbe6ca8d3",
    "full_inference_lab_runtime.py": "c4f131baec043511e525bb3babfa9a0b11236d4de1f399b2152c43f288cc79b9",
    "full_inference_lab_session.py": "217cd468111b5e3fea280515a9ac7b9e5b77776c5510764c8b9ca8803ddf5b02",
    "full_inference_lab_sources.py": "920d2ed171d314a6cb346032651c24a7972e51b2a91c2bb2892dcd9419c50d48",
    "full_inference_lab_supervisor.py": "da5ac76fb48541a2661caa1cb4fe7f21d84334abb9ab935fb1aaaf72c4faba55",
    "full_inference_lab_validator.py": "0c4a21d7894dd2c41d89aa00d2fa5969277991ff86febf8a89a61ac299966858",
    "full_inference_lab_workload.py": "b0ad8a6422d4290cd73568916de4e35ef05130e5b93aee22c629ce7560beb236",
}
COMPETING_UNITS = (
    "f2-preflight-prepare.service", "f2-preflight-final.service",
    "f3-from-f2-20261029.service", "f4-f5-evidence-20261029.service",
    "epub-narration-quiesce-20261029.service",
    "epub-narration-resume-20261029.service",
)
PROCESS_MARKERS = ("vzdump", "zstd -t", "f2_preflight", "f3_from_f2",
                   "stream_a_evaluation_evidence", "full_aster_first_screen",
                   "epub_narration_quiesce", "epub_narration_resume")
LOCAL_ZONE = ZoneInfo("America/Vancouver")
WINDOW_START = (4, 0)
WINDOW_END = (4, 15)


class NightRunError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def fail(code: str) -> None:
    raise NightRunError(code)


def call(command: tuple[str, ...], timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)


def atomic_json(path: Path, value: dict[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def require_static() -> None:
    if os.geteuid() != 0:
        fail("NOT_ROOT")
    local_now = datetime.now(LOCAL_ZONE)
    if local_now.date().isoformat() != "2026-10-29":
        fail("OUTSIDE_EXACT_DATE")
    minute = local_now.hour * 60 + local_now.minute
    if not (WINDOW_START[0] * 60 + WINDOW_START[1] <= minute
            <= WINDOW_END[0] * 60 + WINDOW_END[1]):
        fail("OUTSIDE_START_WINDOW")
    for name, expected in PINNED.items():
        path = PILOT / name
        if not path.is_file() or path.is_symlink():
            fail(f"INSTALLED_PIN_TYPE:{name}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            fail(f"INSTALLED_PIN_DRIFT:{name}")
    if EVIDENCE.exists():
        fail("ATTEMPT_ALREADY_EXISTS")
    for path in (STATE_ROOT / "full-inference-drain.json",
                 STATE_ROOT / "full-inference-drain.lock",
                 Path("/run/local-ai-lab-operation.lock")):
        if path.exists():
            fail("SHARED_STATE_OR_LOCK_PRESENT")
    lease = call(("/usr/local/sbin/local-ai-lease", "status"), 10.0)
    if lease.returncode != 0 or lease.stdout.strip() != '{\n  "state": "ready"\n}':
        fail("LEASE_NOT_READY")
    for unit in COMPETING_UNITS:
        result = call(("systemctl", "is-active", unit), 10.0)
        if result.returncode == 0:
            fail(f"COMPETING_EXACT_CYCLE_UNIT:{unit}")
    for proc in Path("/proc").glob("[0-9]*"):
        if proc.name == str(os.getpid()):
            continue
        try:
            command = proc.joinpath("cmdline").read_bytes().replace(b"\0", b" ").decode("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        marker = next((item for item in PROCESS_MARKERS if item in command), None)
        if marker is not None:
            fail(f"COMPETING_PROCESS:{marker}")


def guardian_command(start: int) -> tuple[str, ...]:
    return ("systemd-run", "--quiet", "--collect", f"--unit={GUARDIAN_UNIT}",
            "--property=User=root", "--property=Restart=no",
            "/usr/bin/python3", "-B", str(PILOT / "full_inference_lab_deadline_guardian.py"),
            "--state-root", str(STATE_ROOT), "--owner-id", TOKEN,
            "--owner-unit", OWNER_UNIT, "--cycle", CYCLE,
            "--model-sha256", MODEL_SHA, "--binary-sha256", BINARY_SHA,
            "--unit-sha256", UNIT_SHA, "--rescue-at", str(start + 1800),
            "--hard-deadline", str(start + 2700), "--effect-authorized")


def owner_command(start: int) -> tuple[str, ...]:
    return ("systemd-run", "--quiet", "--collect", "--scope", f"--unit={OWNER_UNIT}",
            "/usr/bin/python3", "-B", str(PILOT / "full_inference_lab_runtime.py"),
            "--phase", "pilot", "--owner-id", TOKEN, "--owner-unit", OWNER_UNIT,
            "--admin-path-evidence", "host-owned-exact-cycle-20261029",
            "--cycle", CYCLE, "--session-start-epoch", str(start),
            "--model-sha256", MODEL_SHA, "--binary-sha256", BINARY_SHA,
            "--unit-sha256", UNIT_SHA, "--effect-authorized", "--news-overlap-authorized")


def postcheck() -> None:
    sys.path.insert(0, str(PILOT))
    from full_inference_lab_sources import AcceptedBaseline
    from full_inference_lab_validator import LocalProxmoxFullDrainValidator
    for path in (STATE_ROOT / "full-inference-drain.json",
                 STATE_ROOT / "full-inference-drain.lock",
                 Path("/run/local-ai-lab-operation.lock")):
        if path.exists():
            fail("POSTCHECK_STATE_OR_LOCK")
    def runner(command, timeout):
        result = call(tuple(command), timeout)
        return result.returncode, result.stdout
    validator = LocalProxmoxFullDrainValidator(
        runner, AcceptedBaseline(MODEL_SHA, BINARY_SHA, UNIT_SHA), cycle=CYCLE)
    if not validator():
        fail("PRODUCTION_RESTORATION_INVALID")
    owner = call(("systemctl", "is-active", OWNER_UNIT), 10.0)
    if owner.returncode == 0:
        fail("OWNER_SCOPE_REMAINS_ACTIVE")


def main() -> int:
    started = int(time.time())
    phase = "static-preflight"
    effects_may_have_started = False
    production_restored = True
    try:
        require_static()
        EVIDENCE.mkdir(mode=0o700, parents=True)
        start = int(time.time()) + 60
        atomic_json(EVIDENCE / "attempt.json", {
            "schema": "aster-lab-hours-exact-cycle.v1", "cycle": CYCLE,
            "owner_id": TOKEN, "start_epoch": start,
            "rescue_epoch": start + 1800, "hard_deadline_epoch": start + 2700,
            "phase": "armed", "candidate_pins": PINNED,
        })
        phase = "guardian-arm"
        guardian = call(guardian_command(start), 30.0)
        if guardian.returncode != 0:
            fail("GUARDIAN_DID_NOT_ARM")
        phase = "owner-transaction"
        effects_may_have_started = True
        production_restored = False
        owner = call(owner_command(start), 45 * 60.0)
        (EVIDENCE / "owner.stdout").write_text(owner.stdout, encoding="utf-8")
        (EVIDENCE / "owner.stderr").write_text(owner.stderr, encoding="utf-8")
        os.chmod(EVIDENCE / "owner.stdout", 0o600)
        os.chmod(EVIDENCE / "owner.stderr", 0o600)
        if owner.returncode != 0:
            if (STATE_ROOT / "full-inference-drain.json").exists():
                phase = "guardian-recovery"
                deadline = start + 2700
                while time.time() <= deadline and (STATE_ROOT / "full-inference-drain.json").exists():
                    time.sleep(5.0)
            phase = "failed-owner-postcheck"
            postcheck()
            production_restored = True
            fail("OWNER_TRANSACTION_FAILED_RESTORED")
        try:
            receipt = json.loads(owner.stdout)
        except json.JSONDecodeError as exc:
            raise NightRunError("OWNER_OUTPUT_INVALID") from exc
        if (receipt.get("effects") != "pilot-complete"
                or receipt.get("receipt") != {"exit_status": 0,
                                               "profile": "accepted-9b-direct-control-smoke-v1",
                                               "request_count": 3}):
            fail("OWNER_RECEIPT_INCOMPLETE")
        phase = "production-postcheck"
        postcheck()
        production_restored = True
        call(("systemctl", "stop", GUARDIAN_UNIT), 30.0)
        call(("systemctl", "reset-failed", GUARDIAN_UNIT), 10.0)
        atomic_json(EVIDENCE / "terminal.json", {
            "schema": "aster-lab-hours-exact-cycle-result.v1", "state": "complete",
            "cycle": CYCLE, "owner_id": TOKEN, "started_epoch": started,
            "finished_epoch": int(time.time()), "request_count": 3,
            "production_restored": True, "candidate_pins": PINNED,
        })
        return 0
    except BaseException as exc:
        if effects_may_have_started and not production_restored:
            try:
                if not (STATE_ROOT / "full-inference-drain.json").exists():
                    postcheck()
                    production_restored = True
            except BaseException:
                production_restored = False
        EVIDENCE.mkdir(mode=0o700, parents=True, exist_ok=True)
        failure_code = exc.code if isinstance(exc, NightRunError) else type(exc).__name__
        atomic_json(EVIDENCE / "terminal.json", {
            "schema": "aster-lab-hours-exact-cycle-result.v1", "state": "no_go",
            "cycle": CYCLE, "owner_id": TOKEN, "started_epoch": started,
            "finished_epoch": int(time.time()), "first_failure_phase": phase,
            "failure_class": type(exc).__name__, "failure_code": failure_code,
            "production_restored": production_restored,
            "candidate_pins": PINNED,
        })
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
