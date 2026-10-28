import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from netbox_incident_adapter import read_netbox_observation


NOW = datetime(2026, 10, 28, 21, 0, tzinfo=timezone.utc)


def report():
    return {
        "schema_version": 1,
        "source": "netbox",
        "generated_at": "2026-10-28T20:59:00Z",
        "instance": {"version": "fixture"},
        "inventory": {
            "counts": {
                "devices": 2, "virtual_machines": 3, "sites": 1,
                "racks": 1, "vlans": 4, "prefixes": 5,
            },
            "devices": [{
                "name": "private-switch", "status": "active", "role": "switch",
                "type": "private-type", "site": "private-site", "location": None,
                "rack": "private-rack", "position": "1", "primary_ip4": "192.0.2.1/24",
            }],
            "virtual_machines": [{
                "name": "private-vm", "status": "active", "role": None,
                "cluster": "private-cluster", "site": "private-site",
                "primary_ip4": "192.0.2.2/24",
            }],
            "vlans": [{"vid": 10, "name": "private-vlan", "status": "active", "site": "private-site"}],
            "prefixes": [{"prefix": "192.0.2.0/24", "status": "active", "vlan": "private-vlan", "site": "private-site"}],
        },
    }


class NetBoxIncidentAdapterTests(unittest.TestCase):
    def read(self, value):
        return read_netbox_observation(
            "incident-netbox-fixture", Path("/fixed/netbox.json"), NOW,
            reader=lambda path, now: value,
        )

    def test_inventory_is_aggregate_without_private_identity(self):
        observation = self.read(report())
        self.assertEqual(("netbox-main", "network", "ok"), (
            observation.target, observation.kind, observation.state,
        ))
        self.assertEqual(2, observation.facts["device_count"])
        self.assertEqual(3, observation.facts["virtual_machine_count"])
        self.assertEqual(24, len(observation.facts["report_digest"]))
        encoded = json.dumps(observation.__dict__)
        for private in (
            "private-switch", "private-type", "private-site", "private-rack",
            "private-vm", "private-cluster", "private-vlan", "192.0.2",
        ):
            self.assertNotIn(private, encoded)

    def test_unavailable_report_is_content_free(self):
        observation = self.read({
            "status": "unavailable", "source": "netbox",
            "error": "private path or validation detail",
        })
        self.assertEqual("unavailable", observation.state)
        self.assertEqual({"reason": "source_unavailable"}, observation.facts)
        self.assertNotIn("private", json.dumps(observation.__dict__))


if __name__ == "__main__":
    unittest.main()
