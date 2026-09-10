import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "aster-agent"))


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


forgejo = load("forgejo_report")
netbox = load("netbox_report")
NOW = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)


class ProducerTests(unittest.TestCase):
    def test_netbox_accepts_only_expected_token_header_forms(self):
        with tempfile.TemporaryDirectory() as directory:
            token_path = Path(directory) / "token"
            token_path.write_text("Bearer nbt_key.secret\n", encoding="utf-8")
            with patch.object(netbox, "TOKEN_PATH", token_path):
                self.assertEqual(netbox._token(), "Bearer nbt_key.secret")
            token_path.write_text("Bearer valid\nInjected: value\n", encoding="utf-8")
            with patch.object(netbox, "TOKEN_PATH", token_path), self.assertRaises(ValueError):
                netbox._token()

    def test_forgejo_report_excludes_repository_content(self):
        def fake_get(path, token):
            headers = {"x-total-count": "1"}
            if path == "/api/v1/version": return {"version": "15.0.7"}, {}
            if path.endswith("/actions/runs?limit=1&page=1"):
                return {"workflow_runs": [{"status": "completed", "conclusion": "success", "created_at": "2026-09-09T11:00:00Z", "logs": "secret"}]}, {}
            if path.endswith("/commits?limit=50&page=1"):
                return [{"sha": "abcdef0123456789", "commit": {"message": "secret", "committer": {"date": "2026-09-09T11:30:00Z", "email": "secret@example"}}}], headers
            if "?" in path: return [{"title": "secret", "body": "secret"}], headers
            return {"private": True, "archived": False, "default_branch": "main", "updated_at": "2026-09-09T11:45:00Z", "description": "secret"}, {}

        with patch.object(forgejo, "_token", return_value="opaque"), patch.object(forgejo, "_get", side_effect=fake_get):
            report = forgejo.build_report(NOW)
        encoded = json.dumps(report)
        for excluded in ("message", "email", "title", "body", "logs", "description"):
            self.assertNotIn(excluded, encoded)
        self.assertEqual(report["repositories"][0]["latest_commit"]["sha"], "abcdef012345")

    def test_netbox_report_excludes_sensitive_inventory_fields(self):
        collections = {
            "/api/dcim/devices/": [{"name": "switch", "status": {"value": "active"}, "role": {"name": "switch"}, "device_type": {"model": "7050"}, "site": {"name": "Home"}, "location": None, "rack": {"name": "Lab"}, "position": 10.5, "primary_ip4": {"address": "192.0.2.1/24"}, "config_context": {"password": "secret"}, "custom_fields": {"key": "secret"}}],
            "/api/virtualization/virtual-machines/": [], "/api/ipam/vlans/": [],
            "/api/ipam/prefixes/": [], "/api/dcim/sites/": [{}], "/api/dcim/racks/": [{}],
        }
        def fake_get(path, token):
            if path == "/api/status/": return {"netbox-version": "4.6.9"}
            base = path.split("?", 1)[0]
            items = collections[base]
            return {"count": len(items), "next": None, "results": items}
        with patch.object(netbox, "_token", return_value="opaque"), patch.object(netbox, "_get", side_effect=fake_get):
            report = netbox.build_report(NOW)
        encoded = json.dumps(report)
        for excluded in ("config_context", "custom_fields", "password"):
            self.assertNotIn(excluded, encoded)
        self.assertEqual(report["inventory"]["devices"][0]["position"], "10.5")

    def test_atomic_writer_rejects_invalid_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "latest.json"
            with self.assertRaises(ValueError):
                forgejo.write_report({"secret": "not a report"}, path)
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
