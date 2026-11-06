"""Exact, source-only plan for reversible SA4 public-trust installation."""
from __future__ import annotations


BASE = "/usr/local/libexec/aster-sa4"
CHECKPOINT = "/var/lib/aster/sa4/source-checkpoints/public-trust-v1"
OLD_SHA256 = {
    f"{BASE}/sa4_authenticated_authority_v1.py":
        "cbc976176841890ba53e2458e55f09c33c802605cfa43ea8c2c3bdd8766be6ee",
    f"{BASE}/sa4_independent_postcheck_receipt_v1.py":
        "a1e99c3abbe90ed788a33118b40d3630d34b740a09e72067871515cf3e145b9d",
    f"{BASE}/sa4_key_custody_slots_v1.py":
        "6e45ecad5bf7d1f7b80e040b9b24b380ef21a9f3343e93f127f0ffb246e04816",
}
NEW_SHA256 = {
    f"{BASE}/sa4_authenticated_authority_v1.py":
        "367bf1a1e473363b8c8aac7d13a4f06456964de45093c172e32a1f3c93a725d6",
    f"{BASE}/sa4_independent_postcheck_receipt_v1.py":
        "ab58b635d823a1c82f30d8d89f68c1ed25519914270c7e3d467228bf2452c355",
    f"{BASE}/sa4_key_custody_slots_v1.py":
        "e1d9088a1725847a6b7f16460177e266e076fd987b01894daf4a69c5b2b8d0d0",
    f"{BASE}/sa4_public_trust_candidate_v1.py":
        "3c1f02bba3985033157977d6810192888b09595ec3af0c55ef1e1c15e135195e",
}
SOURCE_BY_PATH = {
    f"{BASE}/sa4_authenticated_authority_v1.py":
        "scripts/aster-adaptive/sa4_authenticated_authority_v1.py",
    f"{BASE}/sa4_independent_postcheck_receipt_v1.py":
        "scripts/aster-adaptive/sa4_independent_postcheck_receipt_v1.py",
    f"{BASE}/sa4_key_custody_slots_v1.py":
        "scripts/aster-adaptive/sa4_key_custody_slots_v1.py",
    f"{BASE}/sa4_public_trust_candidate_v1.py":
        "scripts/aster-adaptive/sa4_public_trust_candidate_v1.py",
}


def plan(*, observed_sha256: dict[str, str], absent_paths: set[str]
         ) -> dict[str, object]:
    candidate_path = f"{BASE}/sa4_public_trust_candidate_v1.py"
    if observed_sha256 != OLD_SHA256:
        raise ValueError("exact installed empty-trust source hashes required")
    if absent_paths != {candidate_path, CHECKPOINT}:
        raise ValueError("candidate and checkpoint paths must be exactly absent")
    return {
        "schema": "aster-sa4-public-trust-install-plan.v1",
        "host_id": "lxc104",
        "checkpoint": {
            "path": CHECKPOINT, "owner": "root", "group": "root",
            "mode": "0700", "copy_mode": "0600",
            "retain_after_success": True,
        },
        "replacements": [{
            "path": path, "old_sha256": OLD_SHA256[path],
            "new_sha256": NEW_SHA256[path], "source": SOURCE_BY_PATH[path],
            "owner": "root", "group": "root", "mode": "0644",
            "method": "atomic-replace-no-follow",
        } for path in OLD_SHA256],
        "creation": {
            "path": candidate_path, "sha256": NEW_SHA256[candidate_path],
            "source": SOURCE_BY_PATH[candidate_path],
            "owner": "root", "group": "root", "mode": "0644",
            "method": "exclusive-create-no-follow",
        },
        "postcheck": {
            "import_all_installed_modules": True,
            "authority_key_counts": {"owner-approval": 1, "ai-pam-grant": 1},
            "observer_key_count": 1,
            "slot_status": "accepted-public-source",
            "effect_authorized": False,
        },
        "rollback": {
            "restore_exact_checkpoint_hashes": True,
            "remove_created_candidate_only_if_hash_unchanged": True,
            "on_uncertainty": "retain-and-stop",
        },
        "service_action": "none",
        "signing_ceremony_authorized": False,
        "effect_authorized": False,
        "automatic_routing": "off",
    }
