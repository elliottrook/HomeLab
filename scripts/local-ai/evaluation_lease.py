"""Pure contract for the endpoint-retaining Stream A evaluation lease.

This module deliberately has no Proxmox, systemd, SSH, HTTP or filesystem
effects.  A later, separately approved adapter may implement this contract.
The accepted llama service remains active; only registered competing consumers
are quiesced for the bounded evaluation sequence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EvaluationLeaseError(ValueError):
    """The proposed lease, workload or recovery state is unsafe."""


ACCEPTED_MODEL = "Qwen3.5 9B Q4_K_M"
ACCEPTED_BACKEND = "llama.cpp b11429 SYCL/Level Zero"
ACCEPTED_ENDPOINT = "http://192.168.70.12:11435/v1/chat/completions"
LEASE_MODE = "stream-a-endpoint-retaining-evaluation-v1"

D4_DIGEST = "03b0ad74a862ee04de75e012f52f6662c61192b69b279ea4d1d66c80d9ff9153"
M3_STAGE_MANIFEST_DIGEST = "69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165"

# The final fifteen minutes are never borrowable by either workload.
WINDOW_SECONDS = 90 * 60
RESTORE_RESERVE_SECONDS = 15 * 60
EFFECT_DEADLINE_SECONDS = WINDOW_SECONDS - RESTORE_RESERVE_SECONDS
SETUP_BUDGET_SECONDS = 10 * 60
D4_BUDGET_SECONDS = 36 * 60
M3_BUDGET_SECONDS = 20 * 60

QUIESCE_TARGETS = (
    "lxc104:aster-agent.service",
    "lxc116:aster-speech.service",
    "lxc114:news-aggregator-ingest.timer",
    "lxc114:news-aggregator-digest.timer",
)
QUIESCE_STATES = tuple((target, "masked+inactive") for target in QUIESCE_TARGETS)
BACKEND_TARGET = "lxc110:aster-llama.service"
PRODUCTION_BASELINE_STATES = tuple((target, "enabled+active") for target in QUIESCE_TARGETS)


class LeaseState(str, Enum):
    READY = "ready"
    QUIESCING = "quiescing"
    RUNNING = "running"
    RESTORING = "restoring"
    FAILED = "failed"


@dataclass(frozen=True)
class WorkloadSpec:
    name: str
    packet_digest: str
    max_calls: int
    max_seconds: int
    journal_name: str
    result_name: str


WORKLOADS = (
    WorkloadSpec(
        name="d4-candidate-g",
        packet_digest=D4_DIGEST,
        max_calls=36,
        max_seconds=D4_BUDGET_SECONDS,
        journal_name="d4-candidate-g.journal.jsonl",
        result_name="d4-candidate-g.result.json",
    ),
    WorkloadSpec(
        name="m3-nlu-calibration",
        packet_digest=M3_STAGE_MANIFEST_DIGEST,
        max_calls=60,
        max_seconds=M3_BUDGET_SECONDS,
        journal_name="m3-nlu-calibration.journal.jsonl",
        result_name="m3-nlu-calibration.result.json",
    ),
)


@dataclass(frozen=True)
class ProductionBaseline:
    """Exact states captured before quiescence and required after restore."""

    units: tuple[tuple[str, str], ...]
    timers: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class Admission:
    """Source-bound observations required before any consumer is stopped."""

    lease_id: str
    generation: int
    backup_receipt: str
    f2_receipt: str
    f3_receipt: str
    model: str
    backend: str
    endpoint: str
    backend_active: bool
    endpoint_authenticated: bool
    endpoint_idle: bool
    gpu_holders: tuple[str, ...]
    registered_targets: tuple[str, ...]
    quiesced_targets: tuple[str, ...]
    baseline: ProductionBaseline
    watchdog_independent: bool
    hard_deadline_epoch: int
    restore_deadline_epoch: int


@dataclass(frozen=True)
class WorkloadOutcome:
    lease_id: str
    generation: int
    name: str
    packet_digest: str
    status: str
    journal_digest: str
    result_digest: str
    calls: int
    elapsed_seconds: int
    tool_free: bool
    transport_uncertain: bool = False


@dataclass(frozen=True)
class WatchdogDecision:
    action: str
    reason: str


def validate_baseline(value: ProductionBaseline) -> None:
    """Require the complete, ordered, duplicate-free production baseline."""
    observed = tuple(value.units) + tuple(value.timers)
    expected = PRODUCTION_BASELINE_STATES
    if observed != expected or len({target for target, _ in observed}) != len(expected):
        raise EvaluationLeaseError("production baseline is not the exact four-target schema")


def workload(name: str) -> WorkloadSpec:
    for item in WORKLOADS:
        if item.name == name:
            return item
    raise EvaluationLeaseError("workload is not in the frozen two-workload bundle")


def validate_window(*, now_epoch: int, hard_deadline_epoch: int,
                    restore_deadline_epoch: int) -> None:
    if hard_deadline_epoch != now_epoch + EFFECT_DEADLINE_SECONDS:
        raise EvaluationLeaseError("effect deadline is not the fixed seventy-five minutes")
    if restore_deadline_epoch != now_epoch + WINDOW_SECONDS:
        raise EvaluationLeaseError("total lease window is not the fixed ninety minutes")
    if SETUP_BUDGET_SECONDS + D4_BUDGET_SECONDS + M3_BUDGET_SECONDS > EFFECT_DEADLINE_SECONDS:
        raise EvaluationLeaseError("fixed workload budgets exceed the effect window")


def validate_admission(value: Admission, *, now_epoch: int) -> None:
    if not value.lease_id or value.generation < 1:
        raise EvaluationLeaseError("lease identity is invalid")
    if not value.backup_receipt or not value.f2_receipt or not value.f3_receipt:
        raise EvaluationLeaseError("fresh F2, F3 and backup receipts are required")
    if value.model != ACCEPTED_MODEL or value.backend != ACCEPTED_BACKEND:
        raise EvaluationLeaseError("accepted model/backend identity does not match")
    if value.endpoint != ACCEPTED_ENDPOINT:
        raise EvaluationLeaseError("endpoint is not the accepted local endpoint")
    if not (value.backend_active and value.endpoint_authenticated and value.endpoint_idle):
        raise EvaluationLeaseError("backend must be active, authenticated and idle")
    if tuple(value.gpu_holders) != (BACKEND_TARGET,):
        raise EvaluationLeaseError("GPU inference slot has an unknown or missing holder")
    if tuple(value.registered_targets) != QUIESCE_TARGETS:
        raise EvaluationLeaseError("registered consumer set is not exact")
    if value.quiesced_targets:
        raise EvaluationLeaseError("pre-quiescence admission claims consumers are already stopped")
    validate_baseline(value.baseline)
    if not value.watchdog_independent:
        raise EvaluationLeaseError("independent watchdog is required")
    validate_window(now_epoch=now_epoch, hard_deadline_epoch=value.hard_deadline_epoch,
                    restore_deadline_epoch=value.restore_deadline_epoch)


def plan() -> tuple[str, ...]:
    """Return the only permitted order for the effectful adapter."""
    return (
        "acquire-evaluation-lock",
        "verify-fresh-f2-f3-backup-and-source-receipts",
        "capture-exact-production-unit-and-timer-baseline",
        "verify-accepted-backend-active-authenticated-idle-and-exclusive",
        "quiesce-registered-aster-speech-and-news-consumers",
        "verify-consumer-quiescence-with-backend-still-active",
        "run-d4-candidate-g-once-to-its-separate-journal-and-result",
        "run-m3-nlu-calibration-once-to-its-separate-journal-and-result",
        "restore-exact-production-unit-and-timer-baseline",
        "verify-production-health-authentication-and-gpu-idleness",
        "release-evaluation-lock-only-after-postcheck",
    )


def validate_post_quiescence(value: Admission, *,
                             observed_states: tuple[tuple[str, str], ...],
                             backend_active: bool, endpoint_authenticated: bool,
                             endpoint_idle: bool, gpu_holders: tuple[str, ...]) -> None:
    """Validate the second boundary before either model workload starts."""
    if tuple(observed_states) != QUIESCE_STATES:
        raise EvaluationLeaseError("post-quiescence units are not exactly masked and inactive")
    if any(state in {"active", "running"} for _, state in observed_states):
        raise EvaluationLeaseError("a registered consumer remains active")
    if not (backend_active and endpoint_authenticated and endpoint_idle):
        raise EvaluationLeaseError("post-quiescence backend is not healthy and idle")
    if tuple(gpu_holders) != (BACKEND_TARGET,):
        raise EvaluationLeaseError("post-quiescence GPU holder is not the accepted backend")


def validate_outcome(value: WorkloadOutcome, *, expected: WorkloadSpec,
                     lease_id: str, generation: int) -> None:
    if (value.lease_id != lease_id or value.generation != generation
            or value.name != expected.name
            or value.packet_digest != expected.packet_digest
            or value.status not in {"completed", "rejected"}):
        raise EvaluationLeaseError("workload outcome does not match its fixed spec")
    if (value.calls < 0 or value.calls > expected.max_calls
            or value.elapsed_seconds < 0
            or value.elapsed_seconds > expected.max_seconds):
        raise EvaluationLeaseError("workload bound exceeded")
    if not value.tool_free or value.transport_uncertain:
        raise EvaluationLeaseError("tool use or transport uncertainty is not admissible")
    if not value.journal_digest or not value.result_digest:
        raise EvaluationLeaseError("separate journal and result digests are required")


def next_workload(*, completed: tuple[str, ...], expected_lease_id: str,
                  expected_generation: int,
                  outcome: WorkloadOutcome | None = None) -> WorkloadSpec | None:
    """Allow M3 only after a terminal, unambiguous D4 outcome."""
    if outcome is not None:
        validate_outcome(outcome, expected=workload(outcome.name),
                         lease_id=expected_lease_id, generation=expected_generation)
        if outcome.transport_uncertain:
            raise EvaluationLeaseError("uncertain D4 outcome forbids the next workload")
    if completed == ():
        if outcome is not None:
            raise EvaluationLeaseError("an outcome cannot precede the first workload")
        return WORKLOADS[0]
    if completed == (WORKLOADS[0].name,):
        if outcome is None or outcome.name != WORKLOADS[0].name:
            raise EvaluationLeaseError("M3 requires the terminal D4 outcome for this lease")
        return WORKLOADS[1]
    if completed == tuple(item.name for item in WORKLOADS):
        if outcome is None or outcome.name != WORKLOADS[1].name:
            raise EvaluationLeaseError("completion requires the terminal M3 outcome for this lease")
        validate_outcome(outcome, expected=WORKLOADS[1],
                         lease_id=expected_lease_id, generation=expected_generation)
        return None
    raise EvaluationLeaseError("workload sequence is not the frozen D4-then-M3 order")


def watchdog_decision(*, now_epoch: int, heartbeat_epoch: int,
                      heartbeat_timeout: int, hard_deadline_epoch: int,
                      restore_deadline_epoch: int, owner_present: bool) -> WatchdogDecision:
    if now_epoch >= restore_deadline_epoch:
        return WatchdogDecision("recover", "restore-deadline")
    if now_epoch >= hard_deadline_epoch:
        return WatchdogDecision("recover", "hard-deadline")
    if not owner_present:
        return WatchdogDecision("recover", "owner-absent")
    if now_epoch - heartbeat_epoch > heartbeat_timeout:
        return WatchdogDecision("recover", "heartbeat-expired")
    return WatchdogDecision("continue", "lease-healthy")


def validate_restoration(*, restored: ProductionBaseline,
                         expected: ProductionBaseline,
                         backend_active: bool, endpoint_authenticated: bool,
                         endpoint_idle: bool,
                         gpu_holders: tuple[str, ...]) -> None:
    if restored != expected:
        raise EvaluationLeaseError("production unit or timer baseline drifted")
    validate_baseline(expected)
    if not (backend_active and endpoint_authenticated and endpoint_idle):
        raise EvaluationLeaseError("backend did not restore healthy, authenticated and idle")
    if tuple(gpu_holders) != (BACKEND_TARGET,):
        raise EvaluationLeaseError("accepted backend is not the exact restored GPU holder")
