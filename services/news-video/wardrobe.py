#!/usr/bin/env python3
"""Select Aster's daily outfit and prepare the annual wardrobe review."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_WARDROBE = ROOT / "wardrobe.json"


class WardrobeError(ValueError):
    pass


def load_wardrobe(path: Path = DEFAULT_WARDROBE) -> dict[str, Any]:
    wardrobe = json.loads(path.read_text(encoding="utf-8"))
    if wardrobe.get("schema") != "aster.presenter-wardrobe.v1":
        raise WardrobeError("unsupported wardrobe schema")
    outfits = wardrobe.get("outfits", [])
    if len(outfits) != 10 or len({item["id"] for item in outfits}) != 10:
        raise WardrobeError("wardrobe must contain exactly ten unique outfits")
    review = wardrobe.get("annual_review_policy", {})
    if review.get("candidate_only") is not True:
        raise WardrobeError("annual wardrobe updates must remain candidates")
    if review.get("human_acceptance_required") is not True:
        raise WardrobeError("human wardrobe acceptance may not be disabled")
    if review.get("activate_automatically") is not False:
        raise WardrobeError("automatic wardrobe activation is forbidden")
    return wardrobe


def verify_assets(
    wardrobe: dict[str, Any], wardrobe_path: Path = DEFAULT_WARDROBE
) -> None:
    for outfit in wardrobe["outfits"]:
        path = (wardrobe_path.parent / outfit["asset"]).resolve()
        if not path.is_file():
            raise WardrobeError(f"missing asset for {outfit['id']}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != outfit["sha256"]:
            raise WardrobeError(f"asset hash mismatch for {outfit['id']}")


def _cycle_order(wardrobe: dict[str, Any], cycle: int) -> list[str]:
    seed = wardrobe["selection_policy"]["seed"]
    ids = [item["id"] for item in wardrobe["outfits"]]
    previous: list[str] | None = None
    ordered: list[str] = []
    for cycle_number in range(cycle + 1):
        ordered = sorted(
            ids,
            key=lambda outfit_id: hashlib.sha256(
                f"{seed}|{cycle_number}|{outfit_id}".encode("utf-8")
            ).digest(),
        )
        if previous is not None and ordered[0] == previous[-1]:
            ordered = ordered[1:] + ordered[:1]
        previous = ordered
    return ordered


def outfit_for_date(wardrobe: dict[str, Any], on_date: date) -> dict[str, Any]:
    epoch = date.fromisoformat(wardrobe["selection_policy"]["epoch_date"])
    day_index = (on_date - epoch).days
    if day_index < 0:
        raise WardrobeError("date predates the wardrobe epoch")
    count = len(wardrobe["outfits"])
    cycle, position = divmod(day_index, count)
    selected_id = _cycle_order(wardrobe, cycle)[position]
    return next(item for item in wardrobe["outfits"] if item["id"] == selected_id)


def build_review_request(wardrobe: dict[str, Any], on_date: date) -> dict[str, Any]:
    policy = wardrobe["annual_review_policy"]
    return {
        "schema": "aster.wardrobe-review-request.v1",
        "identity_id": wardrobe["identity_id"],
        "year": on_date.year,
        "status": "candidate",
        "activate_automatically": False,
        "research_cutoff": on_date.isoformat(),
        "research_max_age_days": policy["research_max_age_days"],
        "source_requirements": {
            "official_uk_broadcasters": policy[
                "minimum_official_uk_broadcaster_sources"
            ],
            "current_uk_tailoring_sources": policy[
                "minimum_current_uk_tailoring_sources"
            ],
        },
        "brief": (
            "Review current male British television news-presenter clothing and current "
            "British tailoring. Refresh only details that have genuinely moved: fit, lapel, "
            "shoulder, trouser line, cloth texture, shirt and tie palette. Keep Aster "
            "authoritative, camera-safe and recognizably himself; avoid costume, streetwear, "
            "logos and short-lived runway novelty. Produce ten identity-preserving wardrobe "
            "candidates and require owner acceptance before replacing this collection."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wardrobe", type=Path, default=DEFAULT_WARDROBE)
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--review", action="store_true")
    args = parser.parse_args()

    wardrobe = load_wardrobe(args.wardrobe)
    verify_assets(wardrobe, args.wardrobe)
    payload: dict[str, Any] = {
        "date": args.date.isoformat(),
        "outfit": outfit_for_date(wardrobe, args.date),
    }
    if args.review:
        payload["annual_review"] = build_review_request(wardrobe, args.date)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
