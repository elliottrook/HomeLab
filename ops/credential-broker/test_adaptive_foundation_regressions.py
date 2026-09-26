"""M1 required-denial regressions using synthetic state only."""

import unittest
import tempfile
import threading
import sqlite3
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from broker_core import BrokerDenied, BrokerStore
from broker_service import BrokerHandler


class AdaptiveFoundationRegressions(unittest.TestCase):
    def setUp(self):
        self.store = BrokerStore(":memory:", clock=lambda: 1000)
        self.addCleanup(self.store.close)
        self.store.register_agent("fixture-owner", 10001)
        self.store.register_agent("fixture-other", 10002)
        self.store.register_service("fixture")
        self.store.register_capability("fixture.read", "fixture", "green", probation_allowed=True)
        self.store.register_capability("fixture.change", "fixture", "yellow")
        for agent in ("fixture-owner", "fixture-other"):
            self.store.grant_capability(agent, "fixture.read")
        self.store.grant_capability("fixture-owner", "fixture.change")
        self.handler = object.__new__(BrokerHandler)
        self.handler.server = SimpleNamespace(store=self.store)

    def test_consume_must_bind_authenticated_originating_agent(self):
        request = self.store.create_request("fixture-owner", "fixture.read", {})
        with self.assertRaises(BrokerDenied):
            self.handler.dispatch("fixture-other", {
                "method": "request.consume", "request_id": request.request_id, "payload": {},
            })
        self.assertEqual("approved", self.store.get_request(request.request_id).status)
        self.assertEqual("consumed", self.handler.dispatch("fixture-owner", {
            "method": "request.consume", "request_id": request.request_id, "payload": {},
        })["status"])

    def test_approved_action_must_not_survive_demotion_to_probation(self):
        self.store.set_agent_state("fixture-owner", "operator")
        request = self.store.create_request("fixture-owner", "fixture.change", {})
        self.store.approve_request(request.request_id, request.payload_hash)
        self.store.set_agent_state("fixture-owner", "probation")
        with self.assertRaises(BrokerDenied):
            self.handler.dispatch("fixture-owner", {
                "method": "request.consume", "request_id": request.request_id, "payload": {},
            })

    def test_json_identity_cannot_override_authenticated_caller(self):
        request = self.store.create_request("fixture-owner", "fixture.read", {})
        with self.assertRaises(BrokerDenied):
            self.handler.dispatch("fixture-other", {
                "method": "request.consume", "request_id": request.request_id,
                "payload": {}, "agent_id": "fixture-owner",
            })

    def test_demotion_then_promotion_does_not_resurrect_approval(self):
        self.store.set_agent_state("fixture-owner", "operator")
        request = self.store.create_request("fixture-owner", "fixture.change", {})
        self.store.approve_request(request.request_id, request.payload_hash)
        self.store.set_agent_state("fixture-owner", "probation")
        self.store.set_agent_state("fixture-owner", "operator")
        with self.assertRaises(BrokerDenied):
            self.store.consume_request(request.request_id, {}, agent_id="fixture-owner")
        self.assertEqual("revoked", self.store.get_request(request.request_id).status)

    def test_current_policy_changes_fail_closed(self):
        # Direct SQL models policy drift from an independent administrative
        # process. It is test-only, not a supported production update path.
        mutations = [
            "DELETE FROM agent_capabilities WHERE agent_id='fixture-owner'",
            "UPDATE capabilities SET enabled=0",
            "UPDATE services SET enabled=0",
            "UPDATE agents SET state='suspended'",
            "UPDATE capabilities SET probation_allowed=0",
            "UPDATE capabilities SET risk_class='yellow'",
            "UPDATE services SET execution_mode='wrapped-static'",
            "UPDATE requests SET policy_hash=NULL",
        ]
        snapshot = sqlite3.connect(":memory:")
        self.addCleanup(snapshot.close)
        self.store.connection.backup(snapshot)
        for sql in mutations:
            with self.subTest(sql=sql):
                request = self.store.create_request("fixture-owner", "fixture.read", {})
                self.store.connection.execute("SAVEPOINT drift")
                self.store.connection.execute(sql)
                # Commit synthetic drift; restore the fixture after the assertion.
                self.store.connection.execute("RELEASE drift")
                with self.assertRaises(BrokerDenied):
                    self.store.consume_request(request.request_id, {}, agent_id="fixture-owner")
                self.assertEqual("approved", self.store.get_request(request.request_id).status)
                snapshot.backup(self.store.connection)

    def test_approval_rechecks_current_policy(self):
        self.store.set_agent_state("fixture-owner", "operator")
        request = self.store.create_request("fixture-owner", "fixture.change", {})
        with self.store.connection:
            self.store.connection.execute("UPDATE capabilities SET risk_class='red' WHERE capability='fixture.change'")
        with self.assertRaises(BrokerDenied):
            self.store.approve_request(request.request_id, request.payload_hash)
        self.assertEqual("pending", self.store.get_request(request.request_id).status)

    def test_policy_code_version_change_requires_new_request(self):
        request = self.store.create_request("fixture-owner", "fixture.read", {})
        with patch("broker_core.AUTHORIZATION_POLICY_VERSION", "future-policy"):
            with self.assertRaises(BrokerDenied):
                self.store.consume_request(request.request_id, {}, agent_id="fixture-owner")

    def test_audit_failure_rolls_back_consumption(self):
        request = self.store.create_request("fixture-owner", "fixture.read", {})
        with patch.object(self.store, "_audit", side_effect=RuntimeError("synthetic disk failure")):
            with self.assertRaises(RuntimeError):
                self.store.consume_request(request.request_id, {}, agent_id="fixture-owner")
        self.assertEqual("approved", self.store.get_request(request.request_id).status)
        self.assertEqual("consumed", self.store.consume_request(request.request_id, {}, agent_id="fixture-owner").status)


class DurableAuthorityRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "fixture.db"
        self.now = 1000
        self.store = self.open_store()
        self.store.register_agent("owner", 10001)
        self.store.register_service("fixture")
        self.store.register_capability("read", "fixture", "green", probation_allowed=True)
        self.store.grant_capability("owner", "read")

    def open_store(self):
        store = BrokerStore(self.path, clock=lambda: self.now)
        self.addCleanup(store.close)
        return store

    def test_two_connections_and_threads_consume_exactly_once(self):
        other = self.open_store()
        request = self.store.create_request("owner", "read", {})
        barrier = threading.Barrier(8)

        def consume(i):
            barrier.wait(timeout=5)
            try:
                (self.store if i % 2 else other).consume_request(request.request_id, {}, agent_id="owner")
                return "consumed"
            except BrokerDenied:
                return "denied"

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(consume, range(8)))
        self.assertEqual(1, results.count("consumed"))
        self.assertEqual(7, results.count("denied"))
        self.assertEqual(1, len(self.store.audit_search(event="request.consume")))

    def test_restart_retains_consumed_revoked_and_expired_states(self):
        consumed = self.store.create_request("owner", "read", {})
        revoked = self.store.create_request("owner", "read", {})
        expired = self.store.create_request("owner", "read", {}, ttl_seconds=1)
        valid = self.store.create_request("owner", "read", {})
        self.store.consume_request(consumed.request_id, {}, agent_id="owner")
        self.store.revoke_request(revoked.request_id)
        self.store.close()
        self.now += 1
        resumed = self.open_store()
        for record in (consumed, revoked, expired):
            with self.subTest(record=record), self.assertRaises(BrokerDenied):
                resumed.consume_request(record.request_id, {}, agent_id="owner")
        self.assertEqual("expired", resumed.get_request(expired.request_id).status)
        self.assertEqual("consumed", resumed.consume_request(valid.request_id, {}, agent_id="owner").status)

    def test_revocation_on_other_connection_is_effective(self):
        request = self.store.create_request("owner", "read", {})
        other = self.open_store()
        other.set_global_enabled(False)
        other.set_global_enabled(True)
        with self.assertRaises(BrokerDenied):
            self.store.consume_request(request.request_id, {}, agent_id="owner")

    def test_service_disable_enable_revokes_without_resurrection(self):
        request = self.store.create_request("owner", "read", {})
        self.store.set_service_enabled("fixture", False)
        self.store.set_service_enabled("fixture", True)
        with self.assertRaises(BrokerDenied):
            self.store.consume_request(request.request_id, {}, agent_id="owner")
        self.assertEqual("revoked", self.store.get_request(request.request_id).status)

    def test_noop_policy_updates_preserve_request(self):
        request = self.store.create_request("owner", "read", {})
        self.store.set_agent_state("owner", "probation")
        self.store.set_service_enabled("fixture", True)
        self.assertEqual(
            "consumed",
            self.store.consume_request(request.request_id, {}, agent_id="owner").status,
        )

    def test_lock_timeout_leaves_request_unconsumed(self):
        request = self.store.create_request("owner", "read", {})
        other = self.open_store()
        with other._transaction():
            with self.assertRaisesRegex(sqlite3.OperationalError, "locked"):
                self.store.consume_request(request.request_id, {}, agent_id="owner")
        self.assertEqual("approved", self.store.get_request(request.request_id).status)
        self.assertEqual(
            "consumed",
            self.store.consume_request(request.request_id, {}, agent_id="owner").status,
        )

    def test_process_exit_before_commit_rolls_back_claim(self):
        request = self.store.create_request("owner", "read", {})
        code = """
import os, sys
from broker_core import BrokerStore
s = BrokerStore(sys.argv[1], clock=lambda: 1000)
s._audit = lambda *args: os._exit(73)
s.consume_request(sys.argv[2], {}, agent_id='owner')
"""
        environment = dict(os.environ, PYTHONPATH=str(Path(__file__).parent.resolve()))
        child = subprocess.run(
            [sys.executable, "-c", code, str(self.path), request.request_id],
            env=environment,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(73, child.returncode, child.stderr)
        resumed = self.open_store()
        self.assertEqual("approved", resumed.get_request(request.request_id).status)
        self.assertEqual(
            "consumed",
            resumed.consume_request(request.request_id, {}, agent_id="owner").status,
        )

    def test_process_exit_after_commit_never_replays(self):
        request = self.store.create_request("owner", "read", {})
        code = """
import os, sys
from broker_core import BrokerStore
s = BrokerStore(sys.argv[1], clock=lambda: 1000)
s.consume_request(sys.argv[2], {}, agent_id='owner')
os._exit(74)
"""
        environment = dict(os.environ, PYTHONPATH=str(Path(__file__).parent.resolve()))
        child = subprocess.run(
            [sys.executable, "-c", code, str(self.path), request.request_id],
            env=environment,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(74, child.returncode, child.stderr)
        resumed = self.open_store()
        with self.assertRaises(BrokerDenied):
            resumed.consume_request(request.request_id, {}, agent_id="owner")
        self.assertEqual("consumed", resumed.get_request(request.request_id).status)

    def test_approval_and_revocation_cannot_resurrect_request(self):
        self.store.set_agent_state("owner", "operator")
        self.store.register_capability("change", "fixture", "yellow")
        self.store.grant_capability("owner", "change")
        request = self.store.create_request("owner", "change", {})
        other = self.open_store()
        barrier = threading.Barrier(2)

        def approve():
            barrier.wait(timeout=5)
            try:
                self.store.approve_request(request.request_id, request.payload_hash)
            except BrokerDenied:
                pass

        def revoke():
            barrier.wait(timeout=5)
            other.revoke_request(request.request_id)

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(approve), pool.submit(revoke)]
            for future in futures:
                future.result(timeout=10)
        self.assertEqual("revoked", self.store.get_request(request.request_id).status)

    def test_expired_approval_denial_commits_terminal_state(self):
        self.store.set_agent_state("owner", "operator")
        self.store.register_capability("change", "fixture", "yellow")
        self.store.grant_capability("owner", "change")
        request = self.store.create_request("owner", "change", {}, ttl_seconds=1)
        self.now += 1
        with self.assertRaises(BrokerDenied):
            self.store.approve_request(request.request_id, request.payload_hash)
        self.assertEqual("expired", self.store.get_request(request.request_id).status)

    def test_isolated_database_restore_preserves_replay_denial(self):
        request = self.store.create_request("owner", "read", {})
        self.store.consume_request(request.request_id, {}, agent_id="owner")
        restore_path = Path(self.temp.name) / "restored.db"
        with sqlite3.connect(restore_path) as snapshot:
            self.store.connection.backup(snapshot)
        restored = BrokerStore(restore_path, clock=lambda: self.now)
        self.addCleanup(restored.close)
        self.assertEqual("ok", restored.connection.execute("PRAGMA integrity_check").fetchone()[0])
        with self.assertRaises(BrokerDenied):
            restored.consume_request(request.request_id, {}, agent_id="owner")

    def test_concurrent_start_migrates_legacy_schema_once(self):
        legacy = self.store.create_request("owner", "read", {})
        self.store.close()
        # Match the previous requests table without assuming SQLite supports
        # DROP COLUMN. This fixture contains no credentials or external state.
        with sqlite3.connect(self.path) as database:
            database.executescript("""
                ALTER TABLE requests RENAME TO old_requests;
                CREATE TABLE requests AS SELECT request_id,agent_id,capability,
                    risk_class,payload_hash,status,created_at,expires_at,approved_at,
                    consumed_at,revoked_at,approval_actor,approval_auth_time,
                    approval_assurance,display_json FROM old_requests;
                DROP TABLE old_requests;
            """)
        barrier = threading.Barrier(8)

        def start(_):
            barrier.wait(timeout=5)
            store = BrokerStore(self.path, clock=lambda: self.now)
            try:
                with self.assertRaises(BrokerDenied):
                    store.consume_request(legacy.request_id, {}, agent_id="owner")
                return store.connection.execute("PRAGMA integrity_check").fetchone()[0]
            finally:
                store.close()

        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(["ok"] * 8, list(pool.map(start, range(8))))


if __name__ == "__main__":
    unittest.main()
