"""Bounded connected check for the current SA3 proposal boundary.

This runner uses synthetic incident state only. It performs three serial model
calls, has no producer or repair capability, and emits only decision metadata.
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

from sysadmin_investigation import EvidenceRequest, Observation, create_incident
from sysadmin_proposal_boundary import build_proposal_request, propose_follow_up
from sysadmin_proposal_transport import ENDPOINT, request_model_proposal


NOW = datetime(2026, 10, 27, 7, 0, tzinfo=timezone.utc)
BASE = ENDPOINT.rsplit("/v1/chat/completions", 1)[0]


def build_synthetic_incidents():
    plan = [
        EvidenceRequest("aster-gateway", "status", "Check gateway state."),
        EvidenceRequest("inference-server", "status", "Check fixed inference health."),
    ]
    initial = create_incident("synthetic-sa3-initial", "Synthetic Aster check", plan)
    gateway = create_incident("synthetic-sa3-gateway", "Synthetic Aster check", plan)
    gateway.add_observation(Observation(
        evidence_id="synthetic-gateway-status",
        incident_id=gateway.incident_id,
        target="aster-gateway",
        kind="status",
        observed_at="2026-10-27T06:59:00Z",
        source="synthetic-fixture",
        state="ok",
        summary="The gateway is serving requests.",
        facts={"service": "aster-agent", "availability": "serving"},
    ), NOW)
    complete = create_incident("synthetic-sa3-complete", "Synthetic Aster check", plan)
    for evidence in (
        Observation(
            evidence_id="synthetic-gateway-status",
            incident_id=complete.incident_id,
            target="aster-gateway",
            kind="status",
            observed_at="2026-10-27T06:59:00Z",
            source="synthetic-fixture",
            state="ok",
            summary="The gateway is serving requests.",
            facts={"service": "aster-agent", "availability": "serving"},
        ),
        Observation(
            evidence_id="synthetic-inference-status",
            incident_id=complete.incident_id,
            target="inference-server",
            kind="status",
            observed_at="2026-10-27T06:59:10Z",
            source="synthetic-fixture",
            state="ok",
            summary="The fixed inference health endpoint reported ok.",
            facts={"service": "aster-llama", "endpoint": "health"},
        ),
    ):
        complete.add_observation(evidence, NOW)
    return [("initial", initial), ("gateway_observed", gateway), ("plan_exhausted", complete)]


def _read_json(path: str, key: str) -> dict:
    request = urllib.request.Request(path, headers={"Authorization": "Bearer " + key})
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.load(response)


def _idle(key: str) -> bool:
    health = _read_json(BASE + "/health", key)
    request = urllib.request.Request(BASE + "/metrics", headers={"Authorization": "Bearer " + key})
    with urllib.request.urlopen(request, timeout=5) as response:
        metrics = response.read(256_000).decode()
    values = []
    for line in metrics.splitlines():
        if line and not line.startswith("#") and line.split()[0].split("{")[0].endswith("requests_processing"):
            values.append(float(line.split()[-1]))
    return health.get("status") == "ok" and bool(values) and not any(values)


def evaluate(transport):
    results = []
    for label, incident in build_synthetic_incidents():
        request = build_proposal_request(incident)
        decision = propose_follow_up(incident, transport)
        results.append({
            "case": label,
            "disposition": decision["disposition"],
            "target": None if decision["request"] is None else decision["request"]["target"],
            "kind": None if decision["request"] is None else decision["request"]["kind"],
            "available_evidence": len(request["observations"]),
            "authority": decision["authority"],
            "effect": decision["effect"],
        })
    return results


def main() -> int:
    key = os.environ.get("ASTER_LLAMA_API_KEY", "")
    if not key:
        print(json.dumps({"status": "no_go", "reason": "existing_authentication_missing"}))
        return 1
    if not _idle(key):
        print(json.dumps({"status": "no_go", "reason": "service_not_confirmed_idle_healthy"}))
        return 1
    try:
        results = evaluate(lambda request: request_model_proposal(request, key))
    except Exception as exc:
        print(json.dumps({"status": "no_go", "reason": type(exc).__name__}))
        return 1
    postcheck = _idle(key)
    output = {"status": "complete" if postcheck else "no_go", "results": results,
              "postcheck_idle_healthy": postcheck}
    print(json.dumps(output, sort_keys=True))
    return 0 if postcheck else 1


if __name__ == "__main__":
    raise SystemExit(main())
