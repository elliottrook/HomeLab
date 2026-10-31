"""Run the M3 J1 non-overlap review where the private corpora are held.

The command reads the exact synthetic J1 subject and the seven exposed
development/calibration corpora, but emits only content-free receipts.  It
never accepts the sealed holdout and never prints or writes request text.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import nlu_joint_training_corpus_v1 as corpus
import nlu_joint_training_nonoverlap_receipt_v1 as receipt
from nlu_threshold_policy import decode_unique_json


SCHEMA = "aster-nlu-j1-private-review-result.v2"
SUBJECT_SOURCE_SHA256 = (
    "a70461c037ef24bf7a346dcefa769d8de938d6c54ddd8acf7d58c1e1370e7b79"
)
SUBJECT_NORMALIZED_TEXT_SET_SHA256 = (
    "891d7dc46c1567f3f7a1e5b489b9e043044944ae843f6b41b6b2cebd964192a3"
)
SUBJECT_CASE_COUNT = 400
AUTHORITY = "not-granted"


def _subject_texts(raw: bytes) -> set[str]:
    if corpus.sha256(raw) != SUBJECT_SOURCE_SHA256:
        raise ValueError("J1 private review subject SHA-256 changed")
    value = decode_unique_json(raw)
    cases = value.get("cases") if isinstance(value, dict) else None
    if not isinstance(cases, list) or len(cases) != SUBJECT_CASE_COUNT:
        raise ValueError("J1 private review subject must contain exactly 400 cases")
    if any(not isinstance(case, dict) for case in cases):
        raise ValueError("J1 private review subject contains an invalid case")
    texts = {corpus.normalized_text(case.get("text")) for case in cases}
    if len(texts) != SUBJECT_CASE_COUNT:
        raise ValueError("J1 private review subject contains duplicate text")
    text_set_raw = ("\n".join(sorted(texts)) + "\n").encode()
    if corpus.sha256(text_set_raw) != SUBJECT_NORMALIZED_TEXT_SET_SHA256:
        raise ValueError("J1 private review normalized subject changed")
    return texts


def evaluate(
    subject_raw: bytes,
    raw_by_reference: dict[str, bytes],
    *,
    expected: dict[str, dict[str, object]] = receipt.REFERENCES,
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    """Return a content-free result and, only on success, valid receipts."""
    if set(raw_by_reference) != set(expected):
        raise ValueError("private review must provide every exposed corpus exactly")
    subject_texts = _subject_texts(subject_raw)
    observations = {}
    receipts = {}
    for reference_class in sorted(expected):
        reference_texts, summary = corpus._reference_texts(
            reference_class, raw_by_reference[reference_class]
        )
        pinned = expected[reference_class]
        if summary != pinned:
            raise ValueError(f"{reference_class} identity changed")
        overlap_count = len(subject_texts & reference_texts)
        observations[reference_class] = {
            "artifact_sha256": summary["artifact_sha256"],
            "normalized_text_set_sha256": summary["normalized_text_set_sha256"],
            "case_count": summary["case_count"],
            "overlap_count": overlap_count,
        }

    status = "complete" if all(
        row["overlap_count"] == 0 for row in observations.values()
    ) else "no-go"
    if status == "complete":
        # Re-run the complete corpus boundary against the actual private bytes.
        summary = corpus.validate_corpus(subject_raw, raw_by_reference)
        if (summary["source_sha256"] != SUBJECT_SOURCE_SHA256
                or summary["normalized_text_set_sha256"]
                != SUBJECT_NORMALIZED_TEXT_SET_SHA256
                or summary["overlap_count"] != 0):
            raise ValueError("J1 private review summary changed")
        for reference_class in sorted(expected):
            pinned = expected[reference_class]
            value = {
                "schema": receipt.SCHEMA,
                "reference_class": reference_class,
                "subject_source_sha256": SUBJECT_SOURCE_SHA256,
                "subject_normalized_text_set_sha256": (
                    SUBJECT_NORMALIZED_TEXT_SET_SHA256
                ),
                "subject_case_count": SUBJECT_CASE_COUNT,
                "reference_artifact_sha256": pinned["artifact_sha256"],
                "reference_normalized_text_set_sha256": (
                    pinned["normalized_text_set_sha256"]
                ),
                "reference_case_count": pinned["case_count"],
                "overlap_count": 0,
                "reviewer": receipt.REVIEWER,
                "authority": AUTHORITY,
                "receipt_sha256": "",
            }
            value["receipt_sha256"] = receipt.canonical_sha256(value)
            receipts[reference_class] = value
        if expected == receipt.REFERENCES:
            encoded = {
                name: (json.dumps(value, sort_keys=True, separators=(",", ":"))
                       + "\n").encode()
                for name, value in receipts.items()
            }
            _, errors = receipt.validate_set(encoded)
            if errors:
                raise ValueError("generated J1 non-overlap receipt set is invalid")

    result = {
        "schema": SCHEMA,
        "subject_source_sha256": SUBJECT_SOURCE_SHA256,
        "subject_normalized_text_set_sha256": SUBJECT_NORMALIZED_TEXT_SET_SHA256,
        "subject_case_count": SUBJECT_CASE_COUNT,
        "reference_count": len(observations),
        "references": observations,
        "status": status,
        "receipts_written": len(receipts),
        "sealed_holdout_read": False,
        "authority": AUTHORITY,
    }
    return result, receipts


def _write_exclusive(path: Path, value: object) -> None:
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subject", type=Path, required=True)
    for reference_class in sorted(receipt.REFERENCES):
        parser.add_argument(
            "--" + reference_class,
            dest=reference_class.replace("-", "_"),
            type=Path,
            required=True,
        )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    raw_by_reference = {
        name: getattr(args, name.replace("-", "_")).read_bytes()
        for name in sorted(receipt.REFERENCES)
    }
    result, receipts = evaluate(args.subject.read_bytes(), raw_by_reference)

    args.output_dir.mkdir(mode=0o700, parents=False, exist_ok=False)
    os.chmod(args.output_dir, 0o700)
    for reference_class, value in sorted(receipts.items()):
        _write_exclusive(args.output_dir / f"{reference_class}.json", value)
    _write_exclusive(args.output_dir / "private-review-result.json", result)
    print(json.dumps({
        "schema": SCHEMA,
        "status": result["status"],
        "reference_count": result["reference_count"],
        "receipts_written": result["receipts_written"],
        "sealed_holdout_read": False,
        "authority": AUTHORITY,
    }, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
