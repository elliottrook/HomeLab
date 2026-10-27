"""Summarize AsterTV release gates without weakening unresolved boundaries."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


STATUSES = {
    "passed", "input-required", "environment-required", "approval-required",
}
CATEGORIES = {"automated", "owner", "hardware", "destructive", "promotion"}


class ReadinessError(ValueError):
    pass


def require(value: object, code: str) -> None:
    if not value:
        raise ReadinessError(code)


def bounded_strings(value: object, code: str, maximum: int = 16) -> list[str]:
    require(isinstance(value, list) and len(value) <= maximum, code)
    require(all(isinstance(item, str) and 0 < len(item) <= 240 for item in value),
            code)
    return value


def build(spec: dict) -> dict:
    require(isinstance(spec, dict) and spec.get("schema") == 1
            and spec.get("kind") == "aster-release-readiness-spec.v1",
            "readiness-spec")
    gates = spec.get("gates")
    require(isinstance(gates, list) and 1 <= len(gates) <= 64,
            "readiness-gates")
    rows: list[dict] = []
    seen: set[str] = set()
    for gate in gates:
        require(isinstance(gate, dict), "readiness-gate")
        identity = gate.get("id")
        category = gate.get("category")
        status = gate.get("status")
        require(isinstance(identity, str) and 0 < len(identity) <= 80,
                "readiness-id")
        require(identity not in seen, "readiness-duplicate")
        require(category in CATEGORIES, "readiness-category")
        require(status in STATUSES, "readiness-status")
        destructive = bool(gate.get("destructive", False))
        evidence = bounded_strings(gate.get("evidence", []),
                                   "readiness-evidence")
        blockers = bounded_strings(gate.get("blockers", []),
                                   "readiness-blockers")
        if status == "passed":
            require(evidence and not blockers, "readiness-passed-evidence")
        else:
            require(blockers, "readiness-open-blocker")
        if destructive:
            require(category == "destructive" and status != "passed",
                    "readiness-destructive-boundary")
        rows.append({
            "id": identity,
            "category": category,
            "status": status,
            "destructive": destructive,
            "evidence": evidence,
            "blockers": blockers,
        })
        seen.add(identity)

    require(any(row["category"] == "promotion" for row in rows),
            "readiness-promotion-gate")
    counts = {status: sum(row["status"] == status for row in rows)
              for status in sorted(STATUSES)}
    automated = [row for row in rows if row["category"] == "automated"]
    promotion = [row for row in rows if row["category"] == "promotion"]
    return {
        "schema": 1,
        "kind": "aster-release-readiness.v1",
        "candidate": spec.get("candidate", "AsterTV v2 HP"),
        "engineering_checks_passed": bool(automated)
        and all(row["status"] == "passed" for row in automated),
        "release_ready": all(row["status"] == "passed" for row in rows),
        "production_authorized": bool(promotion)
        and all(row["status"] == "passed" for row in promotion),
        "counts": counts,
        "gates": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(json.loads(args.spec.read_bytes())),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
