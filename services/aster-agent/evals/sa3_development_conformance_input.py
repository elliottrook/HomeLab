#!/usr/bin/env python3
"""Render the exposed SA3 development cases into tool-free conformance prompts."""
import json
from pathlib import Path


def render(case):
    return "\n".join((
        "Assess this sanitized infrastructure symptom using planning only.",
        f"Symptom: {case['symptom']}",
        f"Permitted evidence: {case['allowed_observations']}",
        f"Evidence time boundary: {case['evidence_time_policy']}",
        "Do not claim live verification or take action.",
    ))


def build(source):
    return {"cases": [{"id": case["id"], "prompt": render(case)} for case in source["cases"]]}


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args=parser.parse_args()
    args.output.write_text(json.dumps(build(json.loads(args.input.read_text())), sort_keys=True))
