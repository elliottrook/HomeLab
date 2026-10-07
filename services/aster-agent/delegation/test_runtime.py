import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime import open_runtime
from store import DispatchStore
from test_usage_companion import usage


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)/'state'
        self.runtime = None

    def tearDown(self):
        if self.runtime:
            self.runtime.close()
        self.tmp.cleanup()

    def test_disabled_creates_nothing(self):
        self.assertIsNone(open_runtime(self.path))
        self.assertFalse(self.path.exists())

    def test_owner_permissions_and_second_worker_denial(self):
        self.runtime = open_runtime(self.path, enabled=True)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.path/'jobs.sqlite').stat().st_mode & 0o777, 0o600)
        with self.assertRaises(BlockingIOError):
            open_runtime(self.path, enabled=True)

    def test_crash_marks_unfinished_work_unknown_without_replay(self):
        code = """import os,sys
from runtime import open_runtime
r=open_runtime(sys.argv[1],enabled=True)
r.store.claim('j','t','owner');r.store.bind('j','t','u')
os._exit(0)
"""
        subprocess.run([sys.executable, '-c', code, str(self.path)],
                       cwd=Path(__file__).parent, check=True, timeout=10)
        self.runtime = open_runtime(self.path, enabled=True)
        self.assertEqual(self.runtime.store.inspect('j'), ('unknown','t','u'))
        self.assertFalse(self.runtime.store.claim('j','t','owner'))

    def test_shutdown_does_not_claim_remote_cancellation(self):
        self.runtime = open_runtime(self.path, enabled=True)
        self.runtime.store.claim('j','t');self.runtime.store.bind('j','t','u')
        self.runtime.close()
        self.runtime = open_runtime(self.path, enabled=True)
        self.assertEqual(self.runtime.store.inspect('j')[0], 'unknown')

    def test_completed_state_survives_restart(self):
        self.runtime = open_runtime(self.path, enabled=True)
        self.runtime.store.claim('j','t');self.runtime.store.bind('j','t','u')
        self.runtime.store.finish('j','t','u','completed')
        self.runtime.close();self.runtime = open_runtime(self.path, enabled=True)
        self.assertEqual(self.runtime.store.inspect('j')[0], 'completed')

    def test_insecure_or_symlink_state_refused(self):
        self.path.mkdir(mode=0o755)
        os.chmod(self.path,0o755)
        with self.assertRaises(ValueError): open_runtime(self.path,enabled=True)
        link = Path(self.tmp.name)/'link';link.symlink_to(self.path)
        with self.assertRaises(ValueError): open_runtime(link,enabled=True)

    def test_capacity_fails_closed_without_releasing_old_ids(self):
        store = DispatchStore(Path(self.tmp.name)/'bounded.sqlite', max_jobs=1)
        try:
            self.assertTrue(store.claim('one'))
            self.assertFalse(store.claim('one'))
            with self.assertRaises(ValueError): store.claim('two')
        finally: store.close()

    def test_usage_expires_but_dispatch_identity_remains(self):
        self.runtime = open_runtime(self.path, enabled=True)
        store = self.runtime.store
        store.claim('j','t');store.bind('j','t','u')
        with patch('store.time.time',return_value=100000):
            store.note_usage('j','t','u',usage())
            self.assertIsNotNone(store.usage('j'))
        with patch('store.time.time',return_value=200000):
            self.assertIsNone(store.usage('j'))
            store.prune_usage()
            self.assertFalse(store.claim('j'))
        self.assertEqual(store.db.execute('SELECT count(*) FROM job_usage').fetchone()[0],0)

    def test_identifier_bounds_prevent_oversized_retained_metadata(self):
        self.runtime = open_runtime(self.path, enabled=True)
        store = self.runtime.store
        with self.assertRaises(ValueError): store.claim('j','x'*129)
        store.claim('j','t')
        with self.assertRaises(ValueError): store.bind('j','t','x'*129)
        self.assertEqual(store.inspect('j'), ('dispatch_unknown','t',None))
