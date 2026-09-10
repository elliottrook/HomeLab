import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import importlib.util

MODULE_PATH = Path(__file__).with_name("refresh-aster-source-reports.py")
SPEC = importlib.util.spec_from_file_location("refresh_source_reports", MODULE_PATH)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class TransportTests(unittest.TestCase):
    def test_transport_uses_fixed_pct_targets_and_never_handles_tokens(self):
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        report = {
            "schema_version": 1, "source": "forgejo", "generated_at": now,
            "instance": {"version": "15.0.7"},
            "repositories": [{"owner": "jason", "name": "homelab", "visibility": "private", "archived": False, "default_branch": "main", "updated_at": now, "counts": {"branches": 1, "tags": 0, "releases": 0, "open_issues": 0, "open_pulls": 0}, "latest_commit": None, "latest_action": None}],
        }
        calls = []
        def fake_run(*command):
            calls.append(command)
            if command[:3] == ("pct", "pull", "108"):
                Path(command[-1]).write_text(json.dumps(report), encoding="utf-8")
                Path(command[-1]).chmod(0o600)
        with tempfile.TemporaryDirectory() as directory, patch.object(module, "run", side_effect=fake_run):
            module.refresh_source("forgejo", Path(directory))
        flattened = " ".join(" ".join(call) for call in calls)
        self.assertIn("pct exec 108 -- systemctl start aster-forgejo-report.service", flattened)
        self.assertIn("pct push 104", flattened)
        self.assertNotIn("token", flattened.casefold())
        self.assertNotIn("api", flattened.casefold())

    def test_invalid_source_report_is_not_pushed(self):
        calls = []
        def fake_run(*command):
            calls.append(command)
            if command[:3] == ("pct", "pull", "108"):
                Path(command[-1]).write_text('{"secret":"raw"}', encoding="utf-8")
                Path(command[-1]).chmod(0o600)
        with tempfile.TemporaryDirectory() as directory, patch.object(module, "run", side_effect=fake_run):
            with self.assertRaises(ValueError):
                module.refresh_source("forgejo", Path(directory))
        self.assertFalse(any(call[:3] == ("pct", "push", "104") for call in calls))


if __name__ == "__main__":
    unittest.main()
