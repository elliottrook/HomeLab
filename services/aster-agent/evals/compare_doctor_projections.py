"""Offline contract comparison of three existing Doctor evidence projections.

This executes the repository's get_lab_health function in isolation because the
whole Aster gateway requires optional web dependencies. It runs no Doctor,
model, network request or production tool. Results are projection behavior,
not answer quality or an independently blinded evaluation.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

AGENT_DIR = Path(__file__).resolve().parents[1]
ROOT = AGENT_DIR.parents[1]
BASELINE_REF = "cf17faed0b680959ac97f395c4f165d70e886cec"
sys.path.insert(0, str(AGENT_DIR))

from doctor_incident_adapter import read_doctor_observation  # noqa: E402
from doctor_structured_incident_adapter import read_doctor_structured_observation  # noqa: E402


NOW = datetime(2026, 10, 10, 20, 0, tzinfo=timezone.utc)
MARKER = "FIXTURE_PRIVATE_MARKER"
CHECK_ID = "aster.agent_inference"


def compile_health_function(source: str):
    """Execute only get_lab_health from a source snapshot."""
    module = ast.parse(source)
    matches = [node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "get_lab_health"]
    if len(matches) != 1:
        raise ValueError("expected one get_lab_health function")
    namespace = {
        "Path": Path, "Any": Any, "json": json, "os": os, "stat": stat,
        "datetime": datetime, "timedelta": timedelta, "timezone": timezone,
        "HEALTH_REPORT_PATH": Path("/nonexistent"),
    }
    exec(compile(ast.Module(body=matches, type_ignores=[]), str(AGENT_DIR / "aster_agent.py"), "exec"), namespace)
    return namespace["get_lab_health"], hashlib.sha256(ast.get_source_segment(source, matches[0]).encode()).hexdigest()


def isolated_baseline_health_function():
    """Run the frozen baseline function without importing the web gateway."""
    source = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{BASELINE_REF}:services/aster-agent/aster_agent.py"],
        check=True, capture_output=True, text=True,
    ).stdout
    return compile_health_function(source)


def run_case(case: dict[str, Any], health_function) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        aggregate_path, structured_path = root / "aggregate.json", root / "structured.json"
        generated_at = (NOW - timedelta(hours=case.get("age_hours", 0), minutes=2)).isoformat().replace("+00:00", "Z")
        aggregate = {
            "schema": 1,
            "generated_at": generated_at,
            "status": case["overall"],
            "checks": [{"name": "HomeLab Doctor", "status": state, "summary": summary} for state, summary in case["checks"]],
        }
        raw = (json.dumps(aggregate, sort_keys=True, separators=(",", ":")) + "\n").encode()
        aggregate_path.write_bytes(raw)
        aggregate_path.chmod(0o600)
        if not case.get("missing_sidecar"):
            sidecar = {
                "schema": 2,
                "generated_at": generated_at,
                "run_id": "a" * 32,
                "source_report_digest": hashlib.sha256(raw).hexdigest(),
                "checks": [{"check_id": CHECK_ID, "state": case["aster_state"]}],
            }
            structured_path.write_text(json.dumps(sidecar), encoding="utf-8")
            structured_path.chmod(0o600)
        current = health_function(aggregate_path)
        aggregate_view = read_doctor_observation(case["id"], aggregate_path, NOW).validate(NOW)
        typed_view = read_doctor_structured_observation(
            case["id"], aggregate_path, structured_path, NOW, required_uid=os.getuid(),
        ).validate(NOW)
        summaries = [item["summary"] for item in current.get("checks", [])]
        serialized_aggregate = json.dumps(aggregate_view, sort_keys=True)
        serialized_typed = json.dumps(typed_view, sort_keys=True)
        return {
            "id": case["id"],
            "current_aster": {
                "status": current["status"],
                "human_summary_count": len(summaries),
                "human_summary_characters": sum(map(len, summaries)),
                "marker_exposed": MARKER in json.dumps(current),
            },
            "aggregate_incident": {
                "state": aggregate_view["state"],
                "check_count": aggregate_view["facts"].get("check_count"),
                "marker_exposed": MARKER in serialized_aggregate,
            },
            "typed_candidate": {
                "state": typed_view["state"],
                "check_id": typed_view["facts"].get("check_id"),
                "marker_exposed": MARKER in serialized_typed,
            },
        }


CASES = [
    {"id": "healthy", "overall": "healthy", "aster_state": "pass", "checks": [("pass", "Aster agent/inference passed.")]},
    {"id": "aster_fail", "overall": "failed", "aster_state": "fail", "checks": [("fail", "Aster agent/inference failed.")]},
    {"id": "other_fail", "overall": "failed", "aster_state": "pass", "checks": [("fail", "Other service failed."), ("pass", "Aster agent/inference passed.")]},
    {"id": "multiple_fail", "overall": "failed", "aster_state": "fail", "checks": [("fail", "Aster agent/inference failed."), ("fail", "Other service failed.")]},
    {"id": "stale", "overall": "failed", "aster_state": "fail", "age_hours": 37, "checks": [("fail", "Aster agent/inference failed.")]},
    {"id": "missing_sidecar", "overall": "failed", "aster_state": "fail", "missing_sidecar": True, "checks": [("fail", "Aster agent/inference failed.")]},
    {"id": "private_marker", "overall": "failed", "aster_state": "fail", "checks": [("fail", "Aster agent/inference failed. " + MARKER)]},
]


def main() -> None:
    health_function, function_digest = isolated_baseline_health_function()
    result = {
        "schema": 1,
        "scope": "synthetic_offline_projection_only",
        "current_health_source_ref": BASELINE_REF,
        "current_health_function_sha256": function_digest,
        "cases": [run_case(case, health_function) for case in CASES],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
