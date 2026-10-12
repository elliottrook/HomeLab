"""Prepare a private, backend-blind development review packet.

Only accepts the public synthetic A1 fixture. Outputs answer text privately,
never to stdout or Git. This does not make case authorship/review independent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from capture_answer_feasibility import capture


REPO = Path(__file__).resolve().parents[2]


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _encoded(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def prepare(fixture_raw: bytes, attempts_raw: bytes, capture_raw: bytes) -> tuple[bytes, bytes]:
    expected = capture(fixture_raw, attempts_raw)
    observed = json.loads(capture_raw)
    if observed != expected:
        raise ValueError("capture does not reproduce original attempts")
    fixture = json.loads(fixture_raw)
    attempts = json.loads(attempts_raw)
    case_map = {case["id"]: case for case in fixture["cases"]}
    packet_rows = []
    template_rows = []
    for attempt in sorted(attempts["attempts"], key=lambda item: item["case_id"]):
        case = case_map[attempt["case_id"]]
        packet_rows.append({
            "case_id": case["id"], "class": case["class"],
            "request": case["request"], "clock": case["clock"],
            "permitted_context": case["context"], "answer": attempt["answer"],
            "status": attempt["status"], "source_ids": attempt["source_ids"],
            "rubric": case["rubric"], "prohibited_claims": case["prohibited_claims"],
        })
        template_rows.append({
            "case_id": case["id"],
            "rubric_checks": [None] * len(case["rubric"]),
            "prohibited_claims_present": [None] * len(case["prohibited_claims"]),
            "source_attribution_ok": None,
        })
    packet = {"schema_version": "aster-answer-review-packet.v0",
              "data_class": "synthetic-public-development",
              "capture_sha256": _sha(capture_raw), "cases": packet_rows,
              "qualification": "none; exposed development cases, reviewer independence unverified"}
    template = {"schema_version": "aster-answer-review.v0",
                "capture_sha256": _sha(capture_raw), "reviewer_id": None,
                "reviews": template_rows}
    return _encoded(packet), _encoded(template)


def _write_private(path: Path, raw: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "wb", closefd=False) as stream:
            stream.write(raw)
            stream.flush()
        os.fsync(fd)
    finally:
        os.close(fd)


def save(output_dir: Path, packet_raw: bytes, template_raw: bytes) -> dict:
    if not output_dir.is_absolute():
        raise ValueError("output directory must be absolute")
    resolved = output_dir.resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError("review packet must remain outside Git")
    output_dir.mkdir(mode=0o700, parents=False, exist_ok=False)
    try:
        _write_private(output_dir / "review-packet.json", packet_raw)
        _write_private(output_dir / "review-template.json", template_raw)
    except Exception:
        for name in ("review-packet.json", "review-template.json"):
            (output_dir / name).unlink(missing_ok=True)
        output_dir.rmdir()
        raise
    return {"output_dir": str(output_dir),
            "packet_sha256": _sha(packet_raw),
            "template_sha256": _sha(template_raw),
            "case_count": len(json.loads(packet_raw)["cases"])}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("attempts", type=Path)
    parser.add_argument("capture", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    packet, template = prepare(args.fixture.read_bytes(), args.attempts.read_bytes(),
                               args.capture.read_bytes())
    print(json.dumps(save(args.output_dir, packet, template), sort_keys=True))


if __name__ == "__main__":
    main()
