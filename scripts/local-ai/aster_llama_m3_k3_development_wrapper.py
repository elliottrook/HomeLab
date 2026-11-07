#!/usr/bin/env python3
"""Fixed LXC110 K3 development wrapper."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error

import aster_llama_m3_k2_development_wrapper as base


PROFILE = "m3-k3-hierarchical-safety-development-v1"
PORT = 11436
CASES = 192
MODEL_REQUESTS = 384
PER_REQUEST_TIMEOUT = 45
DEADLINE = 1800
RUNTIME_ROOT = base.RUNTIME_ROOT
PINS = {
    "aster_llama_m3_k2_development_wrapper.py": "12f86fdf694866a08cc0dbd31341d26cb0bec352901bda0241167afe746dd531",
    "nlu_deterministic_guard_v1.py": "d7d62d19008519ae50aa9b46799ab1f277a51904f2e80e65c30517abca8a7135",
    "nlu_k2_consensus_policy_v1.py": "9027abbcc446d9c63100178e3ce9add60275a1f134bde9d7beeb30aa4a4d504e",
    "nlu_k2_development_runner_v1.py": "d5c9ef87bd49185466a12e7b53eab741d0f0dc40ce92c2977389dd2b0e5e3785",
    "nlu_k2_development_scorer_v1.py": "c43f3894ba65251b6fadbda1012bd2aead44c3357323b09f491f590ffd6e8558",
    "nlu_k2_shortlist_arbitrator_v1.py": "7c81894da9adbd1c3ee22b97d1487fcf2feadc1e4bc1e321a7c715479c517962",
    "nlu_k3_development_runner_v1.py": "940d1de888bc00709f37db09604bd7062dbd9553dbdc970e7d9c8d705378bf96",
    "nlu_k3_development_scorer_v1.py": "61dce93dc94ec76725e5d1048ab099a383a9e418245629e9631e98e834a8a353",
    "nlu_k3_hierarchical_safety_preregistration_v1.py": "47b12ca52d7880121f2005ee53a788a981d5b9009721c9bfbb15f9c34485de14",
    "nlu_k3_hierarchical_safety_veto_v1.py": "3cf4b0a531596760e6ad811c090fded4434fdd55143663c470104abdeba41bff",
    "nlu_local_model_adapter.py": "3a3b09f12bcd2088f0d604363a5bc0e69190c177eced50dc5a14eb582749aed0",
    "nlu_threshold_policy.py": "984932d8716531858972e22723fe962701077f9a15991c58384c6ee6661ebb5d",
    "nlu_whole_label_choice_v1.py": "6e7ee332ce74a44a5bb19877f9f8f0c90f814687279b3c4993fbb93fbd58948a",
    "nlu-k3-runtime-manifest-v1.json": "0a9866a10c4079879fc7d7e8298969074cc50e44b36afd3b1c56e570fe08fa45",
    "nlu-k2-development-corpus-v1.json": "9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a",
    "nlu-k2-shortlist-v1.json": "620f5b5badce1c3ee70b5718a0d05ff4ad6261308360cc5c5dad588e4b977f6e",
}
PRIVATE_FILES = frozenset({"nlu-k2-development-corpus-v1.json",
                           "nlu-k2-shortlist-v1.json"})
ERROR_CLASS_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,63}")


class GuestError(RuntimeError):
    pass


def _scope_unit(lease_id: str, generation: int) -> str:
    if (not base.LEASE_RE.fullmatch(lease_id) or type(generation) is not int
            or generation < 1):
        raise GuestError("invalid lease identity")
    token = hashlib.sha256(f"{lease_id}:{generation}".encode()).hexdigest()[:16]
    return f"aster-llama-k3-{token}.scope"


def check_pins() -> None:
    for name, expected in PINS.items():
        mode = 0o600 if name in PRIVATE_FILES else 0o644
        if not base._pinned_file(RUNTIME_ROOT / name, expected, mode):
            raise GuestError("K3 runtime pin drift:" + name)
    if (not base._pinned_model()
            or not base._pinned_file(Path(base.SERVER), base.BINARY_SHA, 0o755)):
        raise GuestError("accepted model or binary pin drift")


def validate_result(value: object) -> None:
    if (not isinstance(value, dict)
            or set(value) != {"schema", "profile", "run", "score",
                              "journal_sha256"}
            or value["schema"] != "aster-m3-k3-development-guest-result.v1"
            or value["profile"] != PROFILE
            or not isinstance(value["run"], dict)
            or value["run"].get("schema") != "aster-nlu-k3-development-run.v1"
            or value["run"].get("engine_sha256") != base.MODEL_SHA
            or value["run"].get("attempted") != MODEL_REQUESTS
            or value["run"].get("valid") != CASES
            or value["run"].get("retries") != 0
            or value["run"].get("response_errors") != 0
            or value["run"].get("complete") is not True
            or value["run"].get("authority") != "not-granted"
            or value["run"].get("automatic_routing") != "off"
            or not isinstance(value["score"], dict)
            or value["score"].get("schema") != "aster-nlu-k3-development-score.v1"
            or value["score"].get("cases") != CASES
            or value["score"].get("model_requests") != MODEL_REQUESTS
            or value["score"].get("retries") != 0
            or value["score"].get("response_errors") != 0
            or value["score"].get("sealed_evaluation_access") is not False
            or value["score"].get("authority") != "not-granted"
            or value["score"].get("automatic_routing") != "off"
            or not isinstance(value["journal_sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", value["journal_sha256"])):
        raise GuestError("K3 result identity or count invalid")


def run(*, profile: str, port: int, requests: int, per_request_timeout: int,
        deadline: int, lease_id: str, generation: int, scope_unit: str,
        process_factory=subprocess.Popen, runner=subprocess.run,
        clock=time.monotonic, production_check=base.production_is_masked) -> dict:
    if (os.geteuid() != 0 or profile != PROFILE or port != PORT
            or requests != CASES or per_request_timeout != PER_REQUEST_TIMEOUT
            or deadline != DEADLINE
            or scope_unit != _scope_unit(lease_id, generation)):
        raise GuestError("fixed K3 invocation mismatch")
    if not production_check():
        raise GuestError("production llama service is not masked and inactive")
    check_pins()
    root = Path("/run/aster-m3-k3-development")
    key_path, key = base._prepare_private_runtime(root)
    process = None
    end = clock() + DEADLINE
    try:
        process = process_factory(
            base._server_command(key_path, scope_unit), stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, start_new_session=True,
            env={**os.environ, "LD_LIBRARY_PATH": base.LD_LIBRARY_PATH,
                 "ONEAPI_DEVICE_SELECTOR": "level_zero:gpu",
                 "GGML_SYCL_ENABLE_FUSION": "1"})
        base._wait_ready(key, end, clock)
        attempt = Path("/var/lib/local-ai-lab/k3-attempts") / _scope_unit(
            lease_id, generation).removesuffix(".scope")
        attempt.mkdir(parents=True, mode=0o700, exist_ok=False)
        os.chmod(attempt, 0o700)
        output = attempt / "run.json"
        journal = attempt / "journal.jsonl"
        command = (
            "/usr/bin/python3", "-B",
            str(RUNTIME_ROOT / "nlu_k3_development_runner_v1.py"),
            "--corpus", str(RUNTIME_ROOT / "nlu-k2-development-corpus-v1.json"),
            "--shortlist", str(RUNTIME_ROOT / "nlu-k2-shortlist-v1.json"),
            "--key-file", str(key_path), "--output", str(output),
            "--journal", str(journal), "--endpoint",
            f"http://127.0.0.1:{PORT}/v1/chat/completions")
        completed = runner(
            command, capture_output=True, text=True,
            timeout=max(1, int(end - clock())), check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                 "PYTHONPATH": str(RUNTIME_ROOT)})
        if completed.returncode != 0:
            raise GuestError("K3 runner exit-status:" + str(completed.returncode))
        sys.path.insert(0, str(RUNTIME_ROOT))
        import nlu_k3_development_scorer_v1 as scorer
        run_value = json.loads(output.read_text())
        decisions = {"schema": "aster-nlu-k3-development-records.v1",
                     "records": run_value["records"],
                     "authority": "not-granted"}
        score_value = json.loads(scorer.score(
            (RUNTIME_ROOT / "nlu-k2-development-corpus-v1.json").read_bytes(),
            (json.dumps(decisions, sort_keys=True, separators=(",", ":"))
             + "\n").encode(),
            {"model_requests": run_value["attempted"],
             "retries": run_value["retries"],
             "response_errors": run_value["response_errors"]}))
        result = {"schema": "aster-m3-k3-development-guest-result.v1",
                  "profile": PROFILE, "run": run_value,
                  "score": score_value,
                  "journal_sha256": hashlib.sha256(journal.read_bytes()).hexdigest()}
        if clock() >= end:
            raise GuestError("K3 workload deadline reached")
        validate_result(result)
        return result
    finally:
        cleanup_error = None
        try:
            base._stop(scope_unit, process, runner=runner)
        except Exception as exc:
            cleanup_error = exc
        try:
            base._cleanup_private_runtime(root, key_path)
        except Exception as exc:
            cleanup_error = cleanup_error or exc
        if cleanup_error is not None:
            raise cleanup_error


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--requests", type=int, required=True)
    parser.add_argument("--per-request-timeout", type=int, required=True)
    parser.add_argument("--deadline", type=int, required=True)
    parser.add_argument("--lease-id", required=True)
    parser.add_argument("--generation", type=int, required=True)
    parser.add_argument("--scope-unit", required=True)
    try:
        print(json.dumps(run(**vars(parser.parse_args(argv))), sort_keys=True,
                         separators=(",", ":")))
        return 0
    except (GuestError, OSError, ValueError, urllib.error.URLError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)},
                         sort_keys=True), file=sys.stderr)
        return 1
    except Exception as exc:
        error_class = type(exc).__name__
        if not ERROR_CLASS_RE.fullmatch(error_class):
            error_class = "Exception"
        print(json.dumps({"state": "no_go",
                          "code": "K3 guest exception-class:" + error_class},
                         sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
