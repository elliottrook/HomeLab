#!/usr/bin/env python3
"""Fail-closed structural audit for every synthetic AsterTV v3 page."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET


HERE = Path(__file__).resolve().parent
PAGES = HERE / "overlay/skin.asterhome.v3pilot/1080i"
FOCUS_TYPES = {"button", "list", "panel", "fixedlist", "wraplist"}
NAV = ("onleft", "onright", "onup", "ondown")
NO_FOCUS_WINDOWS = {"custom_1203_aster_ai_command.xml"}
TOP_RAIL_PAGES = {
    "custom_1191_youtube_rework.xml",
    "custom_1198_news_rework.xml",
    "custom_1199_podcast_requests.xml",
}
MEDIA_DETAIL_PAGES = {
    "custom_1194_movie_rework.xml",
    "custom_1196_tv_rework.xml",
}


def audit(root: Path = PAGES) -> dict:
    rows = []
    for path in sorted(root.glob("custom_*.xml")):
        failures = []
        text = path.read_text()
        tree = ET.fromstring(text)
        controls = [node for node in tree.findall(".//control")
                    if node.attrib.get("id", "").isdigit()]
        focus = {int(node.attrib["id"]) for node in controls
                 if node.attrib.get("type") in FOCUS_TYPES}
        default = tree.findtext("defaultcontrol")
        if path.name not in NO_FOCUS_WINDOWS:
            if not default or not default.isdigit() or int(default) not in focus:
                failures.append("default-control-not-focusable")
        for node in controls:
            source = int(node.attrib["id"])
            if source not in focus:
                continue
            directions = 0
            for name in NAV:
                value = node.findtext(name)
                if value:
                    directions += 1
                if value and value.isdigit() and int(value) not in focus:
                    failures.append(f"broken-focus-edge:{source}:{name}:{value}")
            if not directions:
                failures.append(f"focus-orphan:{source}")
        lowered = text.casefold()
        if "stone-compass" in lowered or "limestone" in lowered:
            failures.append("stone-icon-outside-side-rail")
        if "asterblue" in lowered:
            failures.append("discarded-blue-token")
        if path.name in TOP_RAIL_PAGES:
            if "AsterV3MediaSearchPill" not in text:
                failures.append("missing-approved-search-pill")
            if "AsterV3MediaPill" not in text:
                failures.append("missing-approved-top-pill")
            if "aster-compass-128.png" not in text:
                failures.append("missing-plain-top-rail-icon")
        if path.name in MEDIA_DETAIL_PAGES:
            for icon in ("play.png", "forward.png", "trailer.png"):
                if f"player-controls/{icon}" not in text:
                    failures.append("missing-semantic-control:" + icon)
        rows.append({"page": path.name, "focus_controls": len(focus),
                     "failures": sorted(set(failures))})
    failures = sum(len(row["failures"]) for row in rows)
    return {"schema_version": 1, "pages": rows, "page_count": len(rows),
            "failure_count": failures, "outcome": "pass" if failures == 0 else "fail"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=PAGES)
    args = parser.parse_args(argv)
    result = audit(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["outcome"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
