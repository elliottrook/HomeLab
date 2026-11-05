#!/usr/bin/env python3
"""Create a deterministic, mutation-free AsterTV onboarding plan."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
FLEET_ROOT = HERE.parent
SPEC = importlib.util.spec_from_file_location("astertv_compile_fleet_onboarding", FLEET_ROOT / "compile_fleet.py")
FLEET = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(FLEET)

SECRET_KEYS = {"password", "token", "secret", "api_key", "private_key", "credential"}
SAFE_REF = re.compile(r"^[a-z0-9][a-z0-9:._/-]+$")


def reject_values(value, location="request"):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in SECRET_KEYS or key.lower().endswith("_value"):
                raise ValueError(f"secret-bearing-key:{location}.{key}")
            if key.lower() in {"command", "script", "shell"}:
                raise ValueError(f"arbitrary-execution-key:{location}.{key}")
            reject_values(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_values(child, f"{location}[{index}]")


def load_devices(root: Path) -> dict[str, dict]:
    return {value["id"]: value for value in (json.loads(path.read_text()) for path in sorted((root / "devices").glob("*.yaml")))}


def validate_flow(flow: dict) -> None:
    required = {"purpose", "destination_ref", "protocol", "port"}
    if set(flow) != required:
        raise ValueError("network-flow-fields")
    if flow["protocol"] not in {"tcp", "udp"}:
        raise ValueError("network-flow-protocol")
    if not isinstance(flow["port"], int) or not 1 <= flow["port"] <= 65535:
        raise ValueError("network-flow-port")
    if not SAFE_REF.fullmatch(flow["destination_ref"]):
        raise ValueError("network-flow-destination-ref")


def plan(request: dict, root: Path = FLEET_ROOT) -> dict:
    reject_values(request)
    if request.get("schema_version") != 1 or request.get("kind") != "astertv-onboarding-request":
        raise ValueError("onboarding-request-schema")
    devices = load_devices(root)
    device = devices.get(request.get("device_id"))
    if device is None:
        raise ValueError("unknown-fleet-device")
    if device.get("lifecycle") != "candidate" or device.get("deployed"):
        raise ValueError("onboarding-target-not-candidate")
    network = request.get("network", {})
    for field in ("vlan_ref", "address_ref"):
        if not isinstance(network.get(field), str) or not SAFE_REF.fullmatch(network[field]) or not network[field].startswith("netbox:"):
            raise ValueError(f"network-authority-ref:{field}")
    flows = network.get("required_flows", [])
    if not flows:
        raise ValueError("network-flows-empty")
    for flow in flows:
        validate_flow(flow)
    ha = request.get("home_assistant", {})
    capabilities = ha.get("capabilities", [])
    controls = ha.get("control_allowlist", [])
    if not isinstance(capabilities, list) or not isinstance(controls, list):
        raise ValueError("home-assistant-capabilities")
    if any(control not in capabilities for control in controls):
        raise ValueError("home-assistant-control-not-capability")
    blockers = []
    measured = request.get("hardware", {}).get("measured_capabilities", [])
    if any(str(value).startswith("pending-") for value in measured):
        blockers.append("hardware-capability-measurement")
    if "pending" in network["address_ref"] or "pending" in network["vlan_ref"]:
        blockers.append("netbox-address-or-vlan-allocation")
    placement = request.get("placement", {})
    if any("pending" in str(placement.get(field, "")) for field in ("display_chain_ref", "power_ref")):
        blockers.append("physical-chain-registration")
    return {
        "schema_version": 1,
        "kind": "astertv-onboarding-plan",
        "device_id": device["id"],
        "source_lifecycle": device["lifecycle"],
        "mutation_authorized": False,
        "ready_for_effects": False,
        "blockers": sorted(blockers),
        "netbox_plan": {
            "device": device["hostname"],
            "room": placement.get("room"),
            "serial_ref": request["hardware"]["serial_ref"],
            "mac_ref": request["hardware"]["mac_ref"],
            "vlan_ref": network["vlan_ref"],
            "address_ref": network["address_ref"],
            "display_chain_ref": placement.get("display_chain_ref"),
            "power_ref": placement.get("power_ref"),
        },
        "network_plan": {"default": "deny", "flows": sorted(flows, key=lambda row: (row["destination_ref"], row["protocol"], row["port"]))},
        "home_assistant_plan": {
            "room_ref": ha.get("room_ref"),
            "exposed_capabilities": sorted(capabilities),
            "control_allowlist": sorted(controls),
            "default_control": "deny",
        },
        "acceptance": request.get("acceptance", []),
        "recovery": ["retain-old-path", "checkpoint-before-effects", "prove-local-console", "prove-rollback-without-wiki"],
        "operator_sequence": ["resolve-blockers", "review-generated-diff", "obtain-effect-authorization", "apply-one-authority-at-a-time", "run-allow-deny-tests", "capture-evidence", "promote-lifecycle-separately"],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("request", type=Path)
    parser.add_argument("--root", type=Path, default=FLEET_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = plan(json.loads(args.request.read_text()), args.root)
    data = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(data)
    else:
        print(data, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
