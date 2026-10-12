import importlib.util, json, subprocess, unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("ha_producer", Path(__file__).with_name("produce-aster-ha-report.py"))
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)

class ProducerTests(unittest.TestCase):
    @patch.object(MODULE.subprocess, "run")
    def test_guest_uses_absolute_qm_path_for_cron(self, run):
        run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=json.dumps({"exitcode": 0, "out-data": json.dumps({"result": "ok", "data": {}})}),
        )
        self.assertEqual(MODULE.guest(["core", "info"]), {})
        self.assertEqual(run.call_args.args[0][:4],
                         ["/usr/sbin/qm", "guest", "exec", "103"])

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
