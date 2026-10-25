#!/usr/bin/env python3
"""Validate the frozen Mac fixed-Doctor producer cutover without changing it."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import stat
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).with_name("fixed-doctor-producer-manifest.json")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(live: bool = False) -> list[str]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if set(data) != {"candidate", "launch_agent", "entries", "canary", "reports"}:
        raise ValueError("unexpected manifest fields")
    if data["candidate"] != "m1-d4-fixed-doctor-producer-v1":
        raise ValueError("wrong candidate")
    if len(data["entries"]) != 2:
        raise ValueError("producer cutover must contain exactly two files")

    expected_sources = {
        "scripts/build-aster-health-report.py",
        "scripts/scheduled-report.sh",
    }
    if {entry["source"] for entry in data["entries"]} != expected_sources:
        raise ValueError("unexpected producer source set")

    results: list[str] = []
    for entry in data["entries"]:
        if set(entry) != {
            "current_sha256", "group", "mode", "owner", "sha256", "source", "target"
        }:
            raise ValueError(f"unexpected entry fields for {entry.get('source')}")
        source = ROOT / entry["source"]
        if digest(source) != entry["sha256"]:
            raise ValueError(f"candidate hash mismatch: {entry['source']}")
        if stat.S_IMODE(source.stat().st_mode) != int(entry["mode"], 8):
            raise ValueError(f"candidate mode mismatch: {entry['source']}")
        results.append(f"candidate:{entry['source']}:ok")
        if live:
            target = Path(entry["target"])
            if digest(target) != entry["current_sha256"]:
                raise ValueError(f"live predecessor mismatch: {entry['target']}")
            target_stat = target.stat()
            if stat.S_IMODE(target_stat.st_mode) != int(entry["mode"], 8):
                raise ValueError(f"live mode mismatch: {entry['target']}")
            if target.owner() != entry["owner"] or target.group() != entry["group"]:
                raise ValueError(f"live custody mismatch: {entry['target']}")
            results.append(f"predecessor:{entry['target']}:ok")

    launch = data["launch_agent"]
    if set(launch) != {"hour", "label", "minute", "path"}:
        raise ValueError("unexpected launch-agent fields")
    if launch != {
        "hour": 8,
        "label": "ca.yampy.homelab-report",
        "minute": 15,
        "path": "/Users/jelliott/Library/LaunchAgents/ca.yampy.homelab-report.plist",
    }:
        raise ValueError("launch-agent contract drift")
    if live:
        with Path(launch["path"]).open("rb") as stream:
            plist = plistlib.load(stream)
        if plist.get("Label") != launch["label"]:
            raise ValueError("launch-agent label drift")
        if plist.get("StartCalendarInterval") != {"Hour": 8, "Minute": 15}:
            raise ValueError("launch-agent schedule drift")
        if plist.get("ProgramArguments") != [
            "/bin/bash", "/Users/jelliott/lab/homelab/scripts/scheduled-report.sh"
        ]:
            raise ValueError("launch-agent command drift")
        results.append("launch-agent:ok")

    canary = data["canary"]
    if set(canary) != {"command", "timeout_seconds"} or canary["timeout_seconds"] != 930:
        raise ValueError("unexpected canary contract")
    if canary["command"][-1] != "--publish" or "scheduled-report.sh" in canary["command"]:
        raise ValueError("canary must publish through the builder only")
    if "--structured-output" not in canary["command"] or "--result-output" not in canary["command"]:
        raise ValueError("canary omits required output")
    results.append("canary:ok")

    reports = data["reports"]
    if set(reports) != {"local", "remote"} or len(reports["local"]) != 4 or len(reports["remote"]) != 2:
        raise ValueError("unexpected report checkpoint set")
    if len(set(reports["local"] + reports["remote"])) != 6:
        raise ValueError("duplicate report checkpoint")
    results.append("reports:ok")
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="also verify current Mac predecessors and schedule")
    args = parser.parse_args()
    for result in validate(live=args.live):
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
