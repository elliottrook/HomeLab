"""Build a private model-blind review packet from a completed D4 journal."""

import argparse
import hashlib
import json
import os
from pathlib import Path

from sa3_fresh_package import decode_journal_json, digest
from sa3_investigation import answer_shape_status


RUBRIC = (
    "diagnosis",
    "evidence",
    "freshness",
    "scope",
    "verification",
    "no_false_completion",
)
REFERENCE_FIELDS = (
    "family",
    "symptom",
    "allowed_observations",
    "evidence_time_policy",
    "expected_discriminating_checks",
    "permitted_outcome",
    "forbidden_effect",
    "repair_scope",
    "expected_postcheck",
)


def canonical_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def read_ledger(path, expected_release, limit=4 * 1024 * 1024):
    raw = Path(path).read_bytes()
    if len(raw) > limit or (raw and not raw.endswith(b"\n")):
        raise ValueError("invalid private journal envelope")
    previous = ""
    events = []
    for line in raw.decode().splitlines():
        row = decode_journal_json(line)
        if not isinstance(row, dict) or set(row) != {"release", "previous", "event", "digest"}:
            raise ValueError("invalid private journal row")
        sealed = dict(row)
        stored = sealed.pop("digest")
        if (
            row["release"] != expected_release
            or row["previous"] != previous
            or digest(sealed) != stored
        ):
            raise ValueError("private journal integrity mismatch")
        previous = stored
        events.append(row["event"])
    return events, sha256_bytes(raw)


def build_packet(
        fixtures, source, events, ledger_sha256, expected_cases=12,
        run_digest=None, candidate_alias="candidate-A"):
    if not isinstance(fixtures, dict) or not isinstance(fixtures.get("cases"), list):
        raise ValueError("invalid fixture bundle")
    if not isinstance(source, dict) or not isinstance(source.get("cases"), list):
        raise ValueError("invalid review source")
    fixture_cases = fixtures["cases"]
    source_cases = source["cases"]
    fixture_ids = [case.get("id") for case in fixture_cases]
    source_ids = [case.get("id") for case in source_cases]
    if (
        len(fixture_cases) != expected_cases
        or len(source_cases) != expected_cases
        or fixture_ids != source_ids
        or len(set(fixture_ids)) != expected_cases
    ):
        raise ValueError("review case identity mismatch")

    finished = {}
    started = set()
    for event in events:
        if not isinstance(event, dict) or event.get("type") not in ("started", "finished"):
            raise ValueError("invalid private journal event")
        if event["type"] == "started":
            if set(event) != {"type", "case_id", "mode"} or event["mode"] != "nonthinking":
                raise ValueError("invalid start event")
            if event["case_id"] in started:
                raise ValueError("duplicate start event")
            started.add(event["case_id"])
            continue
        if set(event) != {"type", "result"}:
            raise ValueError("invalid finish event")
        result = event["result"]
        ident = result.get("case_id") if isinstance(result, dict) else None
        if ident in finished:
            raise ValueError("duplicate finish event")
        finished[ident] = result
    if started != set(fixture_ids) or set(finished) != set(fixture_ids):
        raise ValueError("incomplete review journal")

    source_by_id = {case["id"]: case for case in source_cases}
    review_cases = []
    for index, fixture in enumerate(fixture_cases, 1):
        ident = fixture["id"]
        result = finished[ident]
        if result.get("status") not in ("conclude", "clarify"):
            raise ValueError("nonterminal result cannot enter review")
        steps = result.get("steps")
        if not isinstance(steps, list) or not steps:
            raise ValueError("terminal result lacks steps")
        answer = steps[-1].get("answer") if isinstance(steps[-1], dict) else None
        if (
            not isinstance(answer, dict)
            or answer.get("decision") != result["status"]
            or answer.get("check") != ""
            or answer.get("effects") != []
        ):
            raise ValueError("terminal answer lineage mismatch")
        if run_digest is not None and answer_shape_status(answer) != "valid":
            raise ValueError("invalid v2 terminal answer contract")
        reference = source_by_id[ident]
        if any(field not in reference for field in REFERENCE_FIELDS):
            raise ValueError("incomplete review reference")
        review_cases.append({
            "review_id": f"D4R-{index:02d}",
            "scenario": fixture["prompt"],
            "reference": {field: reference[field] for field in REFERENCE_FIELDS},
            "candidate": {
                "terminal_status": result["status"],
                "selected_checks": result.get("checks", []),
                "observations": result.get("observations", []),
                "evidence_ids": answer.get("evidence_ids"),
                "summary": answer.get("summary"),
                "effects": answer.get("effects"),
            },
        })
        if run_digest is not None:
            review_cases[-1]["candidate"].update({
                "discrimination": answer.get("discrimination"),
                "post_change_verification": answer.get("post_change_verification"),
            })
    packet = {
        "schema": "aster-d4-model-blind-review-packet.v1",
        "candidate_alias": candidate_alias,
        "model_identity_disclosed": False,
        "timing_disclosed": False,
        "ledger_sha256": ledger_sha256,
        "rubric": list(RUBRIC),
        "cases": review_cases,
    }
    if run_digest is not None:
        if (
            not isinstance(run_digest, str)
            or len(run_digest) != 64
            or any(character not in "0123456789abcdef" for character in run_digest)
            or not isinstance(candidate_alias, str)
            or not candidate_alias.strip()
            or len(candidate_alias) > 64
        ):
            raise ValueError("invalid review candidate identity")
        packet["schema"] = "aster-d4-model-blind-review-packet.v2"
        packet["run_digest"] = run_digest
    return packet


def blank_review(packet_sha256, packet):
    return {
        "schema": "aster-d4-model-blind-review.v1",
        "packet_sha256": packet_sha256,
        "reviewer": "",
        "model_blind": True,
        "cases": [
            {
                "review_id": case["review_id"],
                "judgments": {field: None for field in RUBRIC},
                "notes": "",
            }
            for case in packet["cases"]
        ],
    }


def write_exclusive(path, value):
    raw = canonical_bytes(value)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return sha256_bytes(raw)


def main(argv=None):
    here = Path(__file__).parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--run-digest", required=True)
    parser.add_argument("--candidate-alias", required=True)
    parser.add_argument("--fixtures", type=Path, default=here / "sysadmin-sa3-development-fixtures-draft-v1.json")
    parser.add_argument("--source", type=Path, default=here / "sysadmin-incident-development-extension-draft-v1.json")
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--review", required=True, type=Path)
    args = parser.parse_args(argv)

    events, ledger_sha256 = read_ledger(args.ledger, args.run_digest)
    packet = build_packet(
        json.loads(args.fixtures.read_text()),
        json.loads(args.source.read_text()),
        events,
        ledger_sha256,
        run_digest=args.run_digest,
        candidate_alias=args.candidate_alias,
    )
    packet_sha256 = write_exclusive(args.packet, packet)
    review_sha256 = write_exclusive(args.review, blank_review(packet_sha256, packet))
    print(json.dumps({
        "status": "review_packet_ready",
        "cases": len(packet["cases"]),
        "candidate_alias": packet["candidate_alias"],
        "model_identity_disclosed": packet["model_identity_disclosed"],
        "packet_sha256": packet_sha256,
        "blank_review_sha256": review_sha256,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
