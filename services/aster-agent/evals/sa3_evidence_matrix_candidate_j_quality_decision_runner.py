"""Run Candidate-J's frozen three-reviewer decision over retained files."""

from __future__ import annotations

import json
from pathlib import Path

from sa3_evidence_matrix_candidate_j_quality_decision import decide
from sa3_evidence_matrix_candidate_j_quality_result_contract import decode_unique


def run(packet_path: Path, keys_path: Path, result_path: Path,
        review_paths: list[Path]) -> dict[str, object]:
    if len(review_paths) != 3:
        raise ValueError("exactly three review files required")
    return decide(
        decode_unique(packet_path.read_bytes()),
        decode_unique(keys_path.read_bytes()),
        decode_unique(result_path.read_bytes()),
        [decode_unique(path.read_bytes()) for path in review_paths],
    )


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--keys", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--review", required=True, type=Path, action="append")
    args = parser.parse_args(argv)
    value = run(args.packet, args.keys, args.result, args.review)
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
