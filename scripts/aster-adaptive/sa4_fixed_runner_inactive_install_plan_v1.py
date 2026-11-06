"""Inactive create-exclusive plan for the fixed SA4 runner."""
from pathlib import Path
import hashlib
SOURCE="scripts/aster-adaptive/sa4_fixed_transaction_runner_v1.py"
DESTINATION="/usr/local/libexec/aster-sa4/sa4_fixed_transaction_runner_v1.py"
AFTER_SHA256="d48e26d50f7d924def929363c10a386030d0bedd51854657de82abc2572fb74e"
DEPENDENCIES={"/usr/local/libexec/aster-sa4/sa4_one_shot_transaction_controller_v1.py":"4d7a2392c5b424a26e28a13e5205f144b1c27910929c8caaccf2b428188e11e7","/usr/local/libexec/aster-sa4/sa4_observer_file_exchange_v1.py":"6cddfd315ca70753e7065de7d01eb176f9fc4b0a0d4740d326f3d08be1883a63"}
def validate(root=Path(__file__).parents[2]):
    if hashlib.sha256((root/SOURCE).read_bytes()).hexdigest()!=AFTER_SHA256: raise ValueError("SA4 fixed runner source changed")
def plan():
    validate(); return {"schema":"aster-sa4-fixed-runner-inactive-install-plan.v1","host_id":"lxc104","source":SOURCE,"destination":DESTINATION,"before":"absent","after_sha256":AFTER_SHA256,"owner":"root","group":"root","mode":"0644","operation":"create-exclusive","dependencies":DEPENDENCIES,"rollback":{"remove-only-if-after-hash-matches":True,"uncertainty":"retain-and-stop"},"postcheck":["exact-hash-metadata","isolated-import","no-runtime-state"],"effect_authorized":False,"automatic_routing":"off","exclusions":["no-runner-invocation","no-input-or-ledger","no-key-signature-authority","no-target-or-service-effect"]}
validate()
