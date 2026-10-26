"""One fixed, read-only Aster Speech capability."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from speech_catalogue_incident_adapter import SOURCE, read_speech_catalogue_observation


CAPABILITY = "diagnostic.aster-speech.latest"
METHOD = "doctor.aster-speech.latest"


class FixedSpeechDenied(RuntimeError):
    pass


def execute_fixed_speech_read(
    request: dict[str, Any], *, incident_id: str, aggregate_path: Path,
    catalogue_path: Path, now: datetime, required_uid: int,
) -> dict[str, Any]:
    if request != {"method": METHOD, "arguments": {}}:
        raise FixedSpeechDenied("request is outside the fixed speech contract")
    record = read_speech_catalogue_observation(
        incident_id, aggregate_path, catalogue_path, now,
        required_uid=required_uid,
    ).validate(now)
    if record["source"] != SOURCE:
        raise FixedSpeechDenied("unexpected speech producer")
    observed = datetime.fromisoformat(record["observed_at"].replace("Z", "+00:00"))
    age = int((now.astimezone(timezone.utc) - observed.astimezone(timezone.utc)).total_seconds())
    if record["state"] == "unavailable":
        facts = {}
    else:
        if set(record["facts"]) != {"check_id", "report_digest"} or record["facts"]["check_id"] != "aster.speech":
            raise FixedSpeechDenied("unexpected speech facts")
        facts = {"check_id": "aster.speech"}
    return {
        "schema": 1,
        "capability": CAPABILITY,
        "observation": {
            "source": SOURCE,
            "state": record["state"],
            "observed_at": record["observed_at"],
            "age_seconds": age,
            "facts": facts,
        },
    }
