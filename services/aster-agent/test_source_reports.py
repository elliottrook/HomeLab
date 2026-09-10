import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from source_reports import get_forgejo_report, get_netbox_report


NOW = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)


def forgejo_report():
    return {
        "schema_version": 1,
        "source": "forgejo",
        "generated_at": "2026-09-09T12:00:00Z",
        "instance": {"version": "15.0.7"},
        "repositories": [{
            "owner": "jason", "name": "homelab", "visibility": "private",
            "archived": False, "default_branch": "main",
            "updated_at": "2026-09-09T11:59:00Z",
            "counts": {"branches": 2, "tags": 1, "releases": 0, "open_issues": 3, "open_pulls": 1},
            "latest_commit": {"sha": "abcdef012345", "committed_at": "2026-09-09T11:58:00Z"},
            "latest_action": {"status": "completed", "conclusion": "success", "started_at": "2026-09-09T11:57:00Z"},
        }],
    }


def netbox_report():
    return {
        "schema_version": 1,
        "source": "netbox",
        "generated_at": "2026-09-09T12:00:00Z",
        "instance": {"version": "4.6.9"},
        "inventory": {
            "counts": {"devices": 1, "virtual_machines": 1, "sites": 1, "racks": 1, "vlans": 1, "prefixes": 1},
            "devices": [{"name": "switch", "status": "active", "role": "switch", "type": "7050", "site": "Home", "location": None, "rack": "Lab", "position": "10.0", "primary_ip4": "192.0.2.1/24"}],
            "virtual_machines": [{"name": "aster", "status": "active", "role": None, "cluster": "Proxmox", "site": "Home", "primary_ip4": "192.0.2.2/24"}],
            "vlans": [{"vid": 20, "name": "Servers", "status": "active", "site": "Home"}],
            "prefixes": [{"prefix": "192.0.2.0/24", "status": "active", "vlan": "Servers", "site": "Home"}],
        },
    }


class SourceReportTests(unittest.TestCase):
    def read(self, source, payload, *, now=NOW, mode=0o600):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            path.chmod(mode)
            reader = get_forgejo_report if source == "forgejo" else get_netbox_report
            return reader(path, now=now, required_uid=os.getuid())

    def test_accepts_exact_forgejo_schema(self):
        self.assertEqual(self.read("forgejo", forgejo_report())["source"], "forgejo")

    def test_accepts_exact_netbox_schema(self):
        self.assertEqual(self.read("netbox", netbox_report())["source"], "netbox")

    def test_rejects_stale_and_future_reports(self):
        for offset in (-901, 61):
            payload = forgejo_report()
            payload["generated_at"] = (NOW + timedelta(seconds=offset)).isoformat()
            self.assertEqual(self.read("forgejo", payload)["status"], "unavailable")

    def test_rejects_unknown_or_sensitive_fields(self):
        cases = []
        forgejo = forgejo_report()
        forgejo["repositories"][0]["commit_message"] = "secret text"
        cases.append(("forgejo", forgejo))
        netbox = netbox_report()
        netbox["inventory"]["devices"][0]["config_context"] = {"password": "secret"}
        cases.append(("netbox", netbox))
        for source, payload in cases:
            self.assertEqual(self.read(source, payload)["status"], "unavailable")

    def test_rejects_group_writable_report(self):
        self.assertEqual(self.read("forgejo", forgejo_report(), mode=0o620)["status"], "unavailable")

    def test_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target.json"
            link = Path(directory) / "report.json"
            target.write_text(json.dumps(forgejo_report()), encoding="utf-8")
            link.symlink_to(target)
            self.assertEqual(get_forgejo_report(link, now=NOW, required_uid=os.getuid())["status"], "unavailable")

    def test_rejects_invalid_commit_and_vlan(self):
        forgejo = forgejo_report()
        forgejo["repositories"][0]["latest_commit"]["sha"] = "not-a-sha"
        self.assertEqual(self.read("forgejo", forgejo)["status"], "unavailable")
        netbox = netbox_report()
        netbox["inventory"]["vlans"][0]["vid"] = 5000
        self.assertEqual(self.read("netbox", netbox)["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
