#!/usr/bin/env python3
"""Verify Aster's studio contract and prepare its annual design review."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import tarfile
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_PROFILE = ROOT / "studio_profile.json"


class StudioProfileError(ValueError):
    pass


def load_studio(path: Path = DEFAULT_PROFILE) -> dict[str, Any]:
    profile = json.loads(path.read_text(encoding="utf-8"))
    if profile.get("schema") != "aster.presenter-studio.v1":
        raise StudioProfileError("unsupported studio profile schema")
    policy = profile.get("annual_review_policy", {})
    if policy.get("candidate_only") is not True:
        raise StudioProfileError("annual studio updates must remain candidates")
    if policy.get("human_acceptance_required") is not True:
        raise StudioProfileError("human studio acceptance may not be disabled")
    if policy.get("activate_automatically") is not False:
        raise StudioProfileError("automatic studio activation is forbidden")
    if policy.get("current_brand_snapshot_required") is not True:
        raise StudioProfileError("current Aster brand snapshot is required")
    return profile


def _resolve(profile_path: Path, asset: str) -> Path:
    return (profile_path.parent / asset).resolve()


def verify_assets(
    profile: dict[str, Any], profile_path: Path = DEFAULT_PROFILE
) -> None:
    studio = profile["studio_asset"]
    studio_path = _resolve(profile_path, studio["asset"])
    if not studio_path.is_file():
        raise StudioProfileError(f"missing studio dependency: {studio['asset']}")
    if hashlib.sha256(studio_path.read_bytes()).hexdigest() != studio["sha256"]:
        raise StudioProfileError("studio candidate hash mismatch")

    snapshot = profile["brand_snapshot"]
    authority = snapshot["authority"]
    archive_path = _resolve(profile_path, authority["archive"])
    if not archive_path.is_file():
        raise StudioProfileError("missing AsterTV design authority archive")
    if hashlib.sha256(archive_path.read_bytes()).hexdigest() != authority["sha256"]:
        raise StudioProfileError("AsterTV design authority archive hash mismatch")
    with tarfile.open(archive_path, "r:gz") as archive:
        for record in snapshot["members"]:
            try:
                extracted = archive.extractfile(record["member"])
            except KeyError as exc:
                raise StudioProfileError(
                    f"missing AsterTV member: {record['member']}"
                ) from exc
            if extracted is None:
                raise StudioProfileError(f"missing AsterTV member: {record['member']}")
            if hashlib.sha256(extracted.read()).hexdigest() != record["sha256"]:
                raise StudioProfileError(f"AsterTV member hash mismatch: {record['member']}")


def review_due(profile: dict[str, Any], on_date: date) -> bool:
    policy = profile["annual_review_policy"]
    first_due = date.fromisoformat(policy["first_due_date"])
    anniversary_reached = (on_date.month, on_date.day) >= (
        policy["anniversary_month"],
        policy["anniversary_day"],
    )
    return (
        on_date >= first_due
        and anniversary_reached
        and policy["last_review_year"] < on_date.year
    )


def build_review_request(profile: dict[str, Any], on_date: date) -> dict[str, Any]:
    policy = profile["annual_review_policy"]
    snapshot = profile["brand_snapshot"]
    return {
        "schema": "aster.studio-review-request.v1",
        "identity_id": profile["identity_id"],
        "year": on_date.year,
        "status": "candidate",
        "activate_automatically": False,
        "research_cutoff": on_date.isoformat(),
        "research_max_age_days": policy["research_max_age_days"],
        "brand_snapshot": {
            "captured": snapshot["captured"],
            "authority": snapshot["authority"],
            "members": snapshot["members"],
            "derived_palette": snapshot["derived_palette"],
        },
        "required_steps": [
            "resolve and hash the then-current accepted AsterTV design release",
            "read its canonical skin colour tokens and accepted surface/material assets",
            "derive a candidate studio palette from that current AsterTV release rather than assuming the 2026 colours",
            "review current British and European broadcast-studio design evidence no more than 90 days old",
            "keep the studio evolutionary: update materials, lighting and display architecture only where evidence supports it",
            "preserve the accepted traditional rectangular story-monitor geometry unless the owner explicitly revisits it",
            "render 16:9 television-distance candidates with presenter and story-graphics safe regions",
            "obtain owner acceptance before replacing the accepted studio"
        ],
        "invariants": profile["design_contract"],
        "brief": (
            "Refresh Aster's studio for the review year using the accepted AsterTV "
            "design language current at that time. Preserve its calm British authority, "
            "warm limestone/ink/jade balance, presenter legibility and large right-hand graphics-safe region. "
            "Keep the story monitor a conventional horizontal rectangle. Avoid cosmetic churn, generic virtual-newsroom styling, literal oversized "
            "app icons, science-fiction spectacle, baked text and automatic activation."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()

    profile = load_studio(args.profile)
    verify_assets(profile, args.profile)
    payload: dict[str, Any] = {
        "date": args.date.isoformat(),
        "studio_status": profile["status"],
        "review_due": review_due(profile, args.date),
        "production_schedule_enabled": profile["annual_review_policy"][
            "production_schedule_enabled"
        ],
    }
    if args.prepare:
        payload["request"] = build_review_request(profile, args.date)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
