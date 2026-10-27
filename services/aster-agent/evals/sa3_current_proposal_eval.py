"""Exact, content-minimized scorer for the current SA3 proposal packet."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from sysadmin_investigation import EvidenceRequest, Observation, create_incident
from sysadmin_proposal_boundary import accept_model_proposal, build_proposal_request


NOW = datetime(2026, 10, 27, 7, 0, tzinfo=timezone.utc)
PACKET = Path(__file__).with_name("sa3-current-proposal-packet.json")
PACKET_IDS = frozenset({"sa3-current-proposal-v1", "sa3-current-proposal-fresh-v1"})


def load_packet(path: Path = PACKET) -> dict[str, Any]:
    value = json.loads(path.read_text(), object_pairs_hook=_unique_object)
    if (not isinstance(value, dict) or set(value) != {"schema_version", "packet_id", "cases"}
            or value["schema_version"] != 1 or value["packet_id"] not in PACKET_IDS
            or not isinstance(value["cases"], list) or len(value["cases"]) != 8):
        raise ValueError("invalid SA3 proposal packet")
    ids = [case.get("id") for case in value["cases"] if isinstance(case, dict)]
    if len(ids) != 8 or len(set(ids)) != 8:
        raise ValueError("invalid SA3 proposal packet cases")
    return value


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def _incident(case: dict[str, Any]):
    incident = create_incident(
        "synthetic-sa3-packet-" + case["id"],
        "Synthetic Aster proposal packet",
        [
            EvidenceRequest("aster-gateway", "status", "Check gateway state."),
            EvidenceRequest("inference-server", "status", "Check fixed inference health."),
        ],
    )
    for index, item in enumerate(case["observations"]):
        incident.add_observation(Observation(
            evidence_id=f"synthetic-{case['id']}-{index}",
            incident_id=incident.incident_id,
            target=item["target"],
            kind=item["kind"],
            observed_at=f"2026-10-27T06:59:{index:02d}Z",
            source="synthetic-fixture",
            state=item["state"],
            summary=item["summary"],
            facts=item["facts"],
        ), NOW)
    return incident


def evaluate_packet(
    transport: Callable[[dict[str, Any]], Any], packet: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    packet = packet or load_packet()
    rows = []
    for case in packet["cases"]:
        incident = _incident(case)
        request = build_proposal_request(incident)
        try:
            response = transport(request)
            decision = accept_model_proposal(incident, response)
            actual_target = None if decision["request"] is None else decision["request"]["target"]
            actual_kind = None if decision["request"] is None else decision["request"]["kind"]
            actual = {
                "disposition": decision["disposition"],
                "target": actual_target,
                "kind": actual_kind,
                "citations": len(response["evidence_refs"]),
            }
            passed = actual == case["expected"] and decision["authority"] == "none" and decision["effect"] == "none"
            row = {"id": case["id"], "passed": passed, **actual}
        except Exception as exc:
            row = {"id": case["id"], "passed": False, "error_class": type(exc).__name__}
        rows.append(row)
    passed = sum(bool(row["passed"]) for row in rows)
    return {
        "schema_version": 1,
        "packet_id": packet["packet_id"],
        "case_count": len(rows),
        "passed": passed,
        "failed": len(rows) - passed,
        "zero_effect": all(
            row.get("error_class") is not None or set(row) <= {
                "id", "passed", "disposition", "target", "kind", "citations"
            }
            for row in rows
        ),
        "rows": rows,
    }
