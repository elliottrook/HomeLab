#!/usr/bin/env python3
"""Materialize the non-deploying Bedroom content-only bridge candidate.

The Aster gateway and Home Assistant component are shared services.  This
candidate therefore lives outside every appliance composition until its
external-service deployment gate is accepted.  In particular, it must not
change Family's frozen materializer or desired composition merely because
Bedroom needs an identity with no equipment-control actions.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[3]
GATEWAY_SOURCE = CHECKOUT / "services/aster-agent/aster_remote.py"
CONTRACT_SOURCE = (
    CHECKOUT
    / "services/home-assistant/aster_room_bridge/custom_components/aster_room_bridge/contract.py"
)

SOURCE_SHA256 = {
    "gateway": "3ad1f24ff56aee121dbd26e997f93af618e6c8f085417f95a22fdc414c0d222d",
    "contract": "ea42ebedcb59703b93d592b40da90d7796b65ab213a10f7caf671b61f131434f",
}
OUTPUT_SHA256 = {
    "gateway": "66f85ee3e439276c25a5768ffe77cf2f252cdb394faaadab411f4100f632cd4c",
    "contract": "2c927737a82312c4fa9707d980a9c2bb3b92ff974d8cbce929c52249d87be82a",
}
DESTINATIONS = {
    "gateway": "/opt/aster-agent/aster_remote.py",
    "contract": "/config/custom_components/aster_room_bridge/contract.py",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def transform() -> dict[str, bytes]:
    gateway = GATEWAY_SOURCE.read_bytes()
    contract = CONTRACT_SOURCE.read_bytes()
    if sha(gateway) != SOURCE_SHA256["gateway"]:
        raise RuntimeError("bedroom-gateway-source-drift")
    if sha(contract) != SOURCE_SHA256["contract"]:
        raise RuntimeError("bedroom-contract-source-drift")

    gateway_text = gateway.decode()
    gateway_anchor = '                or not row["actions"]\n'
    if gateway_text.count(gateway_anchor) != 1:
        raise RuntimeError("bedroom-gateway-transform-anchor")
    gateway_output = gateway_text.replace(gateway_anchor, "", 1).encode()

    contract_text = contract.decode()
    contract_anchor = "        if not self.actions or not self.actions <= EQUIPMENT_ACTIONS:\n"
    if contract_text.count(contract_anchor) != 1:
        raise RuntimeError("bedroom-contract-transform-anchor")
    contract_output = contract_text.replace(
        contract_anchor,
        "        if not self.actions <= EQUIPMENT_ACTIONS:\n",
        1,
    ).encode()

    outputs = {"gateway": gateway_output, "contract": contract_output}
    for name, data in outputs.items():
        if sha(data) != OUTPUT_SHA256[name]:
            raise RuntimeError(f"bedroom-{name}-output-drift")
        ast.parse(data.decode())
    return outputs


def manifest(outputs: dict[str, bytes]) -> dict:
    return {
        "schema_version": 1,
        "kind": "astertv-external-service-candidate",
        "id": "bedroom-content-only-bridge",
        "deployment_authorized": False,
        "room_id": "bedroom",
        "equipment_actions": [],
        "files": [
            {
                "authority": "aster-agent" if name == "gateway" else "home-assistant",
                "destination": DESTINATIONS[name],
                "source_sha256": SOURCE_SHA256[name],
                "sha256": sha(outputs[name]),
                "bytes": len(outputs[name]),
                "mode": "0644",
            }
            for name in ("gateway", "contract")
        ],
        "excluded": [
            "credentials",
            "home-assistant-configuration",
            "equipment-control-authority",
            "family-composition",
            "bedroom-live-state",
        ],
    }


def write(output: Path, outputs: dict[str, bytes], receipt: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for name, data in outputs.items():
        target = output / ("aster_remote.py" if name == "gateway" else "contract.py")
        descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}-", dir=output)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o644)
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    (output / "manifest.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    outputs = transform()
    receipt = manifest(outputs)
    write(args.output, outputs, receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
