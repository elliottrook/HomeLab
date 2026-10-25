"""One-call, content-free diagnostic for the reviewed D4 development contract."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request

from sa3_development_execute import (
    MODEL,
    RUNTIME,
    file_sha256,
    validate_development_cases,
)
from sa3_fresh_execute import (
    BASE,
    build_local_opener,
    decode_unique_json,
    load_bounded_json,
    parse_processing_metric,
    read_bounded,
)
from sa3_fresh_package import digest
from sa3_investigation import answer_shape_status, request_for
from sa3_investigation_runner import sanitize_response
from validate_sa3_fixture_bundle import review_source_sha256


REQUEST_TIMEOUT_SECONDS = 60


def probe_spec(fixtures, source_corpus, source_plan):
    here = Path(__file__).parent
    implementation = {
        name: file_sha256(here / name)
        for name in (
            "sa3_development_probe.py",
            "sa3_development_execute.py",
            "sa3_fair_request.py",
            "sa3_fresh_execute.py",
            "sa3_fresh_package.py",
            "sa3_investigation.py",
            "sa3_investigation_runner.py",
            "validate_sa3_fixture_bundle.py",
            "validate_sa3_holdout_release.py",
        )
    }
    return {
        "schema": "aster-sa3-development-contract-probe.v1",
        "fixture_file_sha256": file_sha256(fixtures),
        "fixture_review_sha256": review_source_sha256(load_bounded_json(fixtures)),
        "source_corpus_sha256": file_sha256(source_corpus),
        "source_plan_sha256": file_sha256(source_plan),
        "implementation_sha256": implementation,
        "endpoint": BASE,
        "model": MODEL,
        "runtime": RUNTIME,
        "mode": "nonthinking",
        "cases": 1,
        "maximum_model_calls": 1,
        "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        "connected_tools": False,
        "effects": False,
        "retains_model_text": False,
        "approval_required": True,
    }


def semantic_status(case, answer):
    shape = answer_shape_status(answer)
    if shape != "valid":
        return "invalid_answer:" + shape
    if answer["effects"] != []:
        return "effect_claim_rejected"
    observed = {item["id"] for item in case["initial_observations"]}
    if not set(answer["evidence_ids"]) <= observed:
        return "unobserved_evidence_rejected"
    if answer["decision"] == "check":
        available = {item["id"] for item in case["capabilities"]}
        return "accepted_first_check" if answer["check"] in available else "check_rejected"
    if answer["check"]:
        return "invalid_terminal_check"
    return "accepted_first_" + answer["decision"]


def write_result(path, value):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, separators=(",", ":"), allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def main(argv=None):
    here = Path(__file__).parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, default=here / "sysadmin-sa3-development-fixtures-draft-v1.json")
    parser.add_argument("--source-corpus", type=Path, default=here / "sysadmin-incident-development-extension-draft-v1.json")
    parser.add_argument("--source-plan", type=Path, default=here / "sysadmin-incident-development-plan-v1.json")
    parser.add_argument("--expected-probe-digest")
    parser.add_argument("--result", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)

    bundle = load_bounded_json(args.fixtures)
    spec = probe_spec(args.fixtures, args.source_corpus, args.source_plan)
    probe_digest = digest(spec)
    validation_manifest = {
        "run_spec": {
            "fixture_file_sha256": spec["fixture_file_sha256"],
        },
        "release_digest": "",
    }
    validation_manifest["release_digest"] = digest(validation_manifest["run_spec"])
    cases = validate_development_cases(
        bundle, validation_manifest, args.source_corpus, args.source_plan
    )
    if not args.execute:
        print(json.dumps({
            "status": "dry_run_valid",
            "probe_digest": probe_digest,
            "probe_spec": spec,
            "keys_accessed": False,
        }, sort_keys=True))
        return 0
    if args.expected_probe_digest != probe_digest:
        raise SystemExit("Probe does not match explicitly approved digest")
    if args.result is None:
        raise SystemExit("Explicit durable result path required")
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

    if not ready():
        raise SystemExit("Local service is not confirmed idle and healthy")
    case = cases[0]
    payload = request_for(case, case["initial_observations"], [], "nonthinking", MODEL)
    started = time.monotonic()
    request = urllib.request.Request(
        BASE + "/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload).encode(),
    )
    with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        transport = sanitize_response(
            decode_unique_json(read_bounded(response)), time.monotonic() - started
        )
    result = {
        "schema": "aster-sa3-development-contract-probe-result.v1",
        "probe_digest": probe_digest,
        "status": semantic_status(case, transport.get("answer")),
        "answer_parse_status": transport["answer_parse_status"],
        "answer_shape_status": answer_shape_status(transport.get("answer")),
        "finish_reason": transport.get("finish_reason"),
        "latency_seconds": transport.get("latency_seconds"),
        "reasoning_present": transport.get("reasoning_present"),
        "reasoning_characters": transport.get("reasoning_characters"),
        "completion_tokens": transport.get("completion_tokens"),
        "tool_call_count": transport.get("tool_call_count"),
        "postcheck_idle_healthy": ready(),
        "model_text_retained": False,
    }
    write_result(args.result, result)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if result["postcheck_idle_healthy"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
