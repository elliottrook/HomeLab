"""Closed SA4 owner graph with the corrected v2 postcheck lineage."""
from __future__ import annotations

import sa4_distinct_registry_bindings_v2 as bindings
import sa4_root_transaction_owner_v2 as previous


BOUND_TARGET_ID = bindings.TARGET_ID


class RootTransactionOwner(previous.RootTransactionOwner):
    def _plan(self) -> bytes:
        raw = self._values.get("plan")
        if not isinstance(raw, bytes) or not raw:
            raise ValueError("SA4 v6 transaction plan is absent")
        return raw

    def prepare(self, plan_raw: bytes, *args, **kwargs):
        with bindings.accepted_registry(plan_raw):
            return super().prepare(plan_raw, *args, **kwargs)

    def execute_once(self, *args, **kwargs):
        with bindings.accepted_registry(self._plan()):
            return super().execute_once(*args, **kwargs)

    def observe(self, *args, **kwargs):
        with bindings.accepted_registry(self._plan()):
            return super().observe(*args, **kwargs)

    def accept_postcheck_proof(self, *args, **kwargs):
        with bindings.accepted_registry(self._plan()):
            return super().accept_postcheck_proof(*args, **kwargs)

    def rollback_once(self, *args, **kwargs):
        with bindings.accepted_registry(self._plan()):
            return super().rollback_once(*args, **kwargs)

    def accept_rollback_proof(self, *args, **kwargs):
        with bindings.accepted_registry(self._plan()):
            return super().accept_rollback_proof(*args, **kwargs)

    def finish(self, *args, **kwargs):
        with bindings.accepted_registry(self._plan()):
            return super().finish(*args, **kwargs)
