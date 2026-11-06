"""Temporarily bind the closed SA4 transaction graph to registry v2.

The original v1 graph deliberately pins every filesystem owner and verifier to
the v1 registry.  The distinct canary is an additive registry-v2 target, so a
successor must switch every registry consumer together or fail closed.  This
module performs only that in-process binding; it has no filesystem, authority,
signing, transport, retry or service surface.
"""
from __future__ import annotations

from contextlib import contextmanager

import sa4_atomic_repair_owner_v1 as repair_owner
import sa4_atomic_rollback_owner_v1 as rollback_owner
import sa4_effect_admission_v1 as effect_admission
import sa4_inactive_checkpoint_owner_v1 as checkpoint_owner
import sa4_inactive_measurement_owner_v1 as measurement_owner
import sa4_independent_postcheck_receipt_v1 as receipt_validator
import sa4_independent_receipt_producer_v1 as receipt_producer
import sa4_independent_rollback_receipt_producer_v1 as rollback_producer
import sa4_preflight_composition_v1 as preflight
import sa4_receipt_ledger_reconciler_v2 as reconciler
import sa4_root_transaction_owner_v2 as root_owner
import sa4_runtime_control_owner_v1 as runtime_owner
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry_v1
import sa4_target_registry_v2 as registry_v2


TARGET_ID = "sa4-lxc104-canary-adapter-v2"


_BINDINGS = (
    (contract, "target_registry"),
    (root_owner, "registry"),
    (runtime_owner, "registry"),
    (measurement_owner, "registry"),
    (checkpoint_owner, "registry"),
    (repair_owner, "registry"),
    (receipt_producer, "registry"),
    (rollback_owner, "registry"),
    (rollback_producer, "registry"),
    (preflight, "target_registry"),
    (effect_admission, "registry"),
    (reconciler, "registry"),
    (receipt_validator, "registry"),
)


@contextmanager
def accepted_registry(plan_raw: bytes):
    """Bind all target consumers atomically for the one accepted v2 target."""
    value = contract.decode_unique_json(plan_raw)
    if not isinstance(value, dict) or value.get("target_id") != TARGET_ID:
        raise ValueError("SA4 distinct registry target changed")
    originals = tuple(getattr(module, name) for module, name in _BINDINGS)
    if all(original is registry_v2 for original in originals):
        plan = contract.validate_plan(plan_raw)
        target = registry_v2.resolve_production(plan["target_id"])
        if target.host_id != root_owner.BOUND_HOST_ID:
            raise ValueError("SA4 distinct registry host changed")
        yield plan
        return
    if any(original is not registry_v1 for original in originals):
        raise ValueError("SA4 distinct registry predecessor binding changed")
    for module, name in _BINDINGS:
        setattr(module, name, registry_v2)
    try:
        plan = contract.validate_plan(plan_raw)
        target = registry_v2.resolve_production(plan["target_id"])
        if target.host_id != root_owner.BOUND_HOST_ID:
            raise ValueError("SA4 distinct registry host changed")
        yield plan
    finally:
        for (module, name), original in zip(_BINDINGS, originals):
            setattr(module, name, original)

