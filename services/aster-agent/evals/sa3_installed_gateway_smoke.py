"""One-call, no-effect smoke test for the installed SA3 proposal gateway.

The runner uses a caller-supplied temporary directory, writes only synthetic
incident state there, makes one bounded model call, and never consumes the
journaled follow-up.  The caller owns removal of the temporary directory.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sysadmin_incident_store import IncidentStore
from sysadmin_investigation import EvidenceRequest, Observation, create_incident
from sysadmin_proposal_gateway import propose_and_bind_follow_up
from sysadmin_proposal_transport import ENDPOINT


BASE = ENDPOINT.rsplit("/v1/chat/completions", 1)[0]


def _read_json(url: str, key: str) -> dict:
    request = urllib.request.Request(url, headers={"Authorization": "Bearer " + key})
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.load(response)


def _idle(key: str) -> bool:
    health = _read_json(BASE + "/health", key)
    request = urllib.request.Request(BASE + "/metrics", headers={"Authorization": "Bearer " + key})
    with urllib.request.urlopen(request, timeout=5) as response:
        metrics = response.read(256_000).decode()
    processing = []
    for line in metrics.splitlines():
        if line and not line.startswith("#"):
            name = line.split()[0].split("{")[0]
            if name.endswith("requests_processing"):
                processing.append(float(line.split()[-1]))
    return health.get("status") == "ok" and bool(processing) and not any(processing)


def run(state_dir: Path, key: str, now: datetime | None = None) -> dict:
    if not state_dir.is_dir() or (state_dir.stat().st_mode & 0o777) != 0o700:
        raise ValueError("temporary state directory must be mode 0700")
    now = now or datetime.now(timezone.utc)
    store = IncidentStore(state_dir / "incidents.sqlite3")
    incident = create_incident(
        "synthetic-installed-gateway-smoke",
        "Synthetic installed gateway smoke",
        [
            EvidenceRequest("aster-gateway", "status", "Check gateway state."),
            EvidenceRequest("inference-server", "status", "Check inference state."),
        ],
    )
    incident.add_observation(Observation(
        evidence_id="synthetic-gateway-status",
        incident_id=incident.incident_id,
        target="aster-gateway",
        kind="status",
        observed_at=now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        source="synthetic-smoke/v1",
        state="ok",
        summary="The synthetic gateway observation is healthy.",
        facts={"availability": "serving"},
    ), now)
    store.save(incident, now)
    journal = propose_and_bind_follow_up(store, incident.incident_id, key, now=now)
    pending = journal["pending"]
    trusted = store.pending_follow_up(incident.incident_id, now)
    if trusted is None:
        raise ValueError("proposal journal did not retain a pending decision")
    return {
        "status": "complete",
        "decision_count": journal["decision_count"],
        "consumed_count": journal["consumed_count"],
        "disposition": pending["disposition"],
        "target": pending.get("target"),
        "kind": pending.get("kind"),
        "authority": trusted["authority"],
        "effect": trusted["effect"],
        "observation_count": len(store.load(incident.incident_id, now).observations),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(json.dumps({"status": "no_go", "reason": "temporary_state_directory_required"}))
        return 2
    key = os.environ.get("ASTER_LLAMA_API_KEY", "")
    if not key:
        print(json.dumps({"status": "no_go", "reason": "existing_authentication_missing"}))
        return 1
    if not _idle(key):
        print(json.dumps({"status": "no_go", "reason": "service_not_confirmed_idle_healthy"}))
        return 1
    try:
        result = run(Path(sys.argv[1]), key)
    except Exception as exc:
        print(json.dumps({"status": "no_go", "reason": type(exc).__name__}))
        return 1
    result["postcheck_idle_healthy"] = _idle(key)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["postcheck_idle_healthy"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
