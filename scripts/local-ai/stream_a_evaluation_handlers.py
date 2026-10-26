"""Fixed production-handler candidate for the Stream A evaluation sequence.

There is deliberately no CLI.  The caller must supply the already accepted
``LivePlan`` and the result verifier.  This module fixes the commands and
custody transitions for arming, workload launch, recovery and cleanup while
remaining uncallable until a separately reviewed composition root exists.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import time
from typing import Callable

from stream_a_evaluation_effect_driver import canonical_bytes, write_new_intent
from stream_a_evaluation_live_plan import D4_COMMAND, M3_COMMAND, LivePlan
from stream_a_evaluation_sequence import VerifiedOutcome
from stream_a_evaluation_watchdog import (
    WatchdogBoundaryError, load_identity, load_owner_heartbeat,
    owner_process_matches,
)


class HandlerError(RuntimeError):
    pass


MAX_COMMAND_RESULT_BYTES = 16 * 1024
MAX_RUNTIME_EVIDENCE_BYTES = 64 * 1024
OWNER_UNIT = "stream-a-evaluation-owner.service"
HEARTBEAT_UNIT = "stream-a-evaluation-owner-heartbeat.service"
HEARTBEAT_TIMER = "stream-a-evaluation-owner-heartbeat.timer"
WATCHDOG_UNIT = "stream-a-evaluation-watchdog.service"
WATCHDOG_TIMER = "stream-a-evaluation-watchdog.timer"
WATCHDOG_COMMAND = (
    "/usr/local/sbin/stream-a-evaluation-watchdog", "--once",
    "--effect-authorized",
)
RUNTIME_FILES = (
    "owner-intent.json", "owner-heartbeat.json", "watchdog-status.json",
    "restore-intent.json",
)


@dataclass(frozen=True)
class HandlerPaths:
    runtime: Path = Path("/var/lib/local-ai-lab/stream-a-evaluation")
    identity: Path = Path(
        "/etc/local-ai-lab/stream-a-evaluation/watchdog-identity.json")
    checkpoint_root: Path = Path("/var/lib/local-ai-lab/checkpoints")


def _run(runner: Callable[..., subprocess.CompletedProcess], command: tuple[str, ...],
         *, timeout: int, allowed: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess:
    result = runner(command, check=False, capture_output=True, text=True,
                    timeout=timeout)
    if result.returncode not in allowed or result.stderr:
        raise HandlerError("fixed command failed or wrote stderr")
    return result


def _single_json(raw: str, *, key_sets: tuple[frozenset[str], ...]) -> dict[str, object]:
    try:
        encoded = raw.encode("utf-8")
    except UnicodeError as error:
        raise HandlerError("command result is not UTF-8") from error
    if not 0 < len(encoded) <= MAX_COMMAND_RESULT_BYTES:
        raise HandlerError("command result size is invalid")
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise HandlerError("duplicate result key")
            value[key] = item
        return value
    try:
        value = json.loads(raw, object_pairs_hook=pairs)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise HandlerError("command result is invalid JSON") from error
    if not isinstance(value, dict) or frozenset(value) not in key_sets:
        raise HandlerError("command result schema is not exact")
    return value


def _write_private_new(path: Path, value: dict[str, object], *, required_uid: int) -> None:
    write_new_intent(path, value, required_uid=required_uid)


def _write_checkpoint(path: Path, value: dict[str, object], *, required_uid: int) -> None:
    _write_private_new(path, value, required_uid=required_uid)
    descriptor = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _file_digest(path: Path, *, required_uid: int) -> str:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        info = os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != required_uid
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
            raise HandlerError("retained runtime file custody is weak")
        if not 0 < info.st_size <= MAX_RUNTIME_EVIDENCE_BYTES:
            raise HandlerError("retained runtime file size is invalid")
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = -1
            raw = stream.read(info.st_size + 1)
            if len(raw) != info.st_size:
                raise HandlerError("retained runtime file changed while reading")
            return hashlib.sha256(raw).hexdigest()
    finally:
        if descriptor != -1:
            os.close(descriptor)


class FixedHandlers:
    """Effect handlers with fixed commands and fail-closed observations."""

    def __init__(
        self,
        plan: LivePlan,
        *,
        runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
        outcome_verifier: Callable[[str], VerifiedOutcome],
        restored_verifier: Callable[[LivePlan], bool],
        paths: HandlerPaths = HandlerPaths(),
        clock: Callable[[], int] = lambda: int(time.time()),
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        required_uid: int = 0,
    ):
        self.plan = plan
        self.runner = runner
        self.outcome_verifier = outcome_verifier
        self.restored_verifier = restored_verifier
        self.paths = paths
        self.clock = clock
        self.monotonic = monotonic
        self.sleep = sleep
        self.required_uid = required_uid
        self._restored = False
        self._checkpoint_created = False

    @property
    def checkpoint(self) -> Path:
        return self.paths.checkpoint_root / Path(self.plan.checkpoint).name

    def _unit_state(self, unit: str) -> tuple[str, str]:
        enabled = _run(self.runner, ("systemctl", "is-enabled", unit), timeout=10,
                       allowed=(0, 1)).stdout.strip()
        active = _run(self.runner, ("systemctl", "is-active", unit), timeout=10,
                      allowed=(0, 3)).stdout.strip()
        return enabled, active

    def arm(self, plan: LivePlan) -> None:
        if plan != self.plan:
            raise HandlerError("handler cannot switch plans")
        if os.geteuid() != self.required_uid:
            raise HandlerError("arming requires the fixed uid")
        if self.checkpoint.exists():
            raise HandlerError("checkpoint already exists")
        self.checkpoint.mkdir(mode=0o700, parents=False)
        self._checkpoint_created = True
        os.chmod(self.checkpoint, 0o700)
        if (self.checkpoint.stat().st_uid != self.required_uid
                or stat.S_IMODE(self.checkpoint.stat().st_mode) != 0o700):
            raise HandlerError("checkpoint custody is weak")
        unit_states = {
            unit: list(self._unit_state(unit)) for unit in (
                OWNER_UNIT, HEARTBEAT_UNIT, HEARTBEAT_TIMER,
                WATCHDOG_UNIT, WATCHDOG_TIMER,
            )
        }
        if any(state != ["disabled", "inactive"]
               for state in unit_states.values()):
            raise HandlerError("F6 prestate is not disabled and inactive")
        prestate = {
            "lease_id": plan.lease_id,
            "generation": 1,
            "units": unit_states,
        }
        _write_checkpoint(self.checkpoint / "prestate.json", prestate,
                          required_uid=self.required_uid)
        _write_private_new(self.paths.runtime / "owner-intent.json",
                           plan.owner_intent(), required_uid=self.required_uid)
        _run(self.runner, ("systemctl", "enable", "--now", HEARTBEAT_TIMER),
             timeout=30)
        _run(self.runner, ("systemctl", "enable", "--now", WATCHDOG_TIMER),
             timeout=30)
        deadline = self.monotonic() + 20
        while True:
            try:
                identity = load_identity(self.paths.identity,
                                         required_uid=self.required_uid)
                heartbeat = load_owner_heartbeat(
                    self.paths.runtime / "owner-heartbeat.json",
                    identity=identity, now_epoch=self.clock(),
                    required_uid=self.required_uid)
                if (identity.lease_id == plan.lease_id
                        and identity.generation == 1
                        and identity.owner_id == plan.owner_id
                        and owner_process_matches(identity)
                        and heartbeat.expires_epoch > self.clock()
                        and self._unit_state(HEARTBEAT_TIMER)
                            == ("enabled", "active")
                        and self._unit_state(WATCHDOG_TIMER)
                            == ("enabled", "active")):
                    return
            except (OSError, ValueError, WatchdogBoundaryError, HandlerError):
                pass
            if self.monotonic() >= deadline:
                raise HandlerError("owner/watchdog arm did not become exact")
            self.sleep(0.2)

    def workload(self, name: str) -> VerifiedOutcome:
        commands = {
            "d4-candidate-h": (D4_COMMAND, 36 * 60),
            "m3-nlu-calibration": (M3_COMMAND, 20 * 60 + 30),
        }
        if name not in commands:
            raise HandlerError("workload is not fixed")
        command, timeout = commands[name]
        _run(self.runner, command, timeout=timeout)
        outcome = self.outcome_verifier(name)
        if not isinstance(outcome, VerifiedOutcome) or outcome.name != name:
            raise HandlerError("workload verifier returned a foreign outcome")
        return outcome

    def recover(self, plan: LivePlan) -> bool:
        if plan != self.plan:
            raise HandlerError("handler cannot switch plans")
        if not self._checkpoint_created:
            return False
        _run(self.runner, ("systemctl", "stop", OWNER_UNIT), timeout=30,
             allowed=(0, 5))
        if not (self.paths.runtime / "lease.json").exists():
            _run(self.runner, ("systemctl", "disable", "--now", WATCHDOG_TIMER),
                 timeout=30)
            _run(self.runner, ("systemctl", "disable", "--now", HEARTBEAT_TIMER),
                 timeout=30)
            if self.restored_verifier(plan) is not True:
                return False
            self._restored = True
            return True
        deadline = self.monotonic() + plan.owner_intent()["heartbeat_timeout"] + 10
        while self.clock() < plan.restore_deadline_epoch:
            result = _run(self.runner, WATCHDOG_COMMAND, timeout=90)
            value = _single_json(
                result.stdout,
                key_sets=(frozenset(("decision", "effects")),
                          frozenset(("decision", "effects", "result"))),
            )
            if value["effects"] == "recovered":
                result_value = value.get("result")
                if (value.get("decision") not in ("owner-absent", "restore-deadline")
                        or not isinstance(result_value, dict)
                        or set(result_value) != {"entrypoint", "stdout"}
                        or result_value.get("entrypoint") != "restored"
                        or not isinstance(result_value.get("stdout"), str)):
                    return False
                if self.restored_verifier(plan) is not True:
                    return False
                self._restored = True
                return True
            if value["effects"] not in ("not-attempted", "failed-closed"):
                return False
            if self.monotonic() >= deadline:
                return False
            self.sleep(1)
        return False

    def mark_restored(self, plan: LivePlan) -> None:
        """Record the normal restore path only after independent verification."""
        if plan != self.plan or self.restored_verifier(plan) is not True:
            raise HandlerError("normal restoration is unconfirmed")
        self._restored = True

    def cleanup(self, plan: LivePlan) -> None:
        if plan != self.plan:
            raise HandlerError("handler cannot switch plans")
        if not self._restored:
            if self.restored_verifier(plan) is not True:
                raise HandlerError("cleanup requires confirmed restoration")
            self._restored = True
        retained: dict[str, str] = {}
        for name in RUNTIME_FILES:
            path = self.paths.runtime / name
            if path.exists():
                retained[name] = _file_digest(path, required_uid=self.required_uid)
        if self.paths.identity.exists():
            retained["watchdog-identity.json"] = _file_digest(
                self.paths.identity, required_uid=self.required_uid)
        _write_checkpoint(self.checkpoint / "retained-runtime-digests.json",
                          {"files": retained}, required_uid=self.required_uid)
        _run(self.runner, ("systemctl", "disable", "--now", WATCHDOG_TIMER),
             timeout=30)
        _run(self.runner, ("systemctl", "disable", "--now", HEARTBEAT_TIMER),
             timeout=30)
        _run(self.runner, ("systemctl", "stop", OWNER_UNIT), timeout=30,
             allowed=(0, 5))
        if self.restored_verifier(plan) is not True:
            raise HandlerError("restoration drifted during cleanup")
        for name in RUNTIME_FILES:
            try:
                (self.paths.runtime / name).unlink()
            except FileNotFoundError:
                pass
        try:
            self.paths.identity.unlink()
        except FileNotFoundError:
            pass
        if (self.paths.runtime / "lease.json").exists() \
                or (self.paths.runtime / "lease.lock").exists() \
                or (self.paths.runtime / "lease.operation.lock").exists():
            raise HandlerError("lease state remains after cleanup")
        if (self._unit_state(HEARTBEAT_TIMER) != ("disabled", "inactive")
                or self._unit_state(WATCHDOG_TIMER) != ("disabled", "inactive")):
            raise HandlerError("F6 timers remain armed after cleanup")
