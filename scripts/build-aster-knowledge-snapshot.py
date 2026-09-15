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


def mirror_members(root: Path) -> tuple[list[tuple[str, bytes]], list[dict[str, object]], dict[str, object]]:
    """Validate and map a generated mirror into derived-memory snapshot members."""
    generation_path = root / "state/generation.json"
    provenance_path = root / "indexes/provenance.json"
    if not generation_path.is_file() or not provenance_path.is_file():
        raise ValueError("mirror generation or provenance manifest missing")
    generation = json.loads(generation_path.read_text(encoding="utf-8"))
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))["entries"]
    members = []
    records = []
    source_counts: dict[str, int] = {}
    for path in sorted((root / "entries").rglob("*.md")):
        data = path.read_bytes()
        if b"PRIVATE KEY-----" in data or ASSIGNED_SECRET.search(data):
            raise ValueError(f"forbidden mirror content: {path}")
        relative = str(path.relative_to(root))
        entry_id = path.stem
        item = provenance.get(entry_id)
        text = data.decode("utf-8")
        if (not item or 'authority: "derived-memory"' not in text or
                item.get("source_locator") not in text):
            raise ValueError(f"invalid mirror provenance: {path}")
        destination = f"mirror/{relative}"
        members.append((destination, data))
        source_counts[path.parent.name] = source_counts.get(path.parent.name, 0) + 1
        records.append({
            "repository": "aster-knowledge-mirror", "path": relative,
            "destination": destination, "authority": "derived-memory",
            "commit": generation["content_sha256"], "dirty": False,
            "reviewed": None, "sha256": hashlib.sha256(data).hexdigest(),
            "human_source": item["source_path"],
            "source_locator": item["source_locator"],
            "source_sha256": item["source_sha256"],
        })
    if len(records) != generation.get("entries") or set(provenance) != {Path(x["path"]).stem for x in records}:
        raise ValueError("mirror entry count does not match accepted generation")
    directories_path = root / "indexes/directories.json"
    try:
        directories_payload = json.loads(directories_path.read_text(encoding="utf-8"))
        directories = directories_payload["entries"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError("mirror directory index missing or invalid") from exc
    if directories_payload.get("schema_version") != 1 or not isinstance(directories, dict):
        raise ValueError("mirror directory index missing or invalid")
    if set(directories) != set(source_counts):
        raise ValueError("mirror directory index sources do not match entries")
    for source_id, count in source_counts.items():
        directory = directories[source_id]
        if (
            not isinstance(directory, dict)
            or directory.get("entry_count") != count
            or not isinstance(directory.get("abstract"), str)
            or not directory["abstract"].strip()
            or not isinstance(directory.get("topics"), list)
            or not 1 <= len(directory["topics"]) <= 6
            or not all(isinstance(topic, str) and topic for topic in directory["topics"])
        ):
            raise ValueError(f"invalid mirror directory entry: {source_id}")
    members.append(("mirror/indexes/directories.json", directories_path.read_bytes()))
    return members, records, {
        "commit": generation["content_sha256"], "dirty": False,
        "accepted_input_sha256": generation["accepted_input_sha256"],
    }


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
    parser.add_argument("--mirror-root", type=Path, help="validated generated Aster mirror")
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

    if args.mirror_root:
        extra_members, extra_provenance, mirror_state = mirror_members(args.mirror_root.resolve())
        for destination, data in extra_members:
            if destination in destinations:
                raise SystemExit(f"Duplicate destination: {destination}")
            destinations.add(destination)
            members.append((destination, data))
        provenance.extend(extra_provenance)
        states["aster-knowledge-mirror"] = mirror_state

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
