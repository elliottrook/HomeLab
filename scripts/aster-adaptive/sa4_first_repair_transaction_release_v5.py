"""Post-controller, no-authority release packet for the first SA4 repair."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import sa4_effect_controller_inactive_install_result_v1 as controller_result
import sa4_runtime_control_inactive_upgrade_result_v1 as runtime_result

ROOT=Path(__file__).parents[2]
RUNTIME_RESULT=ROOT/"docs/projects/AI Projects/evidence/SA4-runtime-control-inactive-upgrade-result-2026-11-05.json"
CONTROLLER_RESULT=ROOT/"docs/projects/AI Projects/evidence/SA4-effect-controller-inactive-install-result-2026-11-05.json"
RUNTIME_RESULT_SHA256="10895012375e346b9fb633f287e44d00953ce1ad8e26c3af867540098e02332b"
CONTROLLER_RESULT_SHA256="27f5dfefc0f6eb74cf88ffb72971d97af332ee489dea6b15bc73e33c9c47f057"
RETAINED_PACKET=ROOT/"docs/projects/AI Projects/evidence/SA4-post-controller-first-repair-release-candidate-2026-11-06.json"
SOURCES={
"scripts/aster-adaptive/sa4_preflight_composition_v1.py":"a38ccb0b33bbc828f7ae96fd68304776cd840ea49bb07986044383e42fb1ad11",
"scripts/aster-adaptive/sa4_effect_admission_v1.py":"16d6bba03357c90da29591513d3e39019400c36dbfe1a6d64f9aef85226c040b",
"scripts/aster-adaptive/sa4_root_transaction_owner_v1.py":"e250bb2cf8bddf86634c973e968a787196ff0ae3fa7eaac10b2cd2d488404e3e",
"scripts/aster-adaptive/sa4_runtime_control_owner_v1.py":"6d6e89d22829395373089c50eece2ffcdcc042c70c85a25a2f38867f2b330daa",
"scripts/aster-adaptive/sa4_receipt_ledger_reconciler_v1.py":"9688ae6e6d50062a5b31e70bdec87d763d5b378ea681a35c07329f772cd669a1",
"scripts/aster-adaptive/sa4_one_shot_transaction_controller_v1.py":"4d7a2392c5b424a26e28a13e5205f144b1c27910929c8caaccf2b428188e11e7",
"scripts/aster-adaptive/sa4_observer_file_exchange_v1.py":"6cddfd315ca70753e7065de7d01eb176f9fc4b0a0d4740d326f3d08be1883a63",
"scripts/aster-adaptive/sa4_proxmox_observer_bridge_v1.py":"f6f6016c683b700ccda3806de99c500d3f24cab624eee89dd3a44791564d8632"}
PLAN_SHA256="596417038ccef2ad49b689417437877820b2e918968dfd8a0eb97485c7eb6956"
BEFORE="19b4e02d7f4edd9b38d9a0c3e9e3b49c4209473694fab39db0494c5fe523df1a"
AFTER="4529dee5c9b58b607a9025b62aa3a4871660de98c4bafbb7fd69d7bc2a1e1065"

def _sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def validate_static_evidence():
    for path,digest in SOURCES.items():
        if _sha(ROOT/path)!=digest: raise ValueError("SA4 v5 source changed")
    if _sha(RUNTIME_RESULT)!=RUNTIME_RESULT_SHA256 or _sha(CONTROLLER_RESULT)!=CONTROLLER_RESULT_SHA256:
        raise ValueError("SA4 v5 installed evidence changed")
    if runtime_result.validate(RUNTIME_RESULT.read_bytes())["inactive"] is not True:
        raise ValueError("SA4 runtime result is not inactive")
    if controller_result.validate(CONTROLLER_RESULT.read_bytes())["inactive"] is not True:
        raise ValueError("SA4 controller result is not inactive")

def packet():
    validate_static_evidence()
    return {"schema":"aster-sa4-first-repair-transaction-release.v5","release_id":"sa4-canary-first-repair-root-owner-v5","target_id":"sa4-lxc104-canary-adapter-v1","plan_sha256":PLAN_SHA256,"target_before_sha256":BEFORE,"target_after_sha256":AFTER,"runtime_control_install_result_sha256":RUNTIME_RESULT_SHA256,"effect_controller_install_result_sha256":CONTROLLER_RESULT_SHA256,"installed_source_sha256":dict(SOURCES),"required_fresh_authority":{"owner":"new-exact-plan-detached-proof","ai_pam":"new-exact-plan-one-use-grant-and-proof","grant_id":"new-unique-v5-id","prior_approval_reusable":False,"deadline_intersection":True},"required_fresh_runtime":{"whole_host_lease":"ready-no-active-lease","operation_lock":"owner-created-exclusively-at-runtime","emergency_stop":"owner-created-plan-bound-at-runtime","observer_exchange":"fixed-controller-bridge-protocol","fresh_measurement":True,"exclusive_checkpoint":True,"installed_hash_recheck":True,"production_postcheck":True},"transaction_limits":{"maximum_repairs":1,"maximum_rollbacks":1,"observer_signatures_success":1,"observer_signatures_rollback":2,"automatic_retry":False,"service_restart":False,"automatic_routing":"off"},"status":"release-candidate-awaiting-new-exact-repair-approval","effect_authorized":False,"exclusions":["other-targets","credentials","firewall","network","model","service-restart","shared-infrastructure","automatic-promotion"]}

def canonical_packet(): return (json.dumps(packet(),sort_keys=True,separators=(",",":"))+"\n").encode()
def packet_sha256(): return hashlib.sha256(canonical_packet()).hexdigest()
def validate_retained_packet():
    if RETAINED_PACKET.read_bytes()!=canonical_packet(): raise ValueError("SA4 v5 retained packet changed")
validate_static_evidence()
