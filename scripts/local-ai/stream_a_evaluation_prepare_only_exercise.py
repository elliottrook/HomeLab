"""One-shot prepare-only Stream A evaluation recovery exercise.

The default CLI is inert.  The authorized path creates no production receipt,
never quiesces a consumer, never calls a model, and invokes only the frozen
exercise-prepare, transient owner, heartbeat and watchdog entry points.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import stat
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from evaluation_lease_adapter import read_state
from stream_a_evaluation_owner import EXERCISE_OWNER_UNIT
from stream_a_evaluation_watchdog import load_identity

ROOT = Path("/var/lib/local-ai-lab/stream-a-evaluation")
IDENTITY = Path("/etc/local-ai-lab/stream-a-evaluation/watchdog-identity.json")
STATE = ROOT / "lease.json"
LEASE_LOCK = ROOT / "lease.lock"
OPERATION_LOCK = ROOT / "lease.operation.lock"
OWNER_INTENT = ROOT / "owner-intent.json"
HEARTBEAT = ROOT / "owner-heartbeat.json"
WATCHDOG_STATUS = ROOT / "watchdog-status.json"
RESTORE_INTENT = ROOT / "restore-intent.json"
RECEIPT_ROOT = ROOT / "exercise-receipts"
LEASE_ENTRYPOINT = "/usr/local/sbin/stream-a-evaluation-lease"
WHOLE_HOST_LEASE = "/usr/local/sbin/local-ai-lease"
OWNER_START = "/usr/local/sbin/stream-a-evaluation-exercise-owner-start"
HEARTBEAT_ENTRYPOINT = "/usr/local/sbin/stream-a-evaluation-owner-heartbeat"
WATCHDOG_ENTRYPOINT = "/usr/local/sbin/stream-a-evaluation-watchdog"
RESTORE_OBSERVER = "/usr/local/sbin/stream-a-evaluation-restore-observe"
EXERCISE_UNIT = "stream-a-evaluation-exercise-owner.service"
F6_UNITS = (
    "stream-a-evaluation-owner.service",
    "stream-a-evaluation-owner-heartbeat.service",
    "stream-a-evaluation-owner-heartbeat.timer",
    "stream-a-evaluation-watchdog.service",
    "stream-a-evaluation-watchdog.timer",
)
F2_TIMERS = ("f2-preflight-prepare-20261026.timer", "f2-preflight-final-20261026.timer")
CONSUMERS = (
    ("104", "aster-agent.service", "unit"),
    ("116", "aster-speech.service", "unit"),
    ("114", "news-aggregator-ingest.timer", "timer"),
    ("114", "news-aggregator-digest.timer", "timer"),
)
REGISTERED = (
    "lxc104:aster-agent.service",
    "lxc116:aster-speech.service",
    "lxc114:news-aggregator-ingest.timer",
    "lxc114:news-aggregator-digest.timer",
)
MODEL = "Qwen3.5 9B Q4_K_M"
BACKEND = "llama.cpp b11429 SYCL/Level Zero"
ENDPOINT = "http://192.168.70.12:11435/v1/chat/completions"
MARKER = "PRE-EFFECT-EXERCISE-NOT-PRODUCTION-EVIDENCE"
MODE = "stream-a-prepare-only-exercise-v1"
HEARTBEAT_TIMEOUT = 5
F2_PREPARE_EPOCH = 1793002500
MINIMUM_F2_MARGIN_SECONDS = 30 * 60
PINNED_FILES = {
    "/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease.py": "5c5aa6c7174d53edb775f9a2640a867634b04a9b098d0742a589a1c2dc692686",
    "/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_adapter.py": "6876e6892cae0d81c584fee7d6f3c5b79874d9b4737d250987f451f28b6aa910",
    "/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_entrypoint.py": "0dab61905c834c36e3a865f8049c2650712422ddc27c534f1cd402b4e5ad52bb",
    "/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_watchdog.py": "19606f6b398dd6f43a461704081e66f09e292c434f73f4aaee46327f9cc02f53",
    "/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_owner.py": "74c8072793cbbcc68e40d0548065f55031c2b8e5bfeab3d9583069aa4c8a22a1",
    "/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_owner_heartbeat.py": "4c45a07098eb8cca31bf95bb50b0824b65c6772e636627b23219761f359ed6cc",
    "/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_watchdog.py": "c406dd4da579d4d5129b13131121b55ac1aacaa1a5125c9d481e0d7f847c9849",
    "/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_restore_observer.py": "9ecf64767e1c7acf402540d2701883241b1d94c6b8ec1b46248f20de6591f22b",
    LEASE_ENTRYPOINT: "15f3de1ebb5294878d5f0ce0c6a0b7c03a64b42a71c081fda6d036b0c1ef71af",
    "/usr/local/sbin/stream-a-evaluation-owner": "4d4e848eeafffdfa3aa9a0ba84097d94487318235442b1a4e4b8edc04a043014",
    HEARTBEAT_ENTRYPOINT: "e0162f60983601192c5f0fdd6d8395604e6636c05c9653c643d3722872dce12a",
    WATCHDOG_ENTRYPOINT: "65012c196134242a76a2131fbc9d7f28b50bcfd9137a87cfda0a416345430c99",
    RESTORE_OBSERVER: "5cb6bec83864b5a8eeeb1b8c0624b93498fc04b2fcf36afb61e13caa0e64e8ab",
    OWNER_START: "0d84d35300202c5d9316cc38a853402f7c252aab0ec5069f0b759dd3f3157d22",
    "/usr/local/libexec/aster-a1/llama_auth_probe.py": "0996e1b565ad24b740997bbfe598065267e20380135a5af41687d0562239cae6",
    "/usr/local/sbin/aster-llama-production-auth-probe": "aac604de1f35c048791c5f1cfc21e25d9eb3e679fb7d799f74671307463313ac",
}

class ExerciseError(RuntimeError):
    pass

@dataclass(frozen=True)
class Result:
    returncode: int
    stdout: str
    stderr: str = ""

Command = Callable[[Sequence[str], int], Result]
Clock = Callable[[], int]
Sleeper = Callable[[float], None]


def _real_command(argv: Sequence[str], timeout: int) -> Result:
    value = subprocess.run(tuple(argv), check=False, capture_output=True, text=True, timeout=timeout)
    return Result(value.returncode, value.stdout, value.stderr)


def _root_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try: os.unlink(temporary)
        except FileNotFoundError: pass
        raise


def _load_json(text: str, expected: set[str]) -> dict[str, object]:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result: raise ExerciseError("duplicate JSON key")
            result[key] = value
        return result
    try: value = json.loads(text, object_pairs_hook=unique)
    except (json.JSONDecodeError, ValueError) as exc: raise ExerciseError("malformed JSON output") from exc
    if not isinstance(value, dict) or set(value) != expected:
        raise ExerciseError("unexpected JSON output schema")
    return value


def _safe_unlink(path: Path) -> None:
    try: info = path.lstat()
    except FileNotFoundError: return
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o600:
        raise ExerciseError(f"refusing unsafe cleanup path: {path.name}")
    path.unlink()


class Exercise:
    def __init__(self, command: Command = _real_command, clock: Clock = lambda: int(time.time()),
                 sleep: Sleeper = time.sleep, *, root: Path = ROOT, identity: Path = IDENTITY,
                 receipt_root: Path = RECEIPT_ROOT):
        self.command = command; self.clock = clock; self.sleep = sleep
        self.root = root; self.identity = identity; self.receipt_root = receipt_root
        self.paths = {
            "state": root / "lease.json", "lease_lock": root / "lease.lock",
            "operation_lock": root / "lease.operation.lock", "owner_intent": root / "owner-intent.json",
            "heartbeat": root / "owner-heartbeat.json", "status": root / "watchdog-status.json",
            "restore_intent": root / "restore-intent.json",
        }
        self.commands: list[str] = []

    def run(self, argv: Sequence[str], *, timeout: int = 20, allowed: tuple[int, ...] = (0,)) -> Result:
        words = tuple(argv)
        forbidden = {"mask", "stop", "start", "restart", "reload"}
        if (words and words[0] == "systemctl" and len(words) > 2
                and words[1] in forbidden and words[2] != EXERCISE_UNIT):
            raise ExerciseError("consumer/systemd mutation is forbidden")
        if any(unit in words for _vmid, unit, _kind in CONSUMERS):
            if not (words[0:2] == ("pct", "exec")
                    and ("is-active" in words or "is-enabled" in words)
                    and not any(action in words for action in forbidden)):
                raise ExerciseError("consumer command is forbidden")
        command_text = " ".join(words)
        if any(token in command_text for token in ("chat/completions", "llama-server", "ollama")):
            raise ExerciseError("model/backend command is forbidden")
        result = self.command(argv, timeout); self.commands.append(" ".join(argv))
        if result.returncode not in allowed: raise ExerciseError(f"command failed: {argv[0]}")
        return result

    def unit_state(self, vmid: str, unit: str) -> str:
        enabled = self.run(("pct", "exec", vmid, "--", "systemctl", "is-enabled", unit)).stdout.strip()
        active = self.run(("pct", "exec", vmid, "--", "systemctl", "is-active", unit)).stdout.strip()
        if (enabled, active) != ("enabled", "active"): raise ExerciseError(f"consumer is not enabled+active: {vmid}:{unit}")
        return "enabled+active"

    def f6_snapshot(self) -> dict[str, list[object]]:
        result = {}
        for unit in F6_UNITS:
            enabled = self.run(("systemctl", "is-enabled", unit), allowed=(0, 1)).stdout.strip()
            active = self.run(("systemctl", "is-active", unit), allowed=(0, 3)).stdout.strip()
            if (enabled, active) != ("disabled", "inactive"):
                raise ExerciseError(f"F6 unit is not disabled/inactive: {unit}")
            result[unit] = [enabled, active]
        return result

    def f2_snapshot(self) -> dict[str, str]:
        result = {}
        for timer in F2_TIMERS:
            value = self.run(("systemctl", "show", timer, "--property=Id,ActiveState,Unit,NextElapseUSecRealtime", "--no-pager")).stdout
            if "ActiveState=active" not in value: raise ExerciseError(f"F2 timer is not active: {timer}")
            result[timer] = hashlib.sha256(value.encode()).hexdigest()
        return result

    def observation(self, lease_id: str, generation: int) -> dict[str, object]:
        result = self.run((RESTORE_OBSERVER, "--lease-id", lease_id, "--generation", str(generation), "--observe-authorized"), timeout=30)
        value = _load_json(result.stdout, {"lease_id", "generation", "observed_at", "backend_active", "endpoint_authenticated", "endpoint_idle", "gpu_holders"})
        if (value["lease_id"] != lease_id or value["generation"] != generation
                or value["backend_active"] is not True or value["endpoint_authenticated"] is not True
                or value["endpoint_idle"] is not True
                or value["gpu_holders"] != ["lxc110:aster-llama.service"]):
            raise ExerciseError("backend observation is not exact")
        return value

    def require_absent(self) -> None:
        for path in tuple(self.paths.values()) + (self.identity, self.root / "exercise-intent.json"):
            if path.exists() or path.is_symlink(): raise ExerciseError(f"runtime path exists: {path.name}")

    def verify_static_custody(self) -> None:
        for raw, expected in PINNED_FILES.items():
            path = Path(raw); info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_uid != 0:
                raise ExerciseError(f"installed pin custody failed: {path.name}")
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ExerciseError(f"installed pin drifted: {path.name}")
        info = self.receipt_root.lstat()
        if (stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode)
                or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o700):
            raise ExerciseError("receipt directory custody is not root-owned 0700")

    def prestate(self, lease_id: str) -> dict[str, object]:
        self.require_absent(); self.verify_static_custody()
        if self.clock() + MINIMUM_F2_MARGIN_SECONDS >= F2_PREPARE_EPOCH:
            raise ExerciseError("exercise is too close to the October 26 F2 window")
        lease = _load_json(self.run((WHOLE_HOST_LEASE, "status")).stdout, {"state"})
        if lease != {"state": "ready"}: raise ExerciseError("whole-host lease is not ready")
        consumers = [self.unit_state(vmid, unit) for vmid, unit, _kind in CONSUMERS]
        return {"f6": self.f6_snapshot(), "f2": self.f2_snapshot(), "consumers": consumers,
                "observation": self.observation(lease_id, 1)}

    def validate_prepared_state(self, lease_id: str, generation: int, now: int,
                                baseline: dict[str, list[list[str]]]) -> None:
        state = read_state(self.paths["state"], expected_lease_id=lease_id,
                           expected_generation=generation)
        expected_units = tuple(tuple(row) for row in baseline["units"])
        expected_timers = tuple(tuple(row) for row in baseline["timers"])
        if (state.lease_mode != MODE or state.exercise_marker != MARKER
                or state.phase != "prepared" or state.window_start_epoch != now
                or state.heartbeat_epoch != now or state.hard_deadline_epoch != now + 120
                or state.restore_deadline_epoch != now + 300
                or state.baseline.units != expected_units or state.baseline.timers != expected_timers
                or state.next_workload is not None or state.in_flight_workload is not None
                or state.completed_outcomes):
            raise ExerciseError("prepared exercise state is not exact")

    def validate_owner_identity(self, lease_id: str, generation: int, owner_id: str) -> None:
        value = load_identity(self.identity)
        if (value.lease_id != lease_id or value.generation != generation
                or value.owner_id != owner_id or value.heartbeat_timeout != HEARTBEAT_TIMEOUT
                or value.unit != EXERCISE_OWNER_UNIT):
            raise ExerciseError("exercise owner identity is not exact")

    @staticmethod
    def validate_recovery(value: dict[str, object], lease_id: str, generation: int) -> None:
        if value.get("effects") != "recovered":
            raise ExerciseError("owner-loss recovery did not complete")
        result = value.get("result")
        if not isinstance(result, dict) or set(result) != {"entrypoint", "stdout"} or result.get("entrypoint") != "restored":
            raise ExerciseError("watchdog recovery result is not exact")
        terminal = _load_json(str(result["stdout"]), {"effects", "lease_id", "generation"})
        if terminal != {"effects": "cancelled-prepared", "lease_id": lease_id,
                        "generation": generation}:
            raise ExerciseError("prepared cancellation result is not exact")

    def execute(self) -> dict[str, object]:
        if os.geteuid() != 0: raise ExerciseError("root required")
        lease_id = f"exercise-20261025-{self.clock()}-{secrets.token_hex(4)}"
        generation = 1; owner_id = f"owner-{secrets.token_hex(8)}"
        pre = self.prestate(lease_id)
        now = self.clock()
        baseline = {"units": [[REGISTERED[0], "enabled+active"], [REGISTERED[1], "enabled+active"]],
                    "timers": [[REGISTERED[2], "enabled+active"], [REGISTERED[3], "enabled+active"]]}
        intent = {"lease_id": lease_id, "generation": generation, "exercise_marker": MARKER,
                  "model": MODEL, "backend": BACKEND, "endpoint": ENDPOINT,
                  "backend_active": True, "endpoint_authenticated": True, "endpoint_idle": True,
                  "gpu_holders": ["lxc110:aster-llama.service"], "registered_targets": list(REGISTERED),
                  "quiesced_targets": [], "baseline": baseline, "watchdog_independent": True,
                  "hard_deadline_epoch": now + 120, "restore_deadline_epoch": now + 300, "now_epoch": now}
        _root_json(self.root / "exercise-intent.json", intent)
        _root_json(self.paths["owner_intent"], {"lease_id": lease_id, "generation": generation,
                                                "heartbeat_timeout": HEARTBEAT_TIMEOUT, "owner_id": owner_id})
        owner_started = False
        try:
            prepared = _load_json(self.run((LEASE_ENTRYPOINT, "--phase", "exercise-prepare", "--intent",
                                             str(self.root / "exercise-intent.json"), "--effect-authorized")).stdout,
                                  {"effects", "state", "mode", "lease_id", "generation"})
            if prepared != {"effects": "exercise-prepared", "state": "prepared", "mode": MODE,
                            "lease_id": lease_id, "generation": generation}:
                raise ExerciseError("prepare result is not exact")
            self.validate_prepared_state(lease_id, generation, now, baseline)
            self.run((OWNER_START, "--effect-authorized")); owner_started = True
            deadline = time.monotonic() + 15
            while not self.identity.exists():
                if time.monotonic() >= deadline: raise ExerciseError("owner identity did not appear")
                self.sleep(0.2)
            self.validate_owner_identity(lease_id, generation, owner_id)
            self.run((HEARTBEAT_ENTRYPOINT, "--once", "--effect-authorized"))
            healthy = _load_json(self.run((WATCHDOG_ENTRYPOINT, "--once", "--effect-authorized"), timeout=60).stdout,
                                 {"decision", "effects"})
            if healthy.get("effects") != "not-attempted": raise ExerciseError("healthy watchdog was not inert")
            self.run(("systemctl", "stop", EXERCISE_UNIT), timeout=20); owner_started = False
            self.sleep(HEARTBEAT_TIMEOUT + 1)
            recovered = _load_json(self.run((WATCHDOG_ENTRYPOINT, "--once", "--effect-authorized"), timeout=60).stdout,
                                   {"decision", "effects", "result"})
            self.validate_recovery(recovered, lease_id, generation)
            if any(self.paths[name].exists() for name in ("state", "lease_lock", "operation_lock")):
                raise ExerciseError("durable exercise state did not clear")
            post_f6 = self.f6_snapshot(); post_f2 = self.f2_snapshot()
            if post_f6 != pre["f6"] or post_f2 != pre["f2"]: raise ExerciseError("unit or F2 state drifted")
            post_consumers = [self.unit_state(vmid, unit) for vmid, unit, _kind in CONSUMERS]
            if post_consumers != pre["consumers"]: raise ExerciseError("consumer baseline drifted")
            self.observation(lease_id, generation)
            for name in ("owner_intent", "heartbeat", "status", "restore_intent"):
                _safe_unlink(self.paths[name])
            _safe_unlink(self.identity); _safe_unlink(self.root / "exercise-intent.json")
            self.run(("systemctl", "reset-failed", EXERCISE_UNIT), allowed=(0, 1))
            command_rows = tuple(self.commands)
            snapshot_digest = hashlib.sha256(json.dumps(pre, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            receipt = {"status": "complete", "lease_id": lease_id, "generation": generation,
                       "healthy_effects": healthy["effects"], "healthy_decision": healthy["decision"],
                       "recovery_effects": recovered["effects"], "recovery_decision": recovered["decision"],
                       "consumer_commands": 0, "f2_unchanged": True, "f6_unchanged": True,
                       "installed_pins": dict(PINNED_FILES), "prestate_digest": snapshot_digest,
                       "commands": list(command_rows),
                       "commands_digest": hashlib.sha256("\n".join(command_rows).encode()).hexdigest(),
                       "completed_epoch": self.clock()}
            _root_json(self.receipt_root / f"{lease_id}.json", receipt)
            return receipt
        except Exception:
            if owner_started:
                try: self.run(("systemctl", "stop", EXERCISE_UNIT), timeout=20)
                except Exception: pass
            raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-once", action="store_true", required=True)
    parser.add_argument("--effect-authorized", action="store_true")
    args = parser.parse_args(argv)
    if not args.effect_authorized:
        print(json.dumps({"effects": "disabled", "state": "source-only"}, sort_keys=True)); return 0
    try: result = Exercise().execute()
    except Exception as exc:
        print(json.dumps({"effects": "failed-closed", "error": type(exc).__name__}, sort_keys=True)); return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":"))); return 0

if __name__ == "__main__": raise SystemExit(main())
