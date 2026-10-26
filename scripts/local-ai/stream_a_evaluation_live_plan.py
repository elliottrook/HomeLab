"""Pure plan builder for the future candidate-H plus M3 evaluation run.

This module has no filesystem, subprocess, systemd, network or model effects.
It converts already accepted evidence identities into the exact phase payloads
required by ``evaluation_lease_entrypoint.py``.  A later reviewed orchestrator
must own custody, observations, execution and recovery.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from evaluation_lease import (
    ACCEPTED_BACKEND,
    ACCEPTED_ENDPOINT,
    ACCEPTED_MODEL,
    BACKEND_TARGET,
    D4_DIGEST,
    EFFECT_DEADLINE_SECONDS,
    M3_STAGE_MANIFEST_DIGEST,
    PRODUCTION_BASELINE_STATES,
    QUIESCE_STATES,
    QUIESCE_TARGETS,
    RESTORE_RESERVE_SECONDS,
    WINDOW_SECONDS,
)


class LivePlanError(ValueError):
    pass


GENERATION = 1
HEARTBEAT_TIMEOUT_SECONDS = 45
_CYCLE = re.compile(r"^20[0-9]{2}-[01][0-9]-[0-3][0-9]$")
_NONCE = re.compile(r"^[0-9a-f]{16}$")
_HEX = "[0-9a-f]{64}"
_BACKUP = re.compile(rf"^retained-archive-integrity-sha256:{_HEX}$")
_F2 = re.compile(rf"^f2-result-sha256:{_HEX}$")
_F3 = re.compile(rf"^f3-receipt-sha256:{_HEX}$")
_ADMISSION = re.compile(rf"^stream-a-evaluation-admission-sha256:{_HEX}$")

INTENT_ROOT = "/var/lib/local-ai-lab/stream-a-evaluation/intents"
STATE_PATH = "/var/lib/local-ai-lab/stream-a-evaluation/lease.json"
OWNER_INTENT_PATH = "/var/lib/local-ai-lab/stream-a-evaluation/owner-intent.json"
CHECKPOINT_ROOT = "/var/lib/local-ai-lab/checkpoints"
ENTRYPOINT = "/usr/local/sbin/stream-a-evaluation-lease"
D4_COMMAND = (
    "pct", "exec", "104", "--", "systemctl", "start",
    "aster-d4-candidate-h.service",
)
M3_COMMAND = (
    "pct", "exec", "110", "--", "sh", "-c",
    "cd /var/lib/aster-nlu-calibration/nlu-calibration-v1 && "
    "exec timeout --signal=TERM --kill-after=10s 1230s /usr/bin/python3 "
    "nlu_calibration_runner.py --source cases.json --release release.json "
    "--development nlu-development-v1.json --output run.json "
    "--journal attempt-journal.jsonl --key-file /etc/aster-llama-api-keys",
)


def _require(pattern: re.Pattern[str], value: str, name: str) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise LivePlanError(f"{name} is invalid")
    return value


def _baseline() -> dict[str, list[list[str]]]:
    return {
        "units": [list(item) for item in PRODUCTION_BASELINE_STATES[:2]],
        "timers": [list(item) for item in PRODUCTION_BASELINE_STATES[2:]],
    }


@dataclass(frozen=True)
class AcceptedEvidence:
    cycle_date: str
    nonce: str
    now_epoch: int
    backup_receipt: str
    f2_receipt: str
    f3_receipt: str
    admission_receipt: str

    def validate(self) -> None:
        _require(_CYCLE, self.cycle_date, "cycle_date")
        _require(_NONCE, self.nonce, "nonce")
        if type(self.now_epoch) is not int or self.now_epoch <= 0:
            raise LivePlanError("now_epoch is invalid")
        _require(_BACKUP, self.backup_receipt, "backup_receipt")
        _require(_F2, self.f2_receipt, "f2_receipt")
        _require(_F3, self.f3_receipt, "f3_receipt")
        _require(_ADMISSION, self.admission_receipt, "admission_receipt")


@dataclass(frozen=True)
class LivePlan:
    evidence: AcceptedEvidence

    def __post_init__(self) -> None:
        self.evidence.validate()

    @property
    def lease_id(self) -> str:
        return f"stream-a-evaluation-{self.evidence.cycle_date}-{self.evidence.nonce}"

    @property
    def owner_id(self) -> str:
        return f"stream-a-evaluation-owner-{self.evidence.nonce}"

    @property
    def checkpoint(self) -> str:
        return f"{CHECKPOINT_ROOT}/stream-a-evaluation-live-{self.evidence.cycle_date}-{self.evidence.nonce}"

    @property
    def hard_deadline_epoch(self) -> int:
        return self.evidence.now_epoch + EFFECT_DEADLINE_SECONDS

    @property
    def restore_deadline_epoch(self) -> int:
        return self.evidence.now_epoch + WINDOW_SECONDS

    def owner_intent(self) -> dict[str, object]:
        return {
            "lease_id": self.lease_id,
            "generation": GENERATION,
            "heartbeat_timeout": HEARTBEAT_TIMEOUT_SECONDS,
            "owner_id": self.owner_id,
        }

    def acquire(self) -> dict[str, object]:
        return {
            "lease_id": self.lease_id,
            "generation": GENERATION,
            "backup_receipt": self.evidence.backup_receipt,
            "f2_receipt": self.evidence.f2_receipt,
            "f3_receipt": self.evidence.f3_receipt,
            "model": ACCEPTED_MODEL,
            "backend": ACCEPTED_BACKEND,
            "endpoint": ACCEPTED_ENDPOINT,
            "backend_active": True,
            "endpoint_authenticated": True,
            "endpoint_idle": True,
            "gpu_holders": [BACKEND_TARGET],
            "registered_targets": list(QUIESCE_TARGETS),
            "quiesced_targets": [],
            "baseline": _baseline(),
            "watchdog_independent": True,
            "hard_deadline_epoch": self.hard_deadline_epoch,
            "restore_deadline_epoch": self.restore_deadline_epoch,
            "now_epoch": self.evidence.now_epoch,
            "admission_receipt": self.evidence.admission_receipt,
        }

    def quiesce(self, now_epoch: int) -> dict[str, object]:
        return self._heartbeat_bound(now_epoch)

    def heartbeat(self, now_epoch: int) -> dict[str, object]:
        return {
            "lease_id": self.lease_id, "generation": GENERATION,
            "now_epoch": self._runtime_epoch(now_epoch),
        }

    def post_quiescence(self, now_epoch: int) -> dict[str, object]:
        return {
            "admission": self.acquire(),
            "observed_states": [list(item) for item in QUIESCE_STATES],
            "backend_active": True,
            "endpoint_authenticated": True,
            "endpoint_idle": True,
            "gpu_holders": [BACKEND_TARGET],
            "now_epoch": self._runtime_epoch(now_epoch),
            "heartbeat_timeout": HEARTBEAT_TIMEOUT_SECONDS,
        }

    def start(self, workload_name: str, now_epoch: int) -> dict[str, object]:
        if workload_name not in ("d4-candidate-h", "m3-nlu-calibration"):
            raise LivePlanError("workload_name is not fixed")
        return {
            "lease_id": self.lease_id, "generation": GENERATION,
            "workload_name": workload_name,
            "now_epoch": self._runtime_epoch(now_epoch),
            "heartbeat_timeout": HEARTBEAT_TIMEOUT_SECONDS,
        }

    def outcome(self, *, name: str, journal_digest: str, result_digest: str,
                calls: int, elapsed_seconds: int, now_epoch: int) -> dict[str, object]:
        packets = {
            "d4-candidate-h": D4_DIGEST,
            "m3-nlu-calibration": M3_STAGE_MANIFEST_DIGEST,
        }
        if name not in packets:
            raise LivePlanError("outcome workload is not fixed")
        for value, field in ((journal_digest, "journal_digest"),
                             (result_digest, "result_digest")):
            _require(re.compile(rf"^{_HEX}$"), value, field)
        if type(calls) is not int or calls < 0:
            raise LivePlanError("calls is invalid")
        limits = {"d4-candidate-h": 36, "m3-nlu-calibration": 60}
        if calls > limits[name]:
            raise LivePlanError("calls exceed the fixed workload bound")
        elapsed_limits = {"d4-candidate-h": 36 * 60, "m3-nlu-calibration": 20 * 60}
        if (type(elapsed_seconds) is not int or elapsed_seconds < 0
                or elapsed_seconds > elapsed_limits[name]):
            raise LivePlanError("elapsed_seconds is invalid")
        return {
            "lease_id": self.lease_id, "generation": GENERATION,
            "name": name, "packet_digest": packets[name], "status": "completed",
            "journal_digest": journal_digest, "result_digest": result_digest,
            "calls": calls, "elapsed_seconds": elapsed_seconds,
            "tool_free": True, "transport_uncertain": False,
            "now_epoch": self._runtime_epoch(now_epoch),
            "heartbeat_timeout": HEARTBEAT_TIMEOUT_SECONDS,
        }

    def restore(self, *, recovery: bool) -> dict[str, object]:
        if type(recovery) is not bool:
            raise LivePlanError("recovery must be boolean")
        return {
            "lease_id": self.lease_id, "generation": GENERATION,
            "restored_baseline": _baseline(), "backend_active": True,
            "endpoint_authenticated": True, "endpoint_idle": True,
            "gpu_holders": [BACKEND_TARGET], "recovery": recovery,
        }

    def command(self, phase: str) -> tuple[str, ...]:
        if phase not in (
            "acquire", "quiesce", "post-quiescence", "heartbeat", "start",
            "outcome", "restore",
        ):
            raise LivePlanError("phase is not fixed")
        return (
            ENTRYPOINT, "--phase", phase, "--intent",
            f"{INTENT_ROOT}/{phase}.json", "--effect-authorized",
        )

    def _heartbeat_bound(self, now_epoch: int) -> dict[str, object]:
        return {
            "lease_id": self.lease_id, "generation": GENERATION,
            "now_epoch": self._runtime_epoch(now_epoch),
            "heartbeat_timeout": HEARTBEAT_TIMEOUT_SECONDS,
        }

    def _runtime_epoch(self, now_epoch: int) -> int:
        if type(now_epoch) is not int or not self.evidence.now_epoch <= now_epoch < self.restore_deadline_epoch:
            raise LivePlanError("runtime epoch is outside the fixed lease window")
        return now_epoch


def restoration_reserve_seconds() -> int:
    return RESTORE_RESERVE_SECONDS
