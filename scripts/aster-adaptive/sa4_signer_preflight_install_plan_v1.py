"""Inert reversible install plan for SA4 signers and preflight correction."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import PurePosixPath


LXC_LIBEXEC = "/usr/local/libexec/aster-sa4"
LXC_CHECKPOINT = "/var/lib/aster/sa4/source-checkpoints/preflight-correction-v1"
MAC_DIRECTORY = "/Users/jelliott/Library/Application Support/Aster/SA4"
MAC_OLD_BINARY = f"{MAC_DIRECTORY}/sa4-owner-signer-485eff23"
MAC_NEW_BINARY = f"{MAC_DIRECTORY}/sa4-owner-signer-4148fee1"


@dataclass(frozen=True)
class Change:
    host_id: str
    source: str
    destination: str
    old_sha256: str | None
    new_sha256: str
    owner: str
    group: str
    mode: str
    operation: str


CHANGES = (
    Change(
        "macbook-owner",
        "compiled-and-ad-hoc-signed:sa4_owner_keychain_signer_v1.swift",
        MAC_NEW_BINARY,
        None,
        "ecf91f6356c368777a5910d8e4c228418ebc05728f3c11f1d7b0b53ed6288836",
        "jelliott", "staff", "0755", "create-exclusive",
    ),
    Change(
        "lxc104",
        "scripts/aster-adaptive/sa4_preflight_composition_v1.py",
        f"{LXC_LIBEXEC}/sa4_preflight_composition_v1.py",
        "a45335dcb6ab209433e71bd486345904d4e0748f5ae03bc85f24a7863926b569",
        "a38ccb0b33bbc828f7ae96fd68304776cd840ea49bb07986044383e42fb1ad11",
        "root", "root", "0644", "checkpoint-and-atomic-replace",
    ),
    Change(
        "lxc104",
        "scripts/aster-adaptive/sa4_ai_pam_signer_v1.py",
        f"{LXC_LIBEXEC}/sa4_ai_pam_signer_v1.py",
        None,
        "10a7e39faacd6b42bd7529720d896683e6722fd954e15af17db57246d1792e55",
        "root", "hlabroker", "0640", "create-exclusive",
    ),
)

SOURCE_HASHES = {
    "scripts/aster-adaptive/sa4_owner_keychain_signer_v1.swift":
        "03bf11c798f31f57c7ac5cb8ce0ebd5b1b1f180892032423fefed52854b67b44",
    "scripts/aster-adaptive/sa4_preflight_composition_v1.py":
        "a38ccb0b33bbc828f7ae96fd68304776cd840ea49bb07986044383e42fb1ad11",
    "scripts/aster-adaptive/sa4_ai_pam_signer_v1.py":
        "10a7e39faacd6b42bd7529720d896683e6722fd954e15af17db57246d1792e55",
}

PRECONDITIONS = {
    "mac_old_binary_sha256":
        "b56d9a35d1edd66a4efcc5a1624e5c1640797678e7397a9a1c2489f3720e372b",
    "mac_new_binary": "absent",
    "lxc_preflight_old_sha256":
        "a45335dcb6ab209433e71bd486345904d4e0748f5ae03bc85f24a7863926b569",
    "lxc_ai_pam_wrapper": "absent",
    "lxc_private_key": "regular-hlabroker-hlabroker-0600-metadata-only",
    "lxc_openssl": "regular-root-root-0755",
}

EXCLUSIONS = (
    "no-private-key-read-print-copy-or-export",
    "no-keychain-query-or-prompt",
    "no-signature-or-authority",
    "no-grant-claim-checkpoint-repair-or-receipt",
    "no-service-unit-timer-booking-restart-reload-or-routing",
)


def _clean_absolute(path: str) -> bool:
    return path.startswith("/") and str(PurePosixPath(path)) == path


def validate() -> None:
    if (len(CHANGES) != 3 or len({item.destination for item in CHANGES}) != 3
            or set(SOURCE_HASHES) != {
                "scripts/aster-adaptive/sa4_owner_keychain_signer_v1.swift",
                "scripts/aster-adaptive/sa4_preflight_composition_v1.py",
                "scripts/aster-adaptive/sa4_ai_pam_signer_v1.py",
            }):
        raise ValueError("SA4 signer/preflight install set changed")
    for item in CHANGES:
        if (not _clean_absolute(item.destination)
                or item.operation not in {
                    "create-exclusive", "checkpoint-and-atomic-replace"}
                or item.mode not in {"0640", "0644", "0755"}):
            raise ValueError("unsafe SA4 signer/preflight change")
    if CHANGES[1].old_sha256 is None or any(
            item.old_sha256 is not None for item in (CHANGES[0], CHANGES[2])):
        raise ValueError("SA4 replacement boundary changed")


def plan() -> dict[str, object]:
    validate()
    return {
        "schema": "aster-sa4-signer-preflight-install-plan.v1",
        "changes": [asdict(item) for item in CHANGES],
        "source_hashes": dict(SOURCE_HASHES),
        "preconditions": dict(PRECONDITIONS),
        "lxc_checkpoint": {
            "path": LXC_CHECKPOINT,
            "owner": "root", "group": "root", "mode": "0700",
            "retained_old_file_mode": "0600",
        },
        "postchecks": [
            "all-destination-hashes-and-metadata-exact",
            "owner-new-binary-codesign-strict-and-self-test-only",
            "lxc-production-target-resolves-to-lxc104",
            "lxc-ai-pam-wrapper-import-and-canonical-validation-only",
            "no-signature-grant-claim-checkpoint-repair-or-service-action",
            "production-health-unchanged",
        ],
        "rollback": {
            "mac": "remove-new-version-only-if-hash-unchanged",
            "lxc": "restore-retained-preflight-and-remove-new-wrapper-if-hashes-unchanged",
            "uncertainty": "retain-and-stop",
        },
        "effect_authorized": False,
        "automatic_routing": "off",
        "exclusions": list(EXCLUSIONS),
    }


validate()

