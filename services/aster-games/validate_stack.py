#!/usr/bin/env python3
"""Static, dependency-free validation for the inactive infrastructure candidate."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPOSITORY = ROOT.parents[1]


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    failures: list[str] = []
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    gate = json.loads((ROOT / "config/release-gate.json").read_text(encoding="utf-8"))
    policy = json.loads((ROOT / "config/policy.json").read_text(encoding="utf-8"))

    image_lines = re.findall(r"^\s+image:\s*(\S+)", compose, flags=re.MULTILINE)
    require(len(image_lines) == 5, "compose must declare exactly five images", failures)
    for image in image_lines:
        if image.startswith("localhost/"):
            require(re.search(r":\d+\.\d+\.\d+$", image) is not None,
                    f"local image is not semver pinned: {image}", failures)
        else:
            require("@sha256:" in image, f"upstream image is not digest pinned: {image}", failures)
        require(":latest" not in image, f"latest tag is forbidden: {image}", failures)

    published = re.findall(r'^\s+- "([^\"]+:[^\"]+)"$', compose, flags=re.MULTILINE)
    require(bool(published), "compose must declare loopback diagnostics ports", failures)
    for binding in published:
        require(
            binding.startswith("${ASTER_GAMES_UI_BIND_ADDRESS:-127.0.0.1}:")
            or binding.startswith("${ASTER_GAMES_BROKER_BIND_ADDRESS:-127.0.0.1}:"),
            f"port binding does not fail closed to loopback: {binding}", failures
        )

    require(compose.count("internal: true") == 2,
            "state and frontend networks must be internal", failures)
    require("egress:\n    driver: bridge" in compose,
            "explicit outbound dependency network is missing", failures)
    require("DEVICE_INSTALL_ENABLED: \"false\"" in compose,
            "RomM remote installation must start disabled", failures)
    require(":/romm/library/roms:ro" in compose,
            "RomM canonical library mount must be read-only", failures)
    require("read_only: true" in compose and "cap_drop: [ALL]" in compose,
            "broker container hardening is incomplete", failures)
    require("B60" not in compose and "b60" not in compose,
            "candidate must not depend on the B60 stack", failures)

    require(gate.get("astertv_v3_deployed") is False, "repository v3 gate must remain closed", failures)
    require(gate.get("astertv_v3_owner_accepted") is False, "owner-acceptance gate must remain closed", failures)
    require(gate.get("v4_client_work_allowed") is False, "v4 client work gate must remain closed", failures)
    require(not gate.get("evidence_refs"), "closed gate must not cite acceptance evidence", failures)
    require(policy.get("execution_enabled") is False, "proposal execution must remain disabled", failures)
    require(policy.get("public_ingress_allowed") is False, "public ingress must remain forbidden", failures)
    require(policy.get("b60_dependency_allowed") is False, "B60 dependency must remain forbidden", failures)

    forbidden = [
        REPOSITORY / "services/kodi/astertv-v4",
        REPOSITORY / "services/kodi/astertv-fleet/overlays/retro-gaming.yaml",
    ]
    for path in forbidden:
        require(not path.exists(), f"premature AsterTV v4 implementation exists: {path}", failures)

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: Aster Games infrastructure candidate is pinned, private, execution-disabled, and v3-gated")
    return 0


if __name__ == "__main__":
    sys.exit(main())

