"""Closed SA4 owner graph with complete distinct-registry binding."""
from __future__ import annotations

import sa4_distinct_registry_bindings_v1 as bindings
import sa4_root_transaction_owner_v2 as previous


class RootTransactionOwner(previous.RootTransactionOwner):
    """Run the accepted v2 graph only while every registry consumer is bound."""

    def _plan(self) -> bytes:
        raw = self._values.get("plan")
        if not isinstance(raw, bytes) or not raw:
            raise ValueError("SA4 v4 transaction plan is absent")
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

