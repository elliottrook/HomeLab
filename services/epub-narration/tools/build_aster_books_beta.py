#!/usr/bin/env python3
"""Build an immutable, inactive Aster Books beta with synthetic ready data."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from epub_narration.publication import VOICE, publish_generation, sha256_file


TEXTS = (
    "The quiet test begins. The first marker follows.",
    "A second chapter opens. The final marker follows.",
)


VERIFY = '''#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'runtime'))
from epub_narration.aster_books import BetaSession,ProgressStore,load_ready_book,probe_opus
book=load_ready_book(ROOT/'data',1,probe_opus)
session=BetaSession(book,ProgressStore(ROOT/'test-progress'))
if session.highlight() is None:raise ValueError('beta-highlight')
session.seek(24000)
if session.highlight() is None:raise ValueError('beta-seek-highlight')
session.select_chapter(2);session.seek(12000);session.close()
resumed=BetaSession(book,ProgressStore(ROOT/'test-progress'))
if (resumed.chapter,resumed.sample)!=(2,12000):raise ValueError('beta-progress-resume')
print(json.dumps({'state':'passed','chapters':len(book.chapters),'active':False,'production_entry':False},sort_keys=True))
'''


def _chapter_files(stage: Path, audio: tuple[bytes, ...]) -> list[dict]:
    if len(audio) != len(TEXTS):
        raise ValueError("beta-audio-count")
    files = []
    for index, (text, payload) in enumerate(zip(TEXTS, audio), 1):
        stem = f"{index:04d}"
        boundary = text.index(".") + 1
        spans = ((0, boundary), (boundary + 1, len(text)))
        cues = [{
            "source_start": start,
            "source_end": end,
            "start_sample": offset * 24_000,
            "end_sample": (offset + 1) * 24_000,
            "spoken_sha256": hashlib.sha256(text[start:end].encode()).hexdigest(),
        } for offset, (start, end) in enumerate(spans)]
        content_hash = hashlib.sha256(text.encode()).hexdigest()
        values = {
            f"chapters/{stem}.opus": payload,
            f"timing/{stem}.json": json.dumps({
                "schema": 1, "timing_level": "sentence-sample-index", "sample_rate": 24_000,
                "total_samples": 48_000, "cleaned_text_sha256": content_hash, "cues": cues,
            }, sort_keys=True, separators=(",", ":")).encode(),
            f"content/{stem}.json": json.dumps({
                "schema": 1, "chapter": index, "text": text, "text_sha256": content_hash,
            }, sort_keys=True, separators=(",", ":")).encode(),
        }
        for relative, raw in values.items():
            path = stage / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            path.chmod(0o600)
            files.append({"path": relative, "bytes": len(raw), "sha256": sha256_file(path)})
    return files


def build(output: Path, audio: tuple[bytes, ...]) -> str:
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    package = output / "runtime" / "epub_narration"
    package.mkdir(mode=0o700, parents=True)
    for name in ("__init__.py", "publication.py", "aster_books.py"):
        shutil.copyfile(ROOT / "epub_narration" / name, package / name)
        (package / name).chmod(0o600)
    data = output / "data"
    stage = output / ".synthetic-stage"
    files = _chapter_files(stage, audio)
    source_hash = hashlib.sha256(b"aster-books-beta-synthetic-source-v1").hexdigest()
    manifest = {
        "schema": 1, "state": "ready-candidate",
        "contracts": {"compiler": "aster-books-beta-synthetic-v1", "parser": "synthetic-v1",
                      "cleanup": "synthetic-v1", "encoder": "ffmpeg-libopus-48k-v1"},
        "book_id": 1, "source_sha256": source_hash, "voice": VOICE,
        "timing_level": "sentence-sample-index", "sample_rate": 24_000,
        "codec": {"name": "opus", "bitrate": 48_000, "channels": 1}, "files": files,
    }
    (stage / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")))
    (stage / "manifest.json").chmod(0o600)
    publish_generation(stage, data)
    verifier = output / "verify_beta.py"
    verifier.write_text(VERIFY)
    verifier.chmod(0o700)
    members = {}
    for path in sorted(output.rglob("*")):
        if path.is_file():
            members[str(path.relative_to(output))] = sha256_file(path)
    bundle = {
        "schema": 1, "kind": "aster-books-compiler-beta-v1", "active": False,
        "production_entry": False, "network": False, "synthetic": True,
        "shared_progress": False, "files": members,
    }
    raw = (json.dumps(bundle, sort_keys=True, indent=2) + "\n").encode()
    (output / "bundle.json").write_bytes(raw)
    (output / "bundle.json").chmod(0o600)
    return hashlib.sha256(raw).hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audio", type=Path, action="append", required=True)
    arguments = parser.parse_args()
    print(build(arguments.output, tuple(path.read_bytes() for path in arguments.audio)))
