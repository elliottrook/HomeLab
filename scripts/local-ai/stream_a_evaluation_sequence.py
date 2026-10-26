"""Effect-driver-independent sequence for the future Stream A live run.

The module performs no effects itself.  A separately reviewed driver must
implement root custody, entrypoint invocation, workload execution and recovery.
This coordinator makes the serial order and uncertain-recovery behavior
testable without touching a host or model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from stream_a_evaluation_live_plan import LivePlan


class SequenceError(RuntimeError):
    pass


class SequenceRecoveryUncertain(SequenceError):
    pass


@dataclass(frozen=True)
class VerifiedOutcome:
    name: str
    journal_digest: str
    result_digest: str
    calls: int
    elapsed_seconds: int


class EffectDriver(Protocol):
    def arm(self, plan: LivePlan) -> None: ...
    def phase(self, phase: str, payload: dict[str, object]) -> dict[str, object]: ...
    def run_workload(self, name: str) -> VerifiedOutcome: ...
    def recover(self, plan: LivePlan) -> bool: ...
    def cleanup(self, plan: LivePlan) -> None: ...


_EXPECTED = {
    "acquire": "prepared",
    "quiesce": "quiescing",
    "post-quiescence": "post-quiescence-recorded",
    "start": "workload-start-recorded",
    "outcome": "outcome-recorded",
    "restore": "restored",
}


def _phase(driver: EffectDriver, phase: str,
           payload: dict[str, object]) -> dict[str, object]:
    result = driver.phase(phase, payload)
    if not isinstance(result, dict) or result.get("effects") != _EXPECTED[phase]:
        raise SequenceError(f"{phase} result is not exact")
    return result


def execute(plan: LivePlan, driver: EffectDriver,
            *, clock: Callable[[], int]) -> tuple[VerifiedOutcome, VerifiedOutcome]:
    """Execute one fixed D4 then M3 transaction through a reviewed driver.

    The caller must ensure ``clock`` is wall-clock epoch time.  Workload result
    files are not trusted here: ``driver.run_workload`` must return only a
    separately verified, bounded outcome.
    """
    cleanup_allowed = False
    try:
        driver.arm(plan)
        _phase(driver, "acquire", plan.acquire())
        _phase(driver, "quiesce", plan.quiesce(clock()))
        _phase(driver, "post-quiescence", plan.post_quiescence(clock()))

        _phase(driver, "start", plan.start("d4-candidate-h", clock()))
        d4 = driver.run_workload("d4-candidate-h")
        if d4.name != "d4-candidate-h":
            raise SequenceError("D4 driver returned a foreign outcome")
        _phase(driver, "outcome", plan.outcome(
            name=d4.name, journal_digest=d4.journal_digest,
            result_digest=d4.result_digest, calls=d4.calls,
            elapsed_seconds=d4.elapsed_seconds, now_epoch=clock(),
        ))

        _phase(driver, "start", plan.start("m3-nlu-calibration", clock()))
        m3 = driver.run_workload("m3-nlu-calibration")
        if m3.name != "m3-nlu-calibration":
            raise SequenceError("M3 driver returned a foreign outcome")
        _phase(driver, "outcome", plan.outcome(
            name=m3.name, journal_digest=m3.journal_digest,
            result_digest=m3.result_digest, calls=m3.calls,
            elapsed_seconds=m3.elapsed_seconds, now_epoch=clock(),
        ))

        _phase(driver, "restore", plan.restore(recovery=False))
        cleanup_allowed = True
        return d4, m3
    except BaseException as error:
        try:
            recovered = driver.recover(plan)
        except BaseException as recovery_error:
            raise SequenceRecoveryUncertain(
                "recovery raised; retain state and locks"
            ) from recovery_error
        if recovered is not True:
            raise SequenceRecoveryUncertain(
                "recovery unconfirmed; retain state and locks"
            ) from error
        cleanup_allowed = True
        raise
    finally:
        if cleanup_allowed:
            driver.cleanup(plan)
