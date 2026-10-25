"""Validate the no-effect LXC110 NLU calibration staging manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nlu_threshold_policy import decode_unique_json, sha256


SCHEMA = "aster-nlu-calibration-stage-manifest.v1"
INPUTS = [
    ("cases.json", "6ba07b680d8f49722559a7b2774e151f613428a106cc7f740b43cd972021726e", "private-synthetic"),
    ("release.json", "f13a795f5c3b1890d87e2b6417c972c47817ded027f607bc00ad05a6e4c894a1", "content-free"),
    ("nlu-development-v1.json", "1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785", "public-synthetic"),
    ("nlu_calibration_runner.py", "484a09d4d1655336808767ead76d7803f6eadf783bbda5bdf1eaec8726389833", "source"),
    ("nlu_calibration_corpus.py", "3b383dcc181cc5c6a41d3aa9a30bc72ee30896ff0375bbc270de9bd82ba4f983", "source"),
    ("nlu_calibration_release.py", "bdc93c7892eda067c0675c04259c996d6f43935ee84ba4ae6bbea6d1892488d9", "source"),
    ("nlu_calibration_score.py", "ec4f4e44ff595617f1fe8e337b587bbab049204d001dd2ba050ee1fb146022fd", "source"),
    ("nlu_calibration_journal.py", "992960fe76540941fe9adf7b75ddaf82541c55039782bf4cf360ad6c5279a744", "source"),
    ("nlu_local_model_adapter.py", "3a3b09f12bcd2088f0d604363a5bc0e69190c177eced50dc5a14eb582749aed0", "source"),
    ("nlu_threshold_policy.py", "984932d8716531858972e22723fe962701077f9a15991c58384c6ee6661ebb5d", "source"),
]


def expected_manifest() -> dict:
    return {
        "schema": SCHEMA,
        "status": "staging-plan-only",
        "run_id": "nlu-calibration-v1",
        "guest_id": 110,
        "base_directory": "/var/lib/aster-nlu-calibration",
        "directory_mode": "0700",
        "file_mode": "0600",
        "endpoint": "http://192.168.70.12:11435/v1/chat/completions",
        "key_path": "/etc/aster-llama-api-keys",
        "inputs": [
            {"name": name, "sha256": digest, "data_class": data_class}
            for name, digest, data_class in INPUTS
        ],
        "outputs": ["run.json", "attempt-journal.jsonl"],
        "excluded": [
            "labels.json", "nlu-policy-registration-v1.json",
            "nlu_threshold_selection.py", "cloud-credentials", "tools",
        ],
        "cleanup": "only-after-verified-mac-custody-and-production-postcheck",
        "uncertain_outcome": "retain-owner-only-and-do-not-retry",
        "authority": "not-granted",
    }


def load_and_validate(raw: bytes) -> dict:
    try:
        value = decode_unique_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("stage manifest must be unique-key UTF-8 JSON") from error
    if value != expected_manifest():
        raise ValueError("stage manifest does not match the frozen no-effect packet")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the frozen NLU staging packet.")
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        raw = args.manifest.read_bytes()
        value = load_and_validate(raw)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps({
        "schema": value["schema"],
        "input_count": len(value["inputs"]),
        "manifest_sha256": sha256(raw),
        "authority": value["authority"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
