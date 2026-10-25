import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sa3_development_execute import main, run_spec


class DevelopmentExecuteTests(unittest.TestCase):
    def setUp(self):
        self.here = Path(__file__).parent
        self.fixtures = self.here / "sysadmin-sa3-development-fixtures-draft-v1.json"
        self.source = self.here / "sysadmin-incident-development-extension-draft-v1.json"
        self.plan = self.here / "sysadmin-incident-development-plan-v1.json"

    def test_dry_run_is_qualified_content_free_and_credential_free(self):
        command = [sys.executable, str(self.here / "sa3_development_execute.py")]
        result = subprocess.run(command, env={}, capture_output=True, text=True, check=True)
        value = json.loads(result.stdout)
        self.assertEqual(value["status"], "dry_run_valid")
        self.assertEqual(value["run_spec"]["cases"], 12)
        self.assertEqual(value["run_spec"]["sessions"], 12)
        self.assertEqual(value["run_spec"]["maximum_model_calls"], 36)
        self.assertEqual(value["run_spec"]["request_timeout_seconds"], 60)
        self.assertEqual(value["run_spec"]["mode"], "nonthinking")
        self.assertFalse(value["run_spec"]["connected_tools"])
        self.assertFalse(value["run_spec"]["effects"])
        self.assertEqual(len(value["run_spec"]["implementation_sha256"]), 7)
        self.assertTrue(all(
            len(item) == 64
            for item in value["run_spec"]["implementation_sha256"].values()
        ))
        self.assertFalse(value["keys_accessed"])

    def test_run_spec_is_bound_to_fixture_and_sources(self):
        spec = run_spec(self.fixtures, self.source, self.plan)
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / "fixtures.json"
            changed.write_bytes(self.fixtures.read_bytes() + b" ")
            self.assertNotEqual(
                spec["fixture_file_sha256"],
                run_spec(changed, self.source, self.plan)["fixture_file_sha256"],
            )

    def test_execute_requires_exact_digest_before_authentication(self):
        with self.assertRaisesRegex(SystemExit, "approved digest"):
            main(["--execute", "--expected-run-digest", "0" * 64])


if __name__ == "__main__":
    unittest.main()
