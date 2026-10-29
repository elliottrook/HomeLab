"""Public-gate entry point for the one-pass 35B joint-semantic candidate."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import nlu_joint_semantic_35b_v1 as candidate
import nlu_whole_label_public_runner_v1 as base


ENDPOINT = candidate.PUBLIC_GATE_ENDPOINT
CANDIDATE_NAME = "joint-semantic-35b-v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fixture_raw = args.fixture.read_bytes()
    token = args.key_file.read_text().splitlines()[0].strip()
    result = base.run(
        fixture_raw,
        token,
        endpoint=ENDPOINT,
        implementation=candidate,
        candidate_name=CANDIDATE_NAME,
    )
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps(base.summarize(fixture_raw, result), sort_keys=True))
    return 0 if result["attempted"] == 24 and result["valid"] == 24 else 2


if __name__ == "__main__":
    raise SystemExit(main())

