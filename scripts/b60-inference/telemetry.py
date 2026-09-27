#!/usr/bin/env python3
"""Parse and compare sanitized B60 telemetry snapshots."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


INTEGER_KEYS = {
    "source_pid", "gpu_temp_pkg_millic", "gpu_temp_vram_millic",
    "vram_resident_kib", "gtt_resident_kib", "ram_total_kib",
    "ram_available_kib",
}
OPTIONAL_NUMBER_KEYS = {"gpu_frequency_mhz", "gpu_power_w"}
TEXT_KEYS = {"schema_version", "recorded_at", "cpu_affinity", "gpu_driver"}
ALLOWED_KEYS = INTEGER_KEYS | OPTIONAL_NUMBER_KEYS | TEXT_KEYS
SECRET_PATTERN = re.compile(r"(?i)(bearer\s+|api[_-]?key|password|passwd|secret|token=|ghp_|github_pat_)")


class TelemetryError(ValueError):
    pass


def parse_snapshot(text: str) -> dict[str, Any]:
    if SECRET_PATTERN.search(text):
        raise TelemetryError("snapshot contains credential-like text")
    raw: dict[str, str] = {}
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        if "=" not in line:
            raise TelemetryError(f"line {number}: expected key=value")
        key, value = line.split("=", 1)
        if key not in ALLOWED_KEYS:
            raise TelemetryError(f"line {number}: unsupported key {key!r}")
        if key in raw:
            raise TelemetryError(f"line {number}: duplicate key {key!r}")
        raw[key] = value.strip()
    required = INTEGER_KEYS | {"schema_version", "recorded_at", "cpu_affinity", "gpu_driver"}
    missing = sorted(required - set(raw))
    if missing:
        raise TelemetryError(f"missing keys: {missing!r}")
    if raw["schema_version"] != "1.0.0" or raw["gpu_driver"] != "xe":
        raise TelemetryError("unexpected schema version or GPU driver")
    parsed: dict[str, Any] = {}
    for key, value in raw.items():
        if key in INTEGER_KEYS:
            try:
                parsed[key] = int(value)
            except ValueError as exc:
                raise TelemetryError(f"{key}: expected integer") from exc
            if parsed[key] < 0:
                raise TelemetryError(f"{key}: expected non-negative integer")
        elif key in OPTIONAL_NUMBER_KEYS:
            if value == "unavailable":
                parsed[key] = None
            else:
                try:
                    parsed[key] = float(value)
                except ValueError as exc:
                    raise TelemetryError(f"{key}: expected number or unavailable") from exc
                if parsed[key] < 0:
                    raise TelemetryError(f"{key}: expected non-negative number")
        else:
            parsed[key] = value
    if parsed["ram_available_kib"] > parsed["ram_total_kib"]:
        raise TelemetryError("available RAM exceeds total RAM")
    if not re.fullmatch(r"[0-9,-]+", parsed["cpu_affinity"]):
        raise TelemetryError("invalid CPU affinity")
    return parsed


def measurement(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "gpu_frequency_mhz": snapshot.get("gpu_frequency_mhz"),
        "gpu_temperature_c": max(snapshot["gpu_temp_pkg_millic"], snapshot["gpu_temp_vram_millic"]) / 1000,
        "gpu_power_w": snapshot.get("gpu_power_w"),
        "vram_used_bytes": snapshot["vram_resident_kib"] * 1024,
        "ram_used_bytes": (snapshot["ram_total_kib"] - snapshot["ram_available_kib"]) * 1024,
        "gpu_resident": snapshot["vram_resident_kib"] > 0,
        "cpu_fallback_detected": None,
        "cpu_affinity": snapshot["cpu_affinity"],
        "gtt_resident_bytes": snapshot["gtt_resident_kib"] * 1024,
    }


def classify_cpu_fallback(startup_excerpt: str, snapshot: dict[str, Any]) -> Any:
    """Return True/False only with affirmative evidence; otherwise None."""
    lowered = startup_excerpt.lower()
    if any(marker in lowered for marker in ("cpu backend only", "falling back to cpu", "offloaded 0/")):
        return True
    match = re.search(r"offload(?:ed|ing)\s+(\d+)\s*/\s*(\d+).*layer", lowered)
    full_offload = bool(match and int(match.group(1)) == int(match.group(2)) and int(match.group(2)) > 0)
    vulkan = "vulkan" in lowered and ("bmg g21" in lowered or "intel" in lowered)
    resident = snapshot.get("vram_resident_kib", 0) > 1024 * 1024
    if full_offload and vulkan and resident:
        return False
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(measurement(parse_snapshot(args.snapshot.read_text(encoding="utf-8"))),
                         indent=2, sort_keys=True))
    except (OSError, TelemetryError) as exc:
        print(f"invalid telemetry: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
