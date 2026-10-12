import os
import sqlite3
import tempfile
import unittest

from store import DispatchStore


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.directory.name, "jobs.sqlite")
        self.store = DispatchStore(self.path)

    def tearDown(self):
        self.store.close()
        self.directory.cleanup()

    def test_restart_does_not_repeat_uncertain_dispatch(self):
        self.assertTrue(self.store.claim("j"))
        self.store.close()
        self.store = DispatchStore(self.path)
        self.assertFalse(self.store.claim("j"))
        self.assertEqual(self.store.inspect("j"), ("dispatch_unknown", None, None))

    def test_two_connections_cannot_claim_same_work(self):
        second = DispatchStore(self.path)
        try:
            self.assertTrue(self.store.claim("j"))
            self.assertFalse(second.claim("j"))
        finally:
            second.close()

    def test_binding_cannot_be_replaced(self):
        self.store.claim("j")
        self.store.bind("j", "t", "u")
        with self.assertRaises(ValueError):
            self.store.bind("j", "other", "other")
        with self.assertRaises(ValueError):
            self.store.bind("missing", "t", "u")

    def test_wrong_terminal_event_does_not_complete_job(self):
        self.store.claim("j"); self.store.bind("j", "t", "u")
        with self.assertRaises(ValueError):
            self.store.finish("j", "t", "wrong", "completed")
        self.assertEqual(self.store.inspect("j"), ("running", "t", "u"))

    def test_completion_is_durable_and_never_releases_claim(self):
        self.store.claim("j"); self.store.bind("j", "t", "u")
        self.store.finish("j", "t", "u", "completed")
        self.store.close(); self.store = DispatchStore(self.path)
        self.assertEqual(self.store.inspect("j"), ("completed", "t", "u"))
        self.assertFalse(self.store.claim("j"))
        with self.assertRaises(ValueError):
            self.store.finish("j", "t", "u", "failed")

    def test_failure_category_is_bounded_owner_scoped_and_durable(self):
        self.store.claim("j", "t", "owner-a")
        self.store.bind("j", "t", "u")
        with self.assertRaises(ValueError):
            self.store.finish("j", "t", "u", "failed", failure_class="private provider error")
        with self.assertRaises(ValueError):
            self.store.finish("j", "t", "u", "completed", failure_class="subscription_limit")
        self.assertEqual(self.store.inspect("j"), ("running", "t", "u"))
        self.store.finish("j", "t", "u", "failed", failure_class="subscription_limit")
        self.store.close(); self.store = DispatchStore(self.path)
        self.assertEqual(self.store.failure_class("j", "owner-a"), "subscription_limit")
        self.assertIsNone(self.store.failure_class("j", "owner-b"))
        self.assertFalse(self.store.claim("j", "t", "owner-a"))

    def test_existing_job_table_migrates_without_releasing_claims(self):
        self.store.close()
        database = sqlite3.connect(self.path)
        database.execute("DROP TABLE jobs")
        database.execute("""CREATE TABLE jobs (
            job_id TEXT PRIMARY KEY, state TEXT NOT NULL,
            thread_id TEXT, turn_id TEXT, owner TEXT)""")
        database.execute("INSERT INTO jobs VALUES ('old','unknown','thread','turn','owner-a')")
        database.commit(); database.close()
        self.store = DispatchStore(self.path)
        self.assertEqual(self.store.inspect("old"), ("unknown", "thread", "turn"))
        self.assertFalse(self.store.claim("old", "thread", "owner-a"))
        self.assertIsNone(self.store.failure_class("old", "owner-a"))
