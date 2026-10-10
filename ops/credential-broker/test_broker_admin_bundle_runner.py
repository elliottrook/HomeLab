import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from broker_core import BrokerDenied, BrokerStore


class BundleRunnerAdminTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "broker.db"
        self.store = BrokerStore(self.database, clock=lambda: 2_000_000_000)
        self.store.register_agent("agent-hermes", os.getuid())
        self.store.register_service("forgejo-mcp-safe-write")
        self.store.register_capability("forgejo.write.safe-branch", "forgejo-mcp-safe-write", "yellow")
        self.store.close()

    def tearDown(self):
        self.temp.cleanup()

    def run_admin(self, uid):
        return subprocess.run(
            [sys.executable, "broker_admin.py", "--database", str(self.database),
             "enable-forgejo-bundle-runner", "--agent-uid", str(uid)],
            cwd=Path(__file__).parent, text=True, capture_output=True,
        )

    def test_onboards_only_probationary_payload_bound_agent(self):
        uid = os.getuid() + 1000
        result = self.run_admin(uid)
        self.assertEqual(0, result.returncode, result.stderr)
        store = BrokerStore(self.database, clock=lambda: 2_000_000_000)
        self.assertEqual("agent-cloud-bundle", store.agent_for_uid(uid))
        with self.assertRaisesRegex(BrokerDenied, "probation"):
            store.create_request("agent-cloud-bundle", "forgejo.write.safe-branch", {})
        store.close()

    def test_uid_mismatch_fails_closed(self):
        uid = os.getuid() + 1000
        self.assertEqual(0, self.run_admin(uid).returncode)
        changed = self.run_admin(uid + 1)
        self.assertNotEqual(0, changed.returncode)
        self.assertIn("does not match", changed.stderr)


if __name__ == "__main__":
    unittest.main()
