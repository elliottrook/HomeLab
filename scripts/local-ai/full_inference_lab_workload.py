"""Offline contract for the distinct three-request accepted-9B lab smoke."""

from __future__ import annotations

import json
from typing import Callable, Sequence


LAB_PROFILE = "accepted-9b-direct-control-smoke-v1"
LAB_PORT = "11436"
LAB_COMMAND = (
    "pct", "exec", "110", "--",
    "/usr/local/sbin/aster-llama-lab-smoke",
    "--profile", LAB_PROFILE, "--port", LAB_PORT, "--requests", "3",
)


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
    code, output = runner(LAB_COMMAND, 300.0)
    if code != 0 or len(output) > 16_384:
        raise LabWorkloadError("fixed lab wrapper failed or exceeded receipt bound")
    try:
        receipt = json.loads(output)
    except json.JSONDecodeError as exc:
        raise LabWorkloadError("fixed lab wrapper did not return JSON") from exc
    return validate_receipt(receipt, lease_id=lease_id, generation=generation)
