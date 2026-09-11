"""Deterministic, source-located Aster mirror packaging."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

from .manifest import canonical_json

PIPELINE_VERSION = "1.2.0"
PROMPT_VERSION = "extractive-claims-v1"
GENERATOR = "deterministic-extractive"
ENTRY_ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,127}$")
UNSAFE_TEXT = re.compile(
    r"(?im)^\s*(?:api[_-]?key|password|passwd|secret|token)\s*[:=]\s*\S{8,}|"
    r"ignore (?:all |any )?(?:previous|prior) instructions|system prompt|exfiltrat"
)
INDEX_TERMS = {
    "assets": ("device", "hardware", "model", "equipment"),
    "services": ("service", "daemon", "application", "server"),
    "symptoms": ("error", "fail", "fault", "symptom", "warning"),
    "dependencies": ("depend", "requires", "prerequisite", "upstream"),
    "recovery": ("recover", "restore", "rollback", "repair", "replace"),
}
SEMANTIC_TERMS = {
    "warnings": ("warning", "caution", "danger", "destructive", "must not", "do not"),
    "uncertainty": ("uncertain", "unknown", "unresolved", " may ", " might "),
    "version-scope": ("version", "release", "model", "applies to", "applicable to"),
    "contradictions": ("conflict", "contradict", "disagree", "inconsistent"),
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


def extract_pdf(path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"],
        check=True, capture_output=True, timeout=30,
        env={"PATH": os.environ.get("PATH", "")},
    )
    if len(result.stdout) > 5 * 1024 * 1024:
        raise ValueError("PDF extracted text exceeds limit")
    return result.stdout.decode("utf-8", errors="strict")


def _source_sections(path: Path, media_type: str,
                     pdf_extractor: Callable[[Path], str] | None = None) -> list[tuple[str, str]]:
    if media_type == "application/pdf":
        extracted = (pdf_extractor or extract_pdf)(path)
        result = []
        for page_number, page in enumerate(extracted.split("\f"), 1):
            for start, end, body in _sections(page):
                result.append((f"page {page_number} / lines {start}-{end}", body))
    else:
        result = [(f"lines {start}-{end}", body)
                  for start, end, body in _sections(path.read_text(encoding="utf-8"))]
    if any(UNSAFE_TEXT.search(body) for _, body in result):
        raise ValueError("unsafe extracted mirror content")
    return result[:128]


def _entry(source: dict, ordinal: int, locator: str, body: str,
           supersedes: str | None = None) -> tuple[str, bytes]:
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
        "source_locator": locator,
        "generated_at": source.get("retrieved_at", "1970-01-01T00:00:00+00:00"),
        "generator_model": GENERATOR,
        "generator_prompt_version": PROMPT_VERSION,
        "authority": "derived-memory",
        "review_state": "generated",
        "confidence": "high",
        "supersedes": supersedes,
    }
    header = ["---"] + [f"{key}: {json.dumps(value, sort_keys=True)}" for key, value in metadata.items()] + ["---"]
    content = "\n".join(header) + "\n\n## Source-located claim\n\n" + body + "\n"
    return entry_id, content.encode("utf-8")


def build_mirror(wiki_root: Path, output_root: Path,
                 pdf_extractor: Callable[[Path], str] | None = None) -> dict:
    lock = json.loads((wiki_root / "sources/accepted-lock.json").read_text(encoding="utf-8"))
    stage = Path(tempfile.mkdtemp(prefix=".mirror-", dir=str(output_root.parent)))
    indexes = {name: {} for name in (*INDEX_TERMS, *SEMANTIC_TERMS)}
    provenance = {}
    entries = 0
    previous = {}
    reusable: dict[str, list[tuple[str, dict, Path]]] = {}
    previous_provenance = output_root / "indexes/provenance.json"
    previous_generation = output_root / "state/generation.json"
    if previous_provenance.is_file() and previous_generation.is_file() and json.loads(
            previous_generation.read_text(encoding="utf-8")).get("pipeline_version") == PIPELINE_VERSION:
        old = json.loads(previous_provenance.read_text(encoding="utf-8")).get("entries", {})
        previous = {
            (item["source_id"], item["source_locator"]): entry_id
            for entry_id, item in old.items()
        }
        for entry_id, item in old.items():
            old_entry = output_root / "entries" / item["source_id"] / f"{entry_id}.md"
            if old_entry.is_file():
                reusable.setdefault(item["source_id"], []).append((entry_id, item, old_entry))
    seen_claims = set()
    try:
        for source in sorted(lock.get("sources", []), key=lambda item: item["source_id"]):
            path = wiki_root / source["path"]
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != source["normalized_sha256"]:
                raise ValueError(f"accepted source mismatch: {source['source_id']}")
            unchanged = sorted(
                (item for item in reusable.get(source["source_id"], [])
                 if item[1]["source_sha256"] == source["normalized_sha256"]),
                key=lambda item: item[0],
            )
            if unchanged:
                for entry_id, item, old_entry in unchanged:
                    encoded = old_entry.read_bytes()
                    body = encoded.decode("utf-8").split("## Source-located claim\n\n", 1)[-1].rstrip("\n")
                    target = stage / "entries" / source["source_id"] / f"{entry_id}.md"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(encoded)
                    provenance[entry_id] = item
                    lowered, padded = body.lower(), f" {body.lower()} "
                    for name, terms in INDEX_TERMS.items():
                        if any(term in lowered for term in terms):
                            indexes[name].setdefault(source["source_id"], []).append(entry_id)
                    for name, terms in SEMANTIC_TERMS.items():
                        if any(term in padded for term in terms):
                            indexes[name].setdefault(source["source_id"], []).append(entry_id)
                    seen_claims.add((source["normalized_sha256"], hashlib.sha256(body.encode()).hexdigest()))
                    entries += 1
                continue
            for ordinal, (locator, body) in enumerate(
                    _source_sections(path, source.get("media_type", "text/plain"), pdf_extractor), 1):
                claim_key = (source["normalized_sha256"], hashlib.sha256(body.encode()).hexdigest())
                if claim_key in seen_claims:
                    continue
                seen_claims.add(claim_key)
                prior_entry = previous.get((source["source_id"], locator))
                entry_id, encoded = _entry(source, ordinal, locator, body, prior_entry)
                if prior_entry == entry_id:
                    entry_id, encoded = _entry(source, ordinal, locator, body, None)
                target = stage / "entries" / source["source_id"] / f"{entry_id}.md"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(encoded)
                provenance[entry_id] = {
                    "source_id": source["source_id"], "source_path": source["path"],
                    "source_sha256": source["normalized_sha256"],
                    "source_locator": locator,
                    "media_type": source.get("media_type", "text/plain"),
                }
                lowered = body.lower()
                for name, terms in INDEX_TERMS.items():
                    if any(term in lowered for term in terms):
                        indexes[name].setdefault(source["source_id"], []).append(entry_id)
                padded = f" {lowered} "
                for name, terms in SEMANTIC_TERMS.items():
                    if any(term in padded for term in terms):
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
        verify_mirror(wiki_root, stage, pdf_extractor)
        backup = output_root.with_name(output_root.name + ".last-good")
        if backup.exists():
            shutil.rmtree(backup)
        if output_root.exists():
            os.replace(output_root, backup)
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


def verify_mirror(wiki_root: Path, mirror_root: Path,
                  pdf_extractor: Callable[[Path], str] | None = None) -> dict:
    provenance = json.loads((mirror_root / "indexes/provenance.json").read_text(encoding="utf-8"))["entries"]
    checked = 0
    source_sections: dict[tuple[str, str], dict[str, str]] = {}
    for entry_id, item in provenance.items():
        source = wiki_root / item["source_path"]
        if hashlib.sha256(source.read_bytes()).hexdigest() != item["source_sha256"]:
            raise ValueError(f"invalid provenance: {entry_id}")
        media_type = item.get("media_type", "text/plain")
        cache_key = (str(source), media_type)
        if cache_key not in source_sections:
            source_sections[cache_key] = dict(_source_sections(source, media_type, pdf_extractor))
        sections = source_sections[cache_key]
        excerpt = sections.get(item["source_locator"], "")
        entry = (mirror_root / "entries" / item["source_id"] / f"{entry_id}.md").read_text(encoding="utf-8")
        if not excerpt or excerpt not in entry:
            raise ValueError(f"unsupported claim: {entry_id}")
        checked += 1
    return {"status": "ok", "checked": checked, "content_sha256": package_hash(mirror_root)}


def rollback_mirror(output_root: Path) -> None:
    backup = output_root.with_name(output_root.name + ".last-good")
    if not backup.is_dir():
        raise ValueError("no last-good mirror retained")
    failed = output_root.with_name(output_root.name + ".rolled-back")
    if failed.exists():
        shutil.rmtree(failed)
    if output_root.exists():
        os.replace(output_root, failed)
    os.replace(backup, output_root)
