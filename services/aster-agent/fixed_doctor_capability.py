"""Source-only candidate for one fixed, read-only Doctor capability.

No live broker or gateway imports this module.  A later deployment must bind
the paths, owner UID, socket peer and broker registration independently.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from doctor_model_projection import project_doctor_for_model
from doctor_structured_incident_adapter import SOURCE, read_doctor_structured_observation


CAPABILITY = "diagnostic.aster-inference.latest"
METHOD = "doctor.aster-inference.latest"


class FixedDoctorDenied(RuntimeError):
    pass


def execute_fixed_doctor_read(
    request: dict[str, Any], *, incident_id: str, aggregate_path: Path,
    structured_path: Path, now: datetime, required_uid: int,
) -> dict[str, Any]:
    """Read and project the fixed check, or deny without a partial result."""
    if request != {"method": METHOD, "arguments": {}}:
        raise FixedDoctorDenied("request is outside the fixed diagnostic contract")
    observation = read_doctor_structured_observation(
        incident_id, aggregate_path, structured_path, now,
        required_uid=required_uid,
    )
    result = project_doctor_for_model(observation, now)
    if result["source"] != SOURCE:
        raise FixedDoctorDenied("unexpected diagnostic producer")
    if result["state"] == "unavailable":
        # Availability is itself a safe typed result. It must remain free of a
        # reason guessed from human text or an unsafe file.
        result = {
            "source": SOURCE,
            "state": "unavailable",
            "observed_at": result["observed_at"],
            "age_seconds": result["age_seconds"],
            "facts": {},
        }
    return {"schema": 1, "capability": CAPABILITY, "observation": result}
