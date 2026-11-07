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
GATEWAY_SOURCE = (
    CHECKOUT
    / "services/kodi/astertv-fleet/materialized/family-equipment-bridge/external/opt/aster-agent/aster_remote.py"
)
CONTRACT_SOURCE = (
    CHECKOUT
    / "services/home-assistant/aster_room_bridge/custom_components/aster_room_bridge/contract.py"
)
REMOTE_SOURCE = CHECKOUT / "services/kodi/astertv-v3/remote_client/addon/service.asterremote"
INSTALLER_SOURCE = HERE / "install_bedroom_publisher.py"
ASTER_INSTALLER_SOURCE = HERE / "install_aster_identity.py"

SOURCE_SHA256 = {
    "gateway": "715b172a62e978ccaf79dfd3f9801da641cd067da72ad7187658efa9ccc0d73a",
    "contract": "ea42ebedcb59703b93d592b40da90d7796b65ab213a10f7caf671b61f131434f",
    "remote_service": "b443edc794f86fc66b1c92d46a048ed18871d9aa325835a2cb8b486d265415c3",
    "content_session": "a85f477bc877f835d18a7027c7532fcbacdd3ff932912a976bdb5a0b5cfd8acb",
    "publisher_installer": "c3980a7256d7109a14d5d7149b3925e991464b584708853af7a779e50dc83455",
    "aster_installer": "2f4bc465b8b589743152cc3609f38a4b464dfac340093efd8972a109eb888ce8",
}
OUTPUT_SHA256 = {
    "gateway": "a804c06732b291275de830dcb0f8188ade5fc4fc3d0a557a86a742d1557cf1b3",
    "contract": "2c927737a82312c4fa9707d980a9c2bb3b92ff974d8cbce929c52249d87be82a",
    "remote_service": SOURCE_SHA256["remote_service"],
    "content_session": SOURCE_SHA256["content_session"],
    "publisher_installer": SOURCE_SHA256["publisher_installer"],
    "aster_installer": SOURCE_SHA256["aster_installer"],
}
DESTINATIONS = {
    "gateway": "/opt/aster-agent/aster_remote.py",
    "contract": "/config/custom_components/aster_room_bridge/contract.py",
    "remote_service": "/storage/.kodi/addons/service.asterremote/service.py",
    "content_session": "/storage/.kodi/addons/service.asterremote/content_session.py",
    "publisher_installer": "transient:/tmp/install_bedroom_publisher.py",
    "aster_installer": "transient:/tmp/install_aster_identity.py",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def transform() -> dict[str, bytes]:
    gateway = GATEWAY_SOURCE.read_bytes()
    contract = CONTRACT_SOURCE.read_bytes()
    remote_service = (REMOTE_SOURCE / "service.py").read_bytes()
    content_session = (REMOTE_SOURCE / "content_session.py").read_bytes()
    publisher_installer = INSTALLER_SOURCE.read_bytes()
    aster_installer = ASTER_INSTALLER_SOURCE.read_bytes()
    if sha(gateway) != SOURCE_SHA256["gateway"]:
        raise RuntimeError("bedroom-gateway-source-drift")
    if sha(contract) != SOURCE_SHA256["contract"]:
        raise RuntimeError("bedroom-contract-source-drift")
    for name, data in {
        "remote_service": remote_service,
        "content_session": content_session,
        "publisher_installer": publisher_installer,
        "aster_installer": aster_installer,
    }.items():
        if sha(data) != SOURCE_SHA256[name]:
            raise RuntimeError(f"bedroom-{name}-source-drift")

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

    outputs = {
        "gateway": gateway_output,
        "contract": contract_output,
        "remote_service": remote_service,
        "content_session": content_session,
        "publisher_installer": publisher_installer,
        "aster_installer": aster_installer,
    }
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
        "deployment_order": [
            "aster-agent-gateway",
            "home-assistant-contract-and-content-only-room",
            "bedroom-content-publisher",
        ],
        "files": [
            {
                "authority": {
                    "gateway": "aster-agent",
                    "contract": "home-assistant",
                    "remote_service": "astertv-bedroom",
                    "content_session": "astertv-bedroom",
                    "publisher_installer": "transient-installer",
                    "aster_installer": "transient-installer",
                }[name],
                "destination": DESTINATIONS[name],
                "source_sha256": SOURCE_SHA256[name],
                "sha256": sha(outputs[name]),
                "bytes": len(outputs[name]),
                "mode": "0755" if name.endswith("installer") else "0644",
            }
            for name in (
                "gateway", "contract", "remote_service", "content_session",
                "publisher_installer",
                "aster_installer",
            )
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
    names = {
        "gateway": "aster_remote.py",
        "contract": "contract.py",
        "remote_service": "service.py",
        "content_session": "content_session.py",
        "publisher_installer": "install_bedroom_publisher.py",
        "aster_installer": "install_aster_identity.py",
    }
    for name, data in outputs.items():
        target = output / names[name]
        descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}-", dir=output)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o755 if name.endswith("installer") else 0o644)
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
