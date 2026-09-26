"""Synthetic M1 lifecycle evidence; no production endpoints or credentials."""

import concurrent.futures
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from broker_core import BrokerDenied, BrokerStore
from broker_approval_service import ApprovalHandler
from broker_service import BrokerHandler


ACTOR = "a" * 64


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.TemporaryDirectory()
        self.addCleanup(self.root.cleanup)
        self.path = Path(self.root.name) / "state.db"
        self.now = 1000
        self.store = BrokerStore(self.path, clock=lambda: self.now)
        self.addCleanup(lambda: self.store.close())
        self.store.set_approver_enabled(ACTOR, True)
        self.store.register_agent("owner", 1001)
        self.store.register_agent("other", 1002)
        self.store.set_agent_state("owner", "operator")
        self.store.register_service("fixture")
        self.store.register_capability("read", "fixture", "green", probation_allowed=True)
        self.store.register_capability("change", "fixture", "yellow")
        self.store.register_capability("red", "fixture", "red")
        for capability in ("read", "change", "red"):
            self.store.grant_capability("owner", capability)

    def request(self, capability="read", ttl=300):
        r = self.store.create_request("owner", capability, {}, ttl_seconds=ttl)
        if capability != "read":
            self.store.approve_request(r.request_id, r.payload_hash, actor=ACTOR,
                                       assurance="passkey", auth_time=self.now)
        return r

    def consume(self, r, store=None):
        return (store or self.store).consume_request(r.request_id, {}, agent_id="owner")

    def reopen(self):
        self.store.close()
        self.store = BrokerStore(self.path, clock=lambda: self.now)

    def test_wrong_caller_cannot_burn_request_or_spoof_owner(self):
        r = self.request()
        handler = object.__new__(BrokerHandler)
        handler.server = SimpleNamespace(store=self.store)
        with self.assertRaisesRegex(BrokerDenied, "another agent"):
            handler.dispatch("other", {"method": "request.consume", "request_id": r.request_id,
                                       "payload": {}, "agent_id": "owner"})
        self.assertEqual("approved", self.store.get_request(r.request_id).status)
        self.assertEqual("consumed", self.consume(r).status)

    def test_exact_expiry_survives_restart_for_all_risks(self):
        for capability in ("read", "change", "red"):
            with self.subTest(capability=capability):
                r = self.request(capability, ttl=1)
                self.now += 1
                self.reopen()
                with self.assertRaisesRegex(BrokerDenied, "expired"):
                    self.consume(r)
                self.reopen()
                self.assertEqual("expired", self.store.get_request(r.request_id).status)

    def test_pending_approval_at_expiry_is_terminal(self):
        r = self.store.create_request("owner", "change", {}, ttl_seconds=1)
        self.now += 1
        with self.assertRaisesRegex(BrokerDenied, "expired"):
            self.store.approve_request(r.request_id, r.payload_hash, actor=ACTOR)
        self.reopen()
        self.assertEqual("expired", self.store.get_request(r.request_id).status)

    def test_disable_enable_and_demotion_promotion_never_resurrect(self):
        mutations = (
            lambda: (self.store.set_global_enabled(False), self.store.set_global_enabled(True)),
            lambda: (self.store.set_service_enabled("fixture", False), self.store.set_service_enabled("fixture", True)),
            lambda: (self.store.set_agent_state("owner", "probation"), self.store.set_agent_state("owner", "operator")),
            lambda: (self.store.set_agent_state("owner", "suspended"), self.store.set_agent_state("owner", "operator")),
            lambda: (self.store.set_approver_enabled(ACTOR, False), self.store.set_approver_enabled(ACTOR, True)),
        )
        for mutation in mutations:
            r = self.request("change")
            mutation()
            self.reopen()
            with self.assertRaises(BrokerDenied):
                self.consume(r)
            self.assertEqual("revoked", self.store.get_request(r.request_id).status)
        self.assertEqual("consumed", self.consume(self.request("change")).status)

    def test_policy_and_grant_changes_invalidate_even_if_restored(self):
        changes = (
            ("UPDATE capabilities SET risk_class='red' WHERE capability='change'",
             "UPDATE capabilities SET risk_class='yellow' WHERE capability='change'"),
            ("UPDATE capabilities SET enabled=0 WHERE capability='change'",
             "UPDATE capabilities SET enabled=1 WHERE capability='change'"),
            ("UPDATE capabilities SET probation_allowed=1 WHERE capability='change'",
             "UPDATE capabilities SET probation_allowed=0 WHERE capability='change'"),
            ("DELETE FROM agent_capabilities WHERE agent_id='owner' AND capability='change'",
             "INSERT INTO agent_capabilities VALUES('owner','change')"),
        )
        for statements in changes:
            with self.subTest(statements=statements):
                r = self.request("change")
                with self.store.connection:
                    for sql in statements:
                        self.store.connection.execute(sql)
                self.reopen()
                with self.assertRaises(BrokerDenied):
                    self.consume(r)
                self.assertEqual("revoked", self.store.get_request(r.request_id).status)

    def test_noop_policy_update_preserves_request(self):
        r = self.request("change")
        self.store.set_agent_state("owner", "operator")
        self.store.set_service_enabled("fixture", True)
        self.assertEqual("consumed", self.consume(r).status)

    def test_concurrent_consumers_across_connections_have_one_winner(self):
        stores = [BrokerStore(self.path, clock=lambda: self.now) for _ in range(8)]
        for store in stores:
            self.addCleanup(store.close)
        for _ in range(5):
            r = self.request("change")
            barrier = threading.Barrier(len(stores))
            def attempt(store):
                barrier.wait(timeout=5)
                try:
                    return self.consume(r, store).status
                except BrokerDenied:
                    return "denied"
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(attempt, stores))
            self.assertEqual(1, results.count("consumed"))
            self.assertEqual(7, results.count("denied"))
            self.assertEqual(1, sum(row["event"] == "request.consume" and row["request_id"] == r.request_id
                                    for row in self.store.audit_rows()))

    def test_same_connection_concurrent_consumers_have_one_winner(self):
        r = self.request()
        barrier = threading.Barrier(8)
        def attempt(_):
            barrier.wait(timeout=5)
            try:
                return self.consume(r).status
            except BrokerDenied:
                return "denied"
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(attempt, range(8)))
        self.assertEqual(1, results.count("consumed"))

    def test_committed_revocation_wins_against_waiting_consumer(self):
        r = self.request("change")
        other = BrokerStore(self.path, clock=lambda: self.now)
        self.addCleanup(other.close)
        ready = threading.Event()
        def attempt():
            ready.set()
            try:
                self.consume(r, other)
                return "consumed"
            except BrokerDenied:
                return "denied"
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            with self.store._transaction():
                future = pool.submit(attempt)
                self.assertTrue(ready.wait(5))
                self.store.revoke_request(r.request_id)
            self.assertEqual("denied", future.result(timeout=5))

    def test_audit_failure_rolls_back_consume_and_restart_allows_one_retry(self):
        r = self.request()
        with patch.object(self.store, "_audit", side_effect=RuntimeError("fixture disk fault")):
            with self.assertRaises(RuntimeError):
                self.consume(r)
        self.reopen()
        self.assertEqual("approved", self.store.get_request(r.request_id).status)
        self.consume(r)
        self.reopen()
        with self.assertRaises(BrokerDenied):
            self.consume(r)

    def test_process_exit_before_commit_rolls_back_claim(self):
        r = self.request()
        code = """
import os, sys
from broker_core import BrokerStore
s = BrokerStore(sys.argv[1], clock=lambda: 1000)
s._audit = lambda *args: os._exit(73)
s.consume_request(sys.argv[2], {}, agent_id='owner')
"""
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).parent.resolve()))
        child = subprocess.run([sys.executable, "-c", code, str(self.path), r.request_id],
                               env=env, capture_output=True, timeout=10)
        self.assertEqual(73, child.returncode, child.stderr)
        self.reopen()
        self.assertEqual("approved", self.store.get_request(r.request_id).status)
        self.assertEqual("consumed", self.consume(r).status)

    def test_restore_preserves_consumed_revoked_and_expired_denials(self):
        consumed, revoked, expired = self.request(), self.request(), self.request(ttl=1)
        self.consume(consumed)
        self.store.revoke_request(revoked.request_id)
        self.now += 1
        with self.assertRaises(BrokerDenied):
            self.consume(expired)
        restore = Path(self.root.name) / "restored.db"
        with sqlite3.connect(restore) as destination:
            self.store.connection.backup(destination)
        recovered = BrokerStore(restore, clock=lambda: self.now)
        self.addCleanup(recovered.close)
        for r in (consumed, revoked, expired):
            with self.assertRaises(BrokerDenied):
                self.consume(r, recovered)

    def test_approver_entitlement_required_for_reads_and_mutations(self):
        handler = object.__new__(ApprovalHandler)
        handler.server = SimpleNamespace(store=self.store)
        r = self.store.create_request("owner", "change", {})
        for method in ("pending.list", "management.snapshot", "request.history", "audit.search",
                       "request.approve", "request.deny", "management.global-enabled"):
            for actor in (None, "b" * 64):
                with self.subTest(method=method, actor=actor), self.assertRaises(BrokerDenied):
                    handler.dispatch({"method": method, "actor": actor, "request_id": r.request_id,
                                      "payload_hash": r.payload_hash, "enabled": False,
                                      "assurance": "passkey", "auth_time": self.now})
        self.assertTrue(self.store.global_enabled())
        self.assertEqual("pending", self.store.get_request(r.request_id).status)
        self.assertEqual(1, len(handler.dispatch({"method": "pending.list", "actor": ACTOR})))

    def test_revoked_approver_cannot_approve_after_restart(self):
        r = self.store.create_request("owner", "change", {})
        self.store.set_approver_enabled(ACTOR, False)
        self.reopen()
        with self.assertRaisesRegex(BrokerDenied, "entitled"):
            self.store.approve_request(r.request_id, r.payload_hash, actor=ACTOR)

    def test_red_rejects_malformed_future_and_stale_auth_time(self):
        r = self.store.create_request("owner", "red", {})
        for auth_time in (None, True, "1000", 1000.0, 1001, 879):
            with self.subTest(auth_time=auth_time), self.assertRaises(BrokerDenied):
                self.store.approve_request(r.request_id, r.payload_hash, actor=ACTOR,
                                           assurance="passkey", auth_time=auth_time)
        self.assertEqual("pending", self.store.get_request(r.request_id).status)

    def test_process_exit_after_commit_never_replays(self):
        r = self.request()
        code = """
import os, sys
from broker_core import BrokerStore
s = BrokerStore(sys.argv[1], clock=lambda: 1000)
s.consume_request(sys.argv[2], {}, agent_id='owner')
os._exit(74)
"""
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).parent.resolve()))
        child = subprocess.run([sys.executable, "-c", code, str(self.path), r.request_id],
                               env=env, capture_output=True, timeout=10)
        self.assertEqual(74, child.returncode, child.stderr)
        self.reopen()
        with self.assertRaises(BrokerDenied):
            self.consume(r)
        self.assertEqual("consumed", self.store.get_request(r.request_id).status)

    def test_lock_timeout_leaves_request_unconsumed(self):
        r = self.request()
        other = BrokerStore(self.path, clock=lambda: self.now)
        self.addCleanup(other.close)
        # A real second SQLite connection holds a writer lock, not a mocked race.
        with other._transaction():
            with self.assertRaisesRegex(sqlite3.OperationalError, "locked"):
                self.consume(r)
        self.assertEqual("approved", self.store.get_request(r.request_id).status)
        self.assertEqual("consumed", self.consume(r).status)

    def test_approval_and_revocation_cannot_resurrect_in_parallel(self):
        r = self.store.create_request("owner", "change", {})
        other = BrokerStore(self.path, clock=lambda: self.now)
        self.addCleanup(other.close)
        ready = threading.Event()
        def approve():
            ready.set()
            try:
                other.approve_request(r.request_id, r.payload_hash, actor=ACTOR)
                return "approved"
            except BrokerDenied:
                return "denied"
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            with self.store._transaction():
                future = pool.submit(approve)
                self.assertTrue(ready.wait(5))
                self.store.revoke_request(r.request_id)
            self.assertEqual("denied", future.result(timeout=5))
        self.assertEqual("revoked", self.store.get_request(r.request_id).status)

    def test_new_database_has_no_implicit_approver(self):
        empty = BrokerStore(Path(self.root.name) / "empty.db")
        self.addCleanup(empty.close)
        with self.assertRaisesRegex(BrokerDenied, "entitled"):
            empty.require_approver(ACTOR)

    def test_no_socket_method_can_enroll_an_approver(self):
        handlers = [object.__new__(ApprovalHandler), object.__new__(BrokerHandler)]
        for handler in handlers:
            handler.server = SimpleNamespace(store=self.store)
            request = {"method": "approver-enable", "actor": ACTOR, "subject_hash": "b" * 64}
            with self.assertRaisesRegex(BrokerDenied, "not exposed"):
                if isinstance(handler, ApprovalHandler):
                    handler.dispatch(request)
                else:
                    handler.dispatch("owner", request)
        with self.assertRaises(BrokerDenied):
            self.store.require_approver("b" * 64)
