#!/usr/bin/env python3
"""Assemble one immutable, schema-validated B60 experiment record."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

import harness
import kernel_log
import runner
import telemetry


METADATA_FIELDS = {
    "experiment_id", "recorded_at", "hypothesis", "prediction", "change",
    "rollback", "success_thresholds", "role_owner", "decision",
}


def assemble(metadata: dict[str, Any], environment: dict[str, Any], raw: dict[str, Any],
             raw_path: Path, telemetry_text: str, kernel_text: str,
             startup_excerpt: str) -> dict[str, Any]:
    missing = sorted(METADATA_FIELDS - set(metadata))
    extras = sorted(set(metadata) - METADATA_FIELDS)
    if missing or extras:
        raise harness.ValidationError(f"metadata missing={missing!r} extra={extras!r}")
    case = runner.selected_fixture(harness.DEFAULT_FIXTURES, raw.get("fixture", ""))
    expected_prompt = harness.sha256_bytes(harness.expand_prompt(case).encode())
    if raw.get("schema_version") != "1.0.0" or raw.get("prompt_sha256") != expected_prompt:
        raise harness.ValidationError("raw result does not match the versioned fixture prompt")
    samples = raw.get("samples")
    if not isinstance(samples, list) or not samples:
        raise harness.ValidationError("raw result has no samples")

    snapshot = telemetry.parse_snapshot(telemetry_text)
    observed = telemetry.measurement(snapshot)
    observed["cpu_fallback_detected"] = telemetry.classify_cpu_fallback(startup_excerpt, snapshot)
    sanitized_kernel = kernel_log.sanitize(kernel_text)
    findings = kernel_log.classify(sanitized_kernel)
    enriched = []
    for sample in samples:
        merged = dict(sample)
        for key in ("gpu_frequency_mhz", "gpu_temperature_c", "gpu_power_w",
                    "vram_used_bytes", "ram_used_bytes", "gpu_resident",
                    "cpu_fallback_detected", "gtt_resident_bytes", "cpu_affinity"):
            merged[key] = observed[key]
        enriched.append(merged)

    measured_decode = [float(item["tokens_per_second"]) for item in enriched
                       if item.get("control_role") == "measured"
                       and item.get("phase") == "decode"
                       and item.get("tokens_per_second") is not None]
    if len(measured_decode) < case["repetitions"]:
        raise harness.ValidationError("raw result lacks the required measured decode samples")
    median = statistics.median(measured_decode)
    mad = statistics.median(abs(value - median) for value in measured_decode)
    correctness = all(item.get("correct") is True for item in enriched
                      if item.get("control_role") == "measured")
    health = raw.get("health_passed") is True
    fallback_clear = observed["cpu_fallback_detected"] is False
    passed = correctness and health and fallback_clear and not findings

    record = {
        "schema_version": "1.0.0",
        "experiment_id": metadata["experiment_id"],
        "recorded_at": metadata["recorded_at"],
        "status": "passed" if passed else "failed",
        "role_owner": metadata["role_owner"],
        "auditor": None,
        "hypothesis": metadata["hypothesis"],
        "prediction": metadata["prediction"],
        "change": metadata["change"],
        "rollback": metadata["rollback"],
        "success_thresholds": metadata["success_thresholds"],
        "environment": environment,
        "fixture": {
            "name": case["name"], "prompt_sha256": expected_prompt,
            "context_position": case["context_position"],
            "cache_state": case["cache_state"], "repetitions": case["repetitions"],
            "correctness_assertions": case["correctness"],
        },
        "samples": enriched,
        "summary": {
            "median_tokens_per_second": median, "spread_method": "MAD",
            "spread": mad, "effect_percent": 0.0,
            "correctness_passed": correctness, "health_passed": health,
            "rollback_passed": False,
        },
        "raw_evidence": {
            "path": str(raw_path), "sha256": harness.sha256_bytes(raw_path.read_bytes()),
            "sanitized": True,
        },
        "errors": findings + ([] if fallback_clear else ["cpu_fallback_not_disproved"]),
        "decision": metadata["decision"],
    }
    harness.validate_schema(record, harness.read_json(harness.DEFAULT_SCHEMA))
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--environment", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--telemetry", type=Path, required=True)
    parser.add_argument("--kernel-log", type=Path, required=True)
    parser.add_argument("--startup-excerpt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        raw = harness.read_json(args.raw)
        record = assemble(
            harness.read_json(args.metadata), harness.read_json(args.environment), raw,
            args.raw, args.telemetry.read_text(encoding="utf-8"),
            args.kernel_log.read_text(encoding="utf-8"),
            args.startup_excerpt.read_text(encoding="utf-8"),
        )
        digest = runner.write_immutable(args.output, record)
        print(json.dumps({"output": str(args.output), "sha256": digest}, sort_keys=True))
    except (OSError, harness.ValidationError, telemetry.TelemetryError,
            kernel_log.KernelLogError) as exc:
        print(f"invalid record: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
