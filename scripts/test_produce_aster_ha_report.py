import importlib.util, unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("ha_producer", Path(__file__).with_name("produce-aster-ha-report.py"))
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)

class ProducerTests(unittest.TestCase):
    @patch.object(MODULE, "guest")
    def test_build_is_aggregate_and_excludes_names(self, guest):
        guest.side_effect = [
            {"boot": True, "version": "1", "version_latest": "1", "update_available": False, "watchdog": True, "secret": "x"},
            {"healthy": True, "supported": True, "version": "2", "version_latest": "2", "update_available": False, "addons": [{"name": "private"}]},
            {"mounts": [{"usage": "backup", "state": "active", "server": "private"}]},
            {"unsupported": [], "unhealthy": [], "issues": [{"context": "private"}], "suggestions": []},]
        report = MODULE.build(); rendered = str(report)
        self.assertTrue(report["backup"]["mount_active"])
        for private in ("secret", "private", "addons", "server", "context"): self.assertNotIn(private, rendered)
