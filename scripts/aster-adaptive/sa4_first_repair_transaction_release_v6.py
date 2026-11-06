"""Final post-runner no-authority release for first SA4 repair."""
import hashlib,json
from pathlib import Path
import sa4_first_repair_transaction_release_v5 as previous
import sa4_fixed_runner_inactive_install_result_v1 as runner_result
ROOT=Path(__file__).parents[2]
RUNNER_SOURCE="scripts/aster-adaptive/sa4_fixed_transaction_runner_v1.py"
RUNNER_SHA256="d48e26d50f7d924def929363c10a386030d0bedd51854657de82abc2572fb74e"
RUNNER_RESULT=ROOT/"docs/projects/AI Projects/evidence/SA4-fixed-runner-inactive-install-result-2026-11-06.json"
RUNNER_RESULT_SHA256="27ceea48ae734da69ad23a008f6aa31ac57d6cd1f08e0f6c2bff6f57662da2bd"
RETAINED=ROOT/"docs/projects/AI Projects/evidence/SA4-final-runner-bound-repair-release-2026-11-06.json"
def validate_static_evidence():
    previous.validate_static_evidence(); previous.validate_retained_packet()
    if hashlib.sha256((ROOT/RUNNER_SOURCE).read_bytes()).hexdigest()!=RUNNER_SHA256 or hashlib.sha256(RUNNER_RESULT.read_bytes()).hexdigest()!=RUNNER_RESULT_SHA256: raise ValueError("SA4 v6 runner evidence changed")
    if runner_result.validate(RUNNER_RESULT.read_bytes())["inactive"] is not True: raise ValueError("SA4 v6 runner is not inactive")
def packet():
    validate_static_evidence(); value=previous.packet(); sources=dict(value["installed_source_sha256"]); sources[RUNNER_SOURCE]=RUNNER_SHA256
    value.update(schema="aster-sa4-first-repair-transaction-release.v6",release_id="sa4-canary-first-repair-root-owner-v6",installed_source_sha256=sources,fixed_runner_install_result_sha256=RUNNER_RESULT_SHA256,status="release-candidate-awaiting-new-exact-repair-approval")
    value["required_fresh_authority"]={**value["required_fresh_authority"],"grant_id":"new-unique-v6-id"}
    value["required_fresh_runtime"]={**value["required_fresh_runtime"],"fixed_runner":"installed-no-argument-entry-point"}
    return value
def canonical_packet(): return (json.dumps(packet(),sort_keys=True,separators=(",",":"))+"\n").encode()
def packet_sha256(): return hashlib.sha256(canonical_packet()).hexdigest()
def validate_retained_packet():
    if RETAINED.read_bytes()!=canonical_packet(): raise ValueError("SA4 v6 retained packet changed")
validate_static_evidence()
