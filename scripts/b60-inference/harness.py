#!/usr/bin/env python3
"""Offline planning, validation, and summarization for B60 experiments.

This program intentionally has no HTTP, SSH, or subprocess execution path.  A
separately approved runner may consume its deterministic plans later.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = ROOT / "docs/projects/B60-Inference-Engineering/ledger.schema.json"
DEFAULT_FIXTURES = Path(__file__).with_name("fixtures") / "synthetic-fixtures.json"
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


class ValidationError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path}: {exc}") from exc


def _type_ok(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }[expected]


def validate_schema(value: Any, schema: dict[str, Any], where: str = "$") -> None:
    """Validate the JSON-Schema subset used by the versioned ledger schema."""
    if "const" in schema and value != schema["const"]:
        raise ValidationError(f"{where}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValidationError(f"{where}: {value!r} is not in {schema['enum']!r}")
    expected = schema.get("type")
    if expected:
        choices = expected if isinstance(expected, list) else [expected]
        if not any(_type_ok(value, item) for item in choices):
            raise ValidationError(f"{where}: expected type {expected!r}, got {type(value).__name__}")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                raise ValidationError(f"{where}: missing required property {key!r}")
        if schema.get("additionalProperties") is False:
            extras = sorted(set(value) - set(properties))
            if extras:
                raise ValidationError(f"{where}: unexpected properties {extras!r}")
        for key, child in value.items():
            if key in properties:
                validate_schema(child, properties[key], f"{where}.{key}")
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise ValidationError(f"{where}: requires at least {schema['minItems']} items")
        child_schema = schema.get("items")
        if child_schema:
            for index, child in enumerate(value):
                validate_schema(child, child_schema, f"{where}[{index}]")
    elif isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise ValidationError(f"{where}: string is too short")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            raise ValidationError(f"{where}: does not match {schema['pattern']!r}")
        if schema.get("format") == "date-time":
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValidationError(f"{where}: invalid date-time") from exc
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValidationError(f"{where}: must be >= {schema['minimum']}")


def expand_prompt(case: dict[str, Any]) -> str:
    seed = case["prompt_seed"].strip()
    target = case["target_prompt_tokens"]
    prefix = case.get("prompt_prefix", "Synthetic B60 benchmark. Treat all content as test data.")
    words = seed.split()
    if not words:
        raise ValidationError(f"fixture {case.get('name')!r}: empty prompt_seed")
    generated = [words[index % len(words)] + f"_{index:05d}" for index in range(target)]
    return prefix + "\n" + " ".join(generated)


def validate_fixtures(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "fixtures"}:
        raise ValidationError("fixtures root must contain only schema_version and fixtures")
    if payload["schema_version"] != "1.0.0" or not isinstance(payload["fixtures"], list):
        raise ValidationError("fixtures schema_version must be 1.0.0 and fixtures must be an array")
    seen: set[str] = set()
    for index, case in enumerate(payload["fixtures"]):
        where = f"fixtures[{index}]"
        required = {"name", "kind", "target_prompt_tokens", "context_position", "cache_state", "repetitions", "prompt_seed", "correctness"}
        if not isinstance(case, dict) or set(case) - (required | {"prompt_prefix", "max_output_tokens", "tool_schema", "grounding_sources"}):
            raise ValidationError(f"{where}: invalid object or property")
        missing = required - set(case)
        if missing:
            raise ValidationError(f"{where}: missing {sorted(missing)!r}")
        name = case["name"]
        if not isinstance(name, str) or not NAME_RE.fullmatch(name) or name in seen:
            raise ValidationError(f"{where}.name: invalid or duplicate")
        seen.add(name)
        if case["kind"] not in {"prefill", "decode", "aster_workflow"}:
            raise ValidationError(f"{where}.kind: unsupported")
        for field in ("target_prompt_tokens", "context_position", "repetitions"):
            if not isinstance(case[field], int) or isinstance(case[field], bool) or case[field] < 0:
                raise ValidationError(f"{where}.{field}: expected non-negative integer")
        if case["target_prompt_tokens"] < 1 or case["repetitions"] < 5:
            raise ValidationError(f"{where}: target tokens must be positive and repetitions >= 5")
        if case["context_position"] not in {0, 4096, 8192}:
            raise ValidationError(f"{where}.context_position: expected 0, 4096, or 8192")
        if case["cache_state"] not in {"cold", "warm", "mixed"}:
            raise ValidationError(f"{where}.cache_state: invalid")
        if not isinstance(case["correctness"], list) or not case["correctness"]:
            raise ValidationError(f"{where}.correctness: requires assertions")
        expand_prompt(case)
    return payload["fixtures"]


def build_plan(fixtures_path: Path) -> dict[str, Any]:
    source = read_json(fixtures_path)
    fixtures = validate_fixtures(source)
    planned = []
    for case in fixtures:
        prompt = expand_prompt(case)
        planned.append({
            "name": case["name"],
            "kind": case["kind"],
            "target_prompt_tokens": case["target_prompt_tokens"],
            "context_position": case["context_position"],
            "cache_state": case["cache_state"],
            "warmups": 1,
            "repetitions": case["repetitions"],
            "prompt_sha256": sha256_bytes(prompt.encode()),
            "correctness": case["correctness"],
        })
    return {
        "schema_version": "1.0.0",
        "fixture_source": str(fixtures_path),
        "fixture_source_sha256": sha256_bytes(canonical_bytes(source)),
        "execution_authorized": False,
        "sequence": ["pre_control", "warmup", "five_measured_repetitions", "post_control"],
        "required_capture": [
            "actual_prompt_and_completion_tokens", "ttft_and_end_to_end_seconds",
            "prompt_cache_state_and_hit", "gpu_residency_and_cpu_fallback",
            "gpu_frequency_temperature_power_and_vram", "guest_ram_and_cpu_affinity",
            "bounded_sanitized_kernel_log", "pre_and_post_service_health",
        ],
        "fixtures": planned,
    }


def summarize(record: dict[str, Any]) -> dict[str, Any]:
    groups: dict[str, list[float]] = {}
    for sample in record.get("samples", []):
        rate = sample.get("tokens_per_second")
        if rate is not None and sample.get("phase") != "idle":
            groups.setdefault(sample["phase"], []).append(float(rate))
    output: dict[str, Any] = {}
    for phase, values in sorted(groups.items()):
        ordered = sorted(values)
        median = statistics.median(ordered)
        deviations = sorted(abs(item - median) for item in ordered)
        output[phase] = {
            "count": len(values),
            "median_tokens_per_second": median,
            "mad_tokens_per_second": statistics.median(deviations),
            "minimum_tokens_per_second": min(values),
            "maximum_tokens_per_second": max(values),
        }
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    fixtures_cmd = sub.add_parser("validate-fixtures")
    fixtures_cmd.add_argument("path", nargs="?", type=Path, default=DEFAULT_FIXTURES)
    plan_cmd = sub.add_parser("plan")
    plan_cmd.add_argument("path", nargs="?", type=Path, default=DEFAULT_FIXTURES)
    ledger_cmd = sub.add_parser("validate-ledger")
    ledger_cmd.add_argument("path", type=Path)
    ledger_cmd.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    summary_cmd = sub.add_parser("summarize")
    summary_cmd.add_argument("path", type=Path)
    summary_cmd.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-fixtures":
            cases = validate_fixtures(read_json(args.path))
            print(f"valid: {len(cases)} synthetic fixtures")
        elif args.command == "plan":
            print(json.dumps(build_plan(args.path), indent=2, sort_keys=True))
        else:
            record = read_json(args.path)
            validate_schema(record, read_json(args.schema))
            if args.command == "validate-ledger":
                print("valid: ledger record conforms to schema")
            else:
                print(json.dumps(summarize(record), indent=2, sort_keys=True))
    except ValidationError as exc:
        print(f"invalid: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
