"""Distinct-canary SA4 transaction owner using the accepted v2 registry.

The installed v2 owner is immutable evidence for the spent first canary.  This
source-only successor reuses its closed phase graph while resolving targets
only through the separately accepted v2 registry.  It adds no command,
signing, transport or retry surface.
"""
from __future__ import annotations

from contextlib import contextmanager

import sa4_root_transaction_owner_v2 as previous
import sa4_target_registry_v2 as registry


BOUND_TARGET_ID = "sa4-lxc104-canary-adapter-v2"


@contextmanager
def _accepted_registry(plan_raw: bytes):
    plan = previous.contract.validate_plan(plan_raw)
    if plan["target_id"] != BOUND_TARGET_ID:
        raise ValueError("SA4 v3 transaction target changed")
    target = registry.resolve_production(plan["target_id"])
    if target.host_id != previous.BOUND_HOST_ID:
        raise ValueError("SA4 v3 transaction host changed")
    original = previous.registry
    previous.registry = registry
    try:
        yield
    finally:
        previous.registry = original


class RootTransactionOwner(previous.RootTransactionOwner):
    """Run the v2 closed graph only for the accepted distinct canary."""

    def prepare(self, plan_raw: bytes, *args, **kwargs):
        with _accepted_registry(plan_raw):
            return super().prepare(plan_raw, *args, **kwargs)

    def execute_once(self, *args, **kwargs):
        with _accepted_registry(self._values["plan"]):
            return super().execute_once(*args, **kwargs)

    def observe(self, *args, **kwargs):
        with _accepted_registry(self._values["plan"]):
            return super().observe(*args, **kwargs)

    def rollback_once(self, *args, **kwargs):
        with _accepted_registry(self._values["plan"]):
            return super().rollback_once(*args, **kwargs)

