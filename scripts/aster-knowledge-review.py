#!/usr/bin/env python3
"""Read-only monthly integrity review for Aster's curated knowledge sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "services/aster-agent/knowledge-sources.json"
MAX_SOURCE_BYTES = 256 * 1024


def git(repository: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repository), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-root", type=Path, default=ROOT.parent / "homelab-reference")
    parser.add_argument("--report", type=Path, help="optional JSON report destination")
    args = parser.parse_args()

    reference = args.reference_root.resolve()
    repositories = {"homelab": ROOT, "reference": reference}
    findings: list[dict[str, str]] = []
    states: dict[str, dict[str, str | bool]] = {}
    for name, repository in repositories.items():
        if not (repository / ".git").exists():
            findings.append({"level": "fail", "message": f"{name} is not a Git repository"})
            continue
        dirty = bool(git(repository, "status", "--porcelain"))
        states[name] = {"commit": git(repository, "rev-parse", "HEAD"), "dirty": dirty}
        if dirty:
            findings.append({"level": "fail", "message": f"{name} working tree is dirty"})

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    destinations: set[str] = set()
    for source in manifest.get("sources", []):
        destination = str(source.get("destination", ""))
        repository = repositories.get(str(source.get("repository", "")))
        path = repository / str(source.get("path", "")) if repository else None
        if not destination or destination in destinations:
            findings.append({"level": "fail", "message": f"duplicate or missing destination: {destination}"})
        destinations.add(destination)
        if not path or not path.is_file():
            findings.append({"level": "fail", "message": f"missing source: {source.get('repository')}:{source.get('path')}"})
        elif path.stat().st_size > MAX_SOURCE_BYTES:
            findings.append({"level": "warn", "message": f"oversized source: {source.get('path')}"})

    if not any(item["level"] == "fail" for item in findings):
        with tempfile.TemporaryDirectory(prefix="aster-knowledge-review-") as temporary:
            first = Path(temporary) / "first.tar.gz"
            second = Path(temporary) / "second.tar.gz"
            command = [sys.executable, str(ROOT / "scripts/build-aster-knowledge-snapshot.py"), "--reference-root", str(reference)]
            subprocess.run([*command, str(first)], check=True)
            subprocess.run([*command, str(second)], check=True)
            if hashlib.sha256(first.read_bytes()).digest() != hashlib.sha256(second.read_bytes()).digest():
                findings.append({"level": "fail", "message": "snapshot rebuild is not deterministic"})
            else:
                index = json.loads(
                    subprocess.run(["tar", "-xOzf", str(first), ".aster-provenance.json"], check=True, capture_output=True, text=True).stdout
                )
                if len(index.get("sources", [])) != len(manifest.get("sources", [])):
                    findings.append({"level": "fail", "message": "provenance source count differs from manifest"})

    report: dict[str, Any] = {
        "schema_version": 1,
        "status": "failed" if any(item["level"] == "fail" for item in findings) else "warning" if findings else "healthy",
        "repositories": states,
        "source_count": len(manifest.get("sources", [])),
        "findings": findings,
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if report["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
