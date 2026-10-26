"""Single fixed composition root for the future Stream A evaluation run.

There is deliberately no CLI.  ``build_runtime`` performs only the reviewed
read-only evidence load and wires fixed production components.  Calling
``EvaluationRuntime.run`` is effectful and remains subject to a later exact
live-run approval and installed packet review.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import time
from typing import Callable

from stream_a_evaluation_effect_driver import FixedEffectDriver
from stream_a_evaluation_evidence_loader import (
    EvidenceExpectation, EvidencePaths, load_accepted_evidence,
)
from stream_a_evaluation_handlers import FixedHandlers, HandlerPaths
from stream_a_evaluation_host_outcome import HostOutcomeVerifier
from stream_a_evaluation_live_plan import LivePlan
from stream_a_evaluation_restored_verifier import RestoredProductionVerifier
from stream_a_evaluation_sequence import VerifiedOutcome, execute


@dataclass(frozen=True)
class EvaluationRuntime:
    plan: LivePlan
    driver: FixedEffectDriver
    clock: Callable[[], int]

    def run(self) -> tuple[VerifiedOutcome, VerifiedOutcome]:
        return execute(self.plan, self.driver, clock=self.clock)


def build_runtime(
    expectation: EvidenceExpectation,
    *,
    now_minute: int,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    clock: Callable[[], int] = lambda: int(time.time()),
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    evidence_paths: EvidencePaths = EvidencePaths(),
    handler_paths: HandlerPaths = HandlerPaths(),
    required_uid: int = 0,
) -> EvaluationRuntime:
    """Load exact evidence, then wire the only production component graph."""
    now_epoch = clock()
    accepted = load_accepted_evidence(
        expectation, now_epoch=now_epoch, now_minute=now_minute,
        paths=evidence_paths, required_uid=required_uid,
    )
    plan = LivePlan(accepted)
    restored = RestoredProductionVerifier(
        runner=runner, runtime_root=handler_paths.runtime, clock=clock,
    )
    outcome = HostOutcomeVerifier(runner=runner)
    handlers = FixedHandlers(
        plan, runner=runner, outcome_verifier=outcome,
        restored_verifier=restored, paths=handler_paths,
        clock=clock, monotonic=monotonic, sleep=sleep,
        required_uid=required_uid,
    )
    driver = FixedEffectDriver(
        plan, runner=runner, arm_handler=handlers.arm,
        workload_handler=handlers.workload,
        recovery_handler=handlers.recover,
        cleanup_handler=handlers.cleanup,
        path_mapper=lambda path: Path(path), required_uid=required_uid,
    )
    return EvaluationRuntime(plan=plan, driver=driver, clock=clock)
