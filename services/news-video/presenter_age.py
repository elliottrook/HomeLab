#!/usr/bin/env python3
"""Prepare Aster's annual identity-preserving presenter render request.

This module is deliberately renderer-neutral. It calculates the apparent age,
verifies the pinned identity/appearance assets, and emits a bounded render
request. It never calls an image service or activates an asset automatically.
"""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any

from wardrobe import build_review_request, load_wardrobe
from studio import build_review_request as build_studio_review_request, load_studio


ROOT = Path(__file__).resolve().parent
DEFAULT_PROFILE = ROOT / "presenter_profile.json"


class PresenterProfileError(ValueError):
    pass


def load_profile(path: Path = DEFAULT_PROFILE) -> dict[str, Any]:
    profile = json.loads(path.read_text(encoding="utf-8"))
    if profile.get("schema") != "aster.presenter-profile.v1":
        raise PresenterProfileError("unsupported presenter profile schema")
    policy = profile.get("age_policy", {})
    if policy.get("candidate_only") is not True:
        raise PresenterProfileError("annual renders must remain candidates")
    if policy.get("human_acceptance_required") is not True:
        raise PresenterProfileError("human acceptance may not be disabled")
    if profile.get("render_contract", {}).get("activate_automatically") is not False:
        raise PresenterProfileError("automatic presenter activation is forbidden")
    return profile


def _asset_path(profile_path: Path, value: str) -> Path:
    return (profile_path.parent / value).resolve()


def verify_assets(profile: dict[str, Any], profile_path: Path = DEFAULT_PROFILE) -> None:
    for section in ("identity_anchor", "accepted_appearance"):
        record = profile[section]
        path = _asset_path(profile_path, record["asset"])
        if not path.is_file():
            raise PresenterProfileError(f"missing {section} asset")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != record["sha256"]:
            raise PresenterProfileError(f"{section} asset hash mismatch")


def apparent_age(profile: dict[str, Any], on_date: date) -> int:
    policy = profile["age_policy"]
    epoch = date.fromisoformat(policy["epoch_date"])
    if on_date < epoch:
        raise PresenterProfileError("date predates the presenter epoch")
    anniversaries = on_date.year - epoch.year
    if (on_date.month, on_date.day) < (
        policy["anniversary_month"], policy["anniversary_day"]
    ):
        anniversaries -= 1
    return policy["epoch_apparent_age"] + anniversaries


def render_due(profile: dict[str, Any], on_date: date) -> bool:
    policy = profile["age_policy"]
    first_due = date.fromisoformat(policy["first_due_date"])
    anniversary_reached = (on_date.month, on_date.day) >= (
        policy["anniversary_month"], policy["anniversary_day"]
    )
    return (
        on_date >= first_due
        and anniversary_reached
        and policy["last_render_year"] < on_date.year
    )


def build_request(profile: dict[str, Any], on_date: date) -> dict[str, Any]:
    year = on_date.year
    age = apparent_age(profile, on_date)
    accepted = profile["accepted_appearance"]
    wardrobe = load_wardrobe()
    studio = load_studio()
    return {
        "schema": "aster.presenter-render-request.v1",
        "identity_id": profile["identity_id"],
        "year": year,
        "apparent_age": age,
        "reference_asset": accepted["asset"],
        "reference_sha256": accepted["sha256"],
        "output_name": profile["render_contract"]["output_pattern"].format(year=year),
        "status": "candidate",
        "activate_automatically": False,
        "wardrobe_review": build_review_request(wardrobe, on_date),
        "studio_review": build_studio_review_request(studio, on_date),
        "prompt": (
            f"Preserve Aster's exact fictional identity and depict him at apparent age {age}. "
            "Advance only natural age cues by one year from the last accepted appearance: "
            "subtle skin texture, hair greying and facial maturity. Preserve eyes, nose, mouth, "
            "ears, facial proportions, skin tone, gaze, body proportions and calm British "
            "broadcast authority. Keep the accepted contemporary 2026 studio composition, "
            "lighting and 16:9 framing. Apply the separately researched, owner-approved "
            "wardrobe update for this year. Do not resemble any real person, "
            "change ethnicity, add text or logos, or activate the result automatically."
        ),
        "acceptance_gates": [
            "recognizably the same Aster identity",
            "only one year of plausible ageing",
            "no resemblance drift toward a real person",
            "mouth and face remain suitable for lip-sync",
            "manual owner acceptance before activation"
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()

    profile = load_profile(args.profile)
    verify_assets(profile, args.profile)
    payload: dict[str, Any] = {
        "identity_id": profile["identity_id"],
        "date": args.date.isoformat(),
        "apparent_age": apparent_age(profile, args.date),
        "render_due": render_due(profile, args.date),
        "production_schedule_enabled": profile["render_contract"][
            "production_schedule_enabled"
        ]
    }
    if args.prepare:
        payload["request"] = build_request(profile, args.date)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
