"""Bounded connected SA1-SA3 investigation using only registered observations.

The runner owns a temporary incident store, seeds it from the fixed sanitized
Doctor report, permits at most three registered read-only observations, and
requires a final no-authority completion. It has no repair or discovery path.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from doctor_incident_adapter import read_doctor_observation
from sysadmin_incident_store import IncidentStore
from sysadmin_investigation import EvidenceRequest, InvestigationError, create_incident
from sysadmin_proposal_gateway import propose_and_bind_follow_up
from sysadmin_proposal_transport import request_model_proposal
from sysadmin_registered_producer import DOCTOR_REPORT, execute_registered_pending_observation
from sa3_installed_gateway_smoke import _idle


def run(
    state_dir: Path,
    key: str,
    *,
    now: datetime | None = None,
    doctor_reader: Callable = read_doctor_observation,
    transport: Callable = request_model_proposal,
    executor: Callable = execute_registered_pending_observation,
) -> dict:
    if not state_dir.is_dir() or (state_dir.stat().st_mode & 0o777) != 0o700:
        raise ValueError("temporary state directory must be mode 0700")
    now = now or datetime.now(timezone.utc)
    store = IncidentStore(state_dir / "incidents.sqlite3")
    incident = create_incident(
        "synthetic-installed-adaptive-loop",
        "Synthetic installed adaptive investigation",
        [
            EvidenceRequest("homelab-doctor", "status", "Read the registered sanitized Doctor report."),
            EvidenceRequest("forgejo-main", "git", "Read the registered sanitized Forgejo report."),
            EvidenceRequest("aster-gateway", "status", "Check gateway state."),
            EvidenceRequest("inference-server", "status", "Check inference state."),
        ],
    )
    incident.add_observation(doctor_reader(incident.incident_id, DOCTOR_REPORT, now), now)
    store.save(incident, now)

    steps = []
    terminal = None
    for _ in range(4):
        propose_and_bind_follow_up(store, incident.incident_id, key, transport=transport, now=now)
        pending = store.pending_follow_up(incident.incident_id, now)
        if pending is None:
            raise ValueError("missing pending proposal")
        request = pending["request"]
        step = {
            "disposition": pending["disposition"],
            "target": None if request is None else request["target"],
            "kind": None if request is None else request["kind"],
            "authority": pending["authority"],
            "effect": pending["effect"],
        }
        steps.append(step)
        if pending["disposition"] == "observe":
            executor(store, incident.incident_id, now)
            continue
        terminal = pending["disposition"]
        break

    current = store.load(incident.incident_id, now)
    journal = store.followup_journal_snapshot(incident.incident_id, now)
    complete = (
        terminal == "complete"
        and len(current.observations) == 4
        and journal["decision_count"] == 4
        and journal["consumed_count"] == 3
        and [item["target"] for item in current.observations]
        == ["homelab-doctor", "forgejo-main", "aster-gateway", "inference-server"]
    )
    return {
        "status": "complete" if complete else "no_go",
        "terminal_disposition": terminal,
        "decision_count": journal["decision_count"],
        "consumed_count": journal["consumed_count"],
        "observation_count": len(current.observations),
        "observation_targets": [item["target"] for item in current.observations],
        "observation_states": [item["state"] for item in current.observations],
        "steps": steps,
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
    except InvestigationError as exc:
        print(json.dumps({"status": "no_go", "reason": "investigation_boundary", "detail": str(exc)}))
        return 1
    except Exception as exc:
        print(json.dumps({"status": "no_go", "reason": type(exc).__name__}))
        return 1
    result["postcheck_idle_healthy"] = _idle(key)
    if not result["postcheck_idle_healthy"]:
        result["status"] = "no_go"
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
