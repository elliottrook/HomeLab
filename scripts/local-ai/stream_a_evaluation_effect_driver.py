"""Fixed intent/entrypoint driver boundary for Stream A evaluation.

There is deliberately no CLI.  Arm, workload verification, recovery and
cleanup are supplied by a later reviewed composition root.  This module owns
only canonical intent custody and exact entrypoint invocation.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
from typing import Callable

from stream_a_evaluation_live_plan import INTENT_ROOT, LivePlan
from stream_a_evaluation_sequence import VerifiedOutcome


class EffectDriverError(RuntimeError):
    pass


MAX_INTENT_BYTES = 16 * 1024
MAX_RESULT_BYTES = 16 * 1024


def _unique_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise EffectDriverError("entrypoint result contains duplicate keys")
        value[key] = item
    return value


def canonical_bytes(value: dict[str, object]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def write_new_intent(path: Path, value: dict[str, object], *, required_uid: int = 0) -> None:
    parent = path.parent.stat()
    if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != required_uid
            or stat.S_IMODE(parent.st_mode) != 0o700):
        raise EffectDriverError("intent parent custody is weak")
    if os.path.lexists(path):
        raise EffectDriverError("phase intent already exists")
    raw = canonical_bytes(value)
    if not 0 < len(raw) <= MAX_INTENT_BYTES:
        raise EffectDriverError("phase intent size is invalid")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    finally:
        if descriptor != -1:
            os.close(descriptor)
    directory = os.open(parent if isinstance(parent, str) else path.parent,
                        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def decode_result(raw: str) -> dict[str, object]:
    encoded = raw.encode()
    if not 0 < len(encoded) <= MAX_RESULT_BYTES:
        raise EffectDriverError("entrypoint result size is invalid")
    try:
        value = json.loads(raw, object_pairs_hook=_unique_pairs)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise EffectDriverError("entrypoint result is invalid JSON") from error
    if not isinstance(value, dict):
        raise EffectDriverError("entrypoint result is not an object")
    return value


class FixedEffectDriver:
    def __init__(
        self,
        plan: LivePlan,
        *,
        runner: Callable[..., subprocess.CompletedProcess],
        arm_handler: Callable[[LivePlan], None],
        workload_handler: Callable[[str], VerifiedOutcome],
        recovery_handler: Callable[[LivePlan], bool],
        cleanup_handler: Callable[[LivePlan], None],
        path_mapper: Callable[[Path], Path] = lambda path: path,
        required_uid: int = 0,
    ):
        self.plan = plan
        self.runner = runner
        self.arm_handler = arm_handler
        self.workload_handler = workload_handler
        self.recovery_handler = recovery_handler
        self.cleanup_handler = cleanup_handler
        self.path_mapper = path_mapper
        self.required_uid = required_uid

    def arm(self, plan: LivePlan) -> None:
        self._same_plan(plan)
        self.arm_handler(plan)

    def phase(self, phase: str, payload: dict[str, object]) -> dict[str, object]:
        workload_name = None
        if phase == "start":
            workload_name = payload.get("workload_name")
        elif phase == "outcome":
            workload_name = payload.get("name")
        command = self.plan.command(phase, workload_name=workload_name)
        fixed_path = Path(command[4])
        if fixed_path.parent != Path(INTENT_ROOT):
            raise EffectDriverError("intent command escaped the fixed root")
        target = self.path_mapper(fixed_path)
        write_new_intent(target, payload, required_uid=self.required_uid)
        result = self.runner(command, check=False, capture_output=True, text=True, timeout=60)
        if result.returncode != 0 or result.stderr:
            raise EffectDriverError("entrypoint invocation failed or wrote stderr")
        return decode_result(result.stdout)

    def run_workload(self, name: str) -> VerifiedOutcome:
        if name not in ("d4-candidate-h", "m3-nlu-calibration"):
            raise EffectDriverError("workload is not fixed")
        return self.workload_handler(name)

    def recover(self, plan: LivePlan) -> bool:
        self._same_plan(plan)
        return self.recovery_handler(plan)

    def cleanup(self, plan: LivePlan) -> None:
        self._same_plan(plan)
        self.cleanup_handler(plan)

    def _same_plan(self, plan: LivePlan) -> None:
        if plan != self.plan:
            raise EffectDriverError("driver cannot switch plans")
