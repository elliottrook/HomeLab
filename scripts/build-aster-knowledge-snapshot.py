#!/usr/bin/env python3
"""Build a deterministic, provenance-indexed Aster knowledge snapshot."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import subprocess
import tarfile
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "services/aster-agent/knowledge-sources.json"
ASSIGNED_SECRET = re.compile(
    rb"(?im)^\s*(?:api[_-]?key|password|passwd|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9+/=_-]{12,}"
)


def git(repository: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *args], check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def metadata(text: str, name: str) -> str | None:
    prefix = f"> {name}: "
    return next(
        (line[len(prefix) :].strip() for line in text.splitlines()[:10] if line.startswith(prefix)),
        None,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", default=str(ROOT / "aster-knowledge.tar.gz"))
    parser.add_argument("--reference-root", type=Path, default=ROOT.parent / "homelab-reference")
    parser.add_argument("--allow-dirty", action="store_true", help="development only; provenance records dirty state")
    args = parser.parse_args()

    repositories = {"homelab": ROOT, "reference": args.reference_root.resolve()}
    states: dict[str, dict[str, object]] = {}
    for name, repository in repositories.items():
        if not (repository / ".git").exists():
            raise SystemExit(f"Not a Git repository: {repository}")
        dirty = bool(git(repository, "status", "--porcelain"))
        if dirty and not args.allow_dirty:
            raise SystemExit(f"Refusing dirty source repository: {repository}")
        states[name] = {"commit": git(repository, "rev-parse", "HEAD"), "dirty": dirty}

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    members: list[tuple[str, bytes]] = []
    provenance: list[dict[str, object]] = []
    destinations: set[str] = set()
    for entry in manifest["sources"]:
        repository = repositories[entry["repository"]]
        source = repository / entry["path"]
        destination = entry["destination"]
        if destination in destinations:
            raise SystemExit(f"Duplicate destination: {destination}")
        destinations.add(destination)
        if not source.is_file() or source.suffix.lower() not in {".md", ".txt"}:
            raise SystemExit(f"Missing or unsupported source: {source}")
        data = source.read_bytes()
        if source.name.startswith("._") or b"PRIVATE KEY-----" in data or ASSIGNED_SECRET.search(data):
            raise SystemExit(f"Forbidden content: {source}")
        text = data.decode("utf-8")
        declared = metadata(text, "Authority")
        if declared and declared != entry["authority"]:
            raise SystemExit(f"Authority mismatch for {source}: {declared} != {entry['authority']}")
        members.append((destination, data))
        provenance.append(
            {
                **entry,
                "commit": states[entry["repository"]]["commit"],
                "dirty": states[entry["repository"]]["dirty"],
                "reviewed": metadata(text, "Reviewed"),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )

    index = {
        "schema_version": 1,
        "built_on": date.today().isoformat(),
        "repositories": states,
        "sources": provenance,
    }
    members.append((".aster-provenance.json", json.dumps(index, indent=2, sort_keys=True).encode() + b"\n"))

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for destination, data in sorted(members):
                    info = tarfile.TarInfo(destination)
                    info.size = len(data)
                    info.mode = 0o444
                    info.mtime = 0
                    info.uid = info.gid = 0
                    info.uname = info.gname = "root"
                    archive.addfile(info, io.BytesIO(data))
    print(f"Created {output} with {len(provenance)} sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
