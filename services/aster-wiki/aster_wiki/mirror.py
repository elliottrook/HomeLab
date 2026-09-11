"""Deterministic, source-located Aster mirror packaging."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from .manifest import canonical_json

PIPELINE_VERSION = "1.0.0"
PROMPT_VERSION = "extractive-claims-v1"
GENERATOR = "deterministic-extractive"
ENTRY_ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,127}$")
INDEX_TERMS = {
    "assets": ("device", "hardware", "model", "equipment"),
    "services": ("service", "daemon", "application", "server"),
    "symptoms": ("error", "fail", "fault", "symptom", "warning"),
    "dependencies": ("depend", "requires", "prerequisite", "upstream"),
}


def _sections(text: str) -> list[tuple[int, int, str]]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    sections = []
    start = None
    buffer: list[str] = []
    for number, line in enumerate(lines, 1):
        if line.startswith("#") and buffer:
            sections.append((start or 1, number - 1, "\n".join(buffer).strip()))
            buffer, start = [], None
        if line.strip():
            start = start or number
            buffer.append(line.rstrip())
        elif buffer:
            sections.append((start or 1, number - 1, "\n".join(buffer).strip()))
            buffer, start = [], None
    if buffer:
        sections.append((start or 1, len(lines), "\n".join(buffer).strip()))
    return [(start, end, body) for start, end, body in sections if body][:128]


def _entry(source: dict, ordinal: int, start: int, end: int, body: str) -> tuple[str, bytes]:
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    entry_id = f"{source['source_id']}-{ordinal:03d}-{digest[:10]}"
    if not ENTRY_ID.fullmatch(entry_id):
        raise ValueError("invalid generated entry id")
    metadata = {
        "schema_version": 1,
        "entry_id": entry_id,
        "source_id": source["source_id"],
        "source_path": source["path"],
        "source_sha256": source["normalized_sha256"],
        "source_version": source.get("etag") or source.get("last_modified") or source["original_sha256"],
        "source_locator": f"lines {start}-{end}",
        "generated_at": source.get("retrieved_at", "1970-01-01T00:00:00+00:00"),
        "generator_model": GENERATOR,
        "generator_prompt_version": PROMPT_VERSION,
        "authority": "derived-memory",
        "review_state": "generated",
        "confidence": "high",
        "supersedes": None,
    }
    header = ["---"] + [f"{key}: {json.dumps(value, sort_keys=True)}" for key, value in metadata.items()] + ["---"]
    content = "\n".join(header) + "\n\n## Source-located claim\n\n" + body + "\n"
    return entry_id, content.encode("utf-8")


def build_mirror(wiki_root: Path, output_root: Path) -> dict:
    lock = json.loads((wiki_root / "sources/accepted-lock.json").read_text(encoding="utf-8"))
    stage = Path(tempfile.mkdtemp(prefix=".mirror-", dir=str(output_root.parent)))
    indexes = {name: {} for name in INDEX_TERMS}
    provenance = {}
    entries = 0
    try:
        for source in sorted(lock.get("sources", []), key=lambda item: item["source_id"]):
            path = wiki_root / source["path"]
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != source["normalized_sha256"]:
                raise ValueError(f"accepted source mismatch: {source['source_id']}")
            if source.get("media_type") == "application/pdf":
                continue
            text = path.read_text(encoding="utf-8")
            for ordinal, (start, end, body) in enumerate(_sections(text), 1):
                entry_id, encoded = _entry(source, ordinal, start, end, body)
                target = stage / "entries" / source["source_id"] / f"{entry_id}.md"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(encoded)
                provenance[entry_id] = {
                    "source_id": source["source_id"], "source_path": source["path"],
                    "source_sha256": source["normalized_sha256"],
                    "source_locator": f"lines {start}-{end}",
                }
                lowered = body.lower()
                for name, terms in INDEX_TERMS.items():
                    if any(term in lowered for term in terms):
                        indexes[name].setdefault(source["source_id"], []).append(entry_id)
                entries += 1
        index_root = stage / "indexes"
        index_root.mkdir(parents=True, exist_ok=True)
        for name, data in indexes.items():
            (index_root / f"{name}.json").write_bytes(canonical_json({"schema_version": 1, "entries": data}))
        (index_root / "provenance.json").write_bytes(canonical_json({"schema_version": 1, "entries": provenance}))
        accepted_input = {"schema_version": 1, "sources": lock.get("sources", [])}
        state_root = stage / "state"
        state_root.mkdir()
        (state_root / "accepted-input.json").write_bytes(canonical_json(accepted_input))
        tree_hash = package_hash(stage)
        generation = {"schema_version": 1, "pipeline_version": PIPELINE_VERSION,
                      "prompt_version": PROMPT_VERSION, "entries": entries,
                      "accepted_input_sha256": hashlib.sha256(canonical_json(accepted_input)).hexdigest(),
                      "content_sha256": tree_hash, "status": "accepted"}
        (state_root / "generation.json").write_bytes(canonical_json(generation))
        if output_root.exists():
            shutil.rmtree(output_root)
        os.replace(stage, output_root)
        return generation
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def package_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file() and item.name != "generation.json"):
        digest.update(str(path.relative_to(root)).encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def verify_mirror(wiki_root: Path, mirror_root: Path) -> dict:
    provenance = json.loads((mirror_root / "indexes/provenance.json").read_text(encoding="utf-8"))["entries"]
    checked = 0
    for entry_id, item in provenance.items():
        source = wiki_root / item["source_path"]
        lines = source.read_text(encoding="utf-8").splitlines()
        match = re.fullmatch(r"lines (\d+)-(\d+)", item["source_locator"])
        if not match or hashlib.sha256(source.read_bytes()).hexdigest() != item["source_sha256"]:
            raise ValueError(f"invalid provenance: {entry_id}")
        excerpt = "\n".join(lines[int(match.group(1)) - 1:int(match.group(2))]).strip()
        entry = (mirror_root / "entries" / item["source_id"] / f"{entry_id}.md").read_text(encoding="utf-8")
        if not excerpt or excerpt not in entry:
            raise ValueError(f"unsupported claim: {entry_id}")
        checked += 1
    return {"status": "ok", "checked": checked, "content_sha256": package_hash(mirror_root)}
