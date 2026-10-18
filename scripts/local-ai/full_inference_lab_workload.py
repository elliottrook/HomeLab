"""Offline contract for the distinct three-request accepted-9B lab smoke."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from typing import Callable, Sequence


LAB_PROFILE = "accepted-9b-direct-control-smoke-v1"
LAB_PORT = "11436"
LAB_COMMAND = (
    "pct", "exec", "110", "--",
    "/usr/local/sbin/aster-llama-lab-smoke",
    "--profile", LAB_PROFILE, "--port", LAB_PORT, "--requests", "3",
)


def lab_command(*, lease_id: str, generation: int) -> tuple[str, ...]:
    return LAB_COMMAND + ("--lease-id", lease_id, "--generation", str(generation))


class LabWorkloadError(ValueError):
    pass


def validate_receipt(value: object, *, lease_id: str, generation: int) -> dict[str, object]:
    """Accept only a content-free receipt from the fixed in-guest wrapper."""
    if not isinstance(value, dict):
        raise LabWorkloadError("lab receipt is not an object")
    if (value.get("schema") != "aster-9b-direct-control-smoke.v1"
            or value.get("profile") != LAB_PROFILE
            or value.get("lease_id") != lease_id
            or value.get("generation") != generation
            or value.get("port") != int(LAB_PORT)
            or value.get("production_service") != "masked-inactive"
            or value.get("credential_exported") is not False
            or value.get("tool_mode") != "disabled"
            or value.get("request_count") != 3
            or not isinstance(value.get("observation_ids"), list)
            or len(value["observation_ids"]) != 3
            or any(not isinstance(item, str) or not item for item in value["observation_ids"])
            or value.get("exit_status") != 0):
        raise LabWorkloadError("lab receipt does not prove the fixed three-request contract")
    return value


def run_fixed_smoke(runner: Callable[[Sequence[str], float], tuple[int, str]], *,
                    lease_id: str, generation: int) -> dict[str, object]:
    """Run only the pinned wrapper; raw answers never cross this boundary."""
    code, output = runner(lab_command(lease_id=lease_id, generation=generation), 300.0)
    if code != 0 or len(output) > 16_384:
        raise LabWorkloadError("fixed lab wrapper failed or exceeded receipt bound")
    try:
        receipt = json.loads(output)
    except json.JSONDecodeError as exc:
        raise LabWorkloadError("fixed lab wrapper did not return JSON") from exc
    return validate_receipt(receipt, lease_id=lease_id, generation=generation)


def run_fixed_smoke_bounded(*, process_factory: Callable[..., object] = subprocess.Popen,
                            heartbeat: Callable[[], None], deadline: float,
                            monotonic: Callable[[], float] = time.monotonic,
                            poll_seconds: float = 1.0, lease_id: str,
                            generation: int) -> dict[str, object]:
    """Run the fixed wrapper in a process group with heartbeat/deadline checks."""
    process = process_factory(lab_command(lease_id=lease_id, generation=generation), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, start_new_session=True)
    try:
        while True:
            heartbeat()
            if monotonic() >= deadline:
                raise LabWorkloadError("lab workload deadline reached")
            result = process.poll()
            if result is not None:
                output, _ = process.communicate()
                if result != 0 or len(output) > 16_384:
                    raise LabWorkloadError("fixed lab wrapper failed or exceeded receipt bound")
                try:
                    receipt = json.loads(output)
                except json.JSONDecodeError as exc:
                    raise LabWorkloadError("fixed lab wrapper did not return JSON") from exc
                return validate_receipt(receipt, lease_id=lease_id, generation=generation)
            time.sleep(poll_seconds)
    except BaseException:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except (AttributeError, OSError):
            process.terminate()
        try:
            process.wait(timeout=5)
        except Exception:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (AttributeError, OSError):
                process.kill()
            process.wait()
        raise
