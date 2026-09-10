import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from broker import Candidate
from state import store_candidates


SCRIPT = Path(__file__).with_name("approve.py")
REF = "radarr-q-abcdefghijklmnop"


class ApprovalCommandTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        now = datetime.now(timezone.utc)
        store_candidates(
            self.root / "candidates.json",
            [Candidate(REF, 42, now, now + timedelta(minutes=5))],
        )
        self.environment = {
            **os.environ,
            "ASTER_ARR_BROKER_STATE_ROOT": str(self.root),
            "PYTHONDONTWRITEBYTECODE": "1",
        }

    def tearDown(self):
        self.directory.cleanup()

    def run_command(self, *arguments):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            env=self.environment,
            capture_output=True,
            check=False,
            text=True,
        )

    def test_nonreversible_acceptance_is_mandatory(self):
        result = self.run_command("--candidate-ref", REF)
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / "approvals.json").exists())

    def test_approved_output_is_bounded_and_approval_secret_stays_server_side(self):
        result = self.run_command("--candidate-ref", REF, "--accept-nonreversible")
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(
            set(output),
            {"status", "operation", "candidate_ref", "expires_at", "nonreversible_accepted"},
        )
        self.assertEqual(output["candidate_ref"], REF)
        self.assertNotIn("approval-", result.stdout)
        self.assertIn("approval-", (self.root / "approvals.json").read_text())

    def test_unknown_candidate_is_refused_without_detail(self):
        result = self.run_command(
            "--candidate-ref", "radarr-q-ponmlkjihgfedcba", "--accept-nonreversible"
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout), {"status": "refused"})


if __name__ == "__main__":
    unittest.main()
