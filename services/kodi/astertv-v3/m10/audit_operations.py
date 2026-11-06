#!/usr/bin/env python3
"""Audit sanitized M10 operational integration evidence without live credentials."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


DEVICES = ("astertv-bedroom", "astertv-family", "astertv-jen")
HEALTHY_DOCTOR = {"clean", "registered-extra"}


def audit(observation: dict) -> dict:
    if observation.get("schema_version") != 1:
        raise ValueError("operations-observation-schema")
    gaps: list[str] = []

    doctor = observation.get("doctor", {})
    monitoring = observation.get("monitoring", {})
    netbox = observation.get("netbox", {})
    for device in DEVICES:
        status = doctor.get(device)
        if status not in HEALTHY_DOCTOR:
            gaps.append(f"doctor:{device}:{status or 'missing'}")
        if monitoring.get(device) != "up":
            gaps.append(f"monitoring:{device}:missing-or-down")
        record = netbox.get(device)
        if not isinstance(record, dict) or not all(record.get(key) for key in ("primary_ip", "mac")):
            gaps.append(f"netbox:{device}:identity-incomplete")

    wiki = observation.get("wiki", {})
    if int(wiki.get("candidate_page_count", 0)) < 25:
        gaps.append("wiki:candidate-incomplete")
    if not wiki.get("published") or int(wiki.get("live_page_count", 0)) < 25:
        gaps.append("wiki:live-astertv-department-absent")

    reference = observation.get("reference", {})
    if int(reference.get("astertv_page_count", 0)) < 1:
        gaps.append("reference:astertv-operations-absent")

    mirror = observation.get("mirror", {})
    if not mirror.get("source_registered") or not mirror.get("derived_with_provenance"):
        gaps.append("mirror:astertv-derived-source-absent")

    backup = observation.get("backup", {})
    for item in ("forgejo_restore_proven", "wiki_restore_proven"):
        if not backup.get(item):
            gaps.append(f"backup:{item.replace('_', '-')}:missing")
    recovered = set(backup.get("appliance_restore_proven", []))
    for device in DEVICES:
        if device not in recovered:
            gaps.append(f"backup:{device}:isolated-restore-unproven")

    administration = observation.get("ai_administration", {})
    if not all(administration.get(key) for key in
               ("fleet_skill_manifested", "design_skill_manifested", "forward_tests_passed")):
        gaps.append("ai-administration:skill-custody-incomplete")

    return {
        "schema_version": 1,
        "kind": "astertv-m10-operations-audit",
        "outcome": "pass" if not gaps else "attention",
        "required_devices": list(DEVICES),
        "gap_count": len(gaps),
        "gaps": gaps,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("observation", type=Path)
    args = parser.parse_args(argv)
    result = audit(json.loads(args.observation.read_text()))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["outcome"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
