"""Dry-run by default executor for the reviewed twelve-case D4 development set."""

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request

from sa3_fresh_execute import (
    BASE,
    build_local_opener,
    decode_unique_json,
    load_bounded_json,
    parse_processing_metric,
    read_bounded,
)
from sa3_fresh_package import digest, run_package
from sa3_investigation import investigate
from sa3_investigation_runner import sanitize_response
from validate_sa3_fixture_bundle import review_source_sha256, validate_for_qualification


MODEL = "qwen3.5-9b"
RUNTIME = "Qwen3.5-9B Q4_K_M / llama.cpp b11429 / SYCL Level Zero"
REQUEST_TIMEOUT_SECONDS = 60
SESSION_TIMEOUT_SECONDS = 180
EXPECTED_CASES = 12


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_spec(fixtures, source_corpus, source_plan):
    here = Path(__file__).parent
    implementation = {
        name: file_sha256(here / name)
        for name in (
            "sa3_development_execute.py",
            "sa3_fair_request.py",
            "sa3_fresh_execute.py",
            "sa3_fresh_package.py",
            "sa3_investigation.py",
            "sa3_investigation_runner.py",
            "validate_sa3_fixture_bundle.py",
        )
    }
    return {
        "schema": "aster-sa3-development-run.v1",
        "fixture_file_sha256": file_sha256(fixtures),
        "fixture_review_sha256": review_source_sha256(
            load_bounded_json(fixtures)
        ),
        "source_corpus_sha256": file_sha256(source_corpus),
        "source_plan_sha256": file_sha256(source_plan),
        "implementation_sha256": implementation,
        "endpoint": BASE,
        "model": MODEL,
        "runtime": RUNTIME,
        "mode": "nonthinking",
        "cases": EXPECTED_CASES,
        "sessions": EXPECTED_CASES,
        "maximum_model_calls": EXPECTED_CASES * 3,
        "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        "session_timeout_seconds": SESSION_TIMEOUT_SECONDS,
        "connected_tools": False,
        "effects": False,
        "approval_required": True,
    }


def validate_development_cases(bundle, manifest, source_corpus, source_plan):
    errors = validate_for_qualification(bundle, source_corpus, source_plan)
    if errors:
        raise ValueError("; ".join(errors))
    cases = bundle["cases"]
    if len(cases) != EXPECTED_CASES:
        raise ValueError("exactly twelve reviewed development cases required")
    if manifest.get("release_digest") != digest(manifest.get("run_spec")):
        raise ValueError("development run manifest digest mismatch")
    if manifest["run_spec"]["fixture_file_sha256"] != hashlib.sha256(
            json.dumps(bundle, indent=2, sort_keys=True).encode() + b"\n").hexdigest():
        raise ValueError("development fixture file digest mismatch")
    return copy.deepcopy(cases)


def main(argv=None):
    here = Path(__file__).parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, default=here / "sysadmin-sa3-development-fixtures-draft-v1.json")
    parser.add_argument("--source-corpus", type=Path, default=here / "sysadmin-incident-development-extension-draft-v1.json")
    parser.add_argument("--source-plan", type=Path, default=here / "sysadmin-incident-development-plan-v1.json")
    parser.add_argument("--expected-run-digest")
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)

    bundle = load_bounded_json(args.fixtures)
    spec = run_spec(args.fixtures, args.source_corpus, args.source_plan)
    manifest = {"run_spec": spec, "release_digest": digest(spec)}

    def case_validator(value, selected_manifest):
        return validate_development_cases(
            value, selected_manifest, args.source_corpus, args.source_plan
        )

    case_validator(bundle, manifest)
    if not args.execute:
        print(json.dumps({
            "status": "dry_run_valid",
            "run_digest": manifest["release_digest"],
            "run_spec": spec,
            "keys_accessed": False,
        }, sort_keys=True))
        return 0
    if args.expected_run_digest != manifest["release_digest"]:
        raise SystemExit("Run does not match explicitly approved digest")
    if args.ledger is None:
        raise SystemExit("Explicit durable ledger path required")
    key = os.environ.get("ASTER_LLAMA_API_KEY")
    if not key:
        raise SystemExit("Existing local service authentication required")
    headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
    opener = build_local_opener()

    def get(path):
        request = urllib.request.Request(BASE + path, headers=headers)
        with opener.open(request, timeout=10) as response:
            return read_bounded(response)

    def ready():
        health = decode_unique_json(get("/health"))
        return health.get("status") == "ok" and parse_processing_metric(get("/metrics")) == 0

    def transport(payload, timeout):
        started = time.monotonic()
        request = urllib.request.Request(
            BASE + "/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload).encode(),
        )
        with opener.open(request, timeout=timeout) as response:
            value = decode_unique_json(read_bounded(response))
        result = sanitize_response(value, time.monotonic() - started)
        print(json.dumps({
            "event": "request_complete",
            "seconds": result["latency_seconds"],
            "finish_reason": result["finish_reason"],
        }), flush=True)
        return result

    def bounded_engine(case, mode, model, selected_transport):
        return investigate(
            case,
            mode,
            model,
            selected_transport,
            request_timeout_seconds=REQUEST_TIMEOUT_SECONDS,
            total_timeout_seconds=SESSION_TIMEOUT_SECONDS,
        )

    result = run_package(
        bundle,
        manifest,
        args.ledger,
        transport,
        ready,
        model=MODEL,
        engine=bounded_engine,
        case_validator=case_validator,
        planner=lambda cases: [(case, "nonthinking") for case in cases],
    )
    result["postcheck_idle_healthy"] = ready()
    print(json.dumps(result), flush=True)
    return 0 if result["status"] == "complete" and result["postcheck_idle_healthy"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
