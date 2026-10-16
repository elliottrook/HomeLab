"""Regression tests for bounded Doctor infrastructure checks."""

import os
from pathlib import Path
import subprocess
import time
import unittest


SOURCE = Path(__file__).with_name("doctor.sh").read_text()
OBSERVABILITY = SOURCE[
    SOURCE.index("check_observability() {") : SOURCE.index("check_truenas() {")
]
FRIGATE = SOURCE[SOURCE.index("check_frigate() {") : SOURCE.index("check_unifi() {")]
JELLYFIN = SOURCE[
    SOURCE.index("check_jellyfin_integrity() {") : SOURCE.index("check_netbox() {")
]


class DoctorInfrastructureTests(unittest.TestCase):
    def run_check(self, function, name, fixture):
        script = """set -u
ssh() { cat >/dev/null; printf '%s\\n' "$FIXTURE"; }
pass() { printf 'PASS %s\\n' "$1"; }
warn() { printf 'WARN %s\\n' "$1"; }
fail() { printf 'FAIL %s\\n' "$1"; }
""" + function + f"\n{name}\n"
        result = subprocess.run(
            ["/bin/bash", "-c", script],
            text=True,
            capture_output=True,
            env=dict(os.environ, FIXTURE=fixture),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_observability_accepts_current_nine_target_inventory(self):
        fixture = "\n".join(
            [
                "services=active active active active active active ",
                "grafana_db=ok",
                "prometheus_ready=Prometheus_Server_is_Ready.",
                "targets_up=9",
                "targets_total=9",
                "root_percent=42",
            ]
        )
        self.assertIn("PASS Prometheus, Grafana and exporters healthy; 9/9", self.run_check(OBSERVABILITY, "check_observability", fixture))

    def test_observability_rejects_extra_or_unhealthy_target(self):
        fixture = "\n".join(
            [
                "services=active active active active active active ",
                "grafana_db=ok",
                "prometheus_ready=Prometheus_Server_is_Ready.",
                "targets_up=9",
                "targets_total=10",
                "root_percent=42",
            ]
        )
        self.assertIn("FAIL Observability health issue: configured scrape jobs=10/9", self.run_check(OBSERVABILITY, "check_observability", fixture))

    def test_frigate_accepts_fresh_recording_fixture(self):
        fixture = "\n".join(
            [
                "service=active",
                "mount_source=192.168.20.40:/mnt/Media/Surveillance/Frigate",
                "mount_type=nfs4",
                f"newest_recording={time.time():.6f}",
            ]
        )
        self.assertIn("PASS Frigate service, NFS storage and recording flow healthy", self.run_check(FRIGATE, "check_frigate", fixture))

    def test_frigate_scan_is_bounded_to_recent_date_directories(self):
        self.assertIn('"$root/$(date +%F)"', FRIGATE)
        self.assertIn('"$root/$(date -d yesterday +%F)"', FRIGATE)
        self.assertIn('find "$day_dir" -mindepth 1 -maxdepth 1', FRIGATE)
        self.assertIn('find "$hour_dir" -mindepth 2 -maxdepth 2', FRIGATE)
        self.assertNotIn("find /opt/frigate/storage/recordings -type f", FRIGATE)

    def test_jellyfin_integrity_reports_invalid_key_as_failure(self):
        fixture = "\n".join(
            [
                "jellyfin_auth=failed",
                "report_path=/fixture/run.json",
                f"mtime={int(time.time())}",
                "mode=apply",
                "errors=0",
                "alerts=0",
                "drift=0",
            ]
        )
        output = self.run_check(JELLYFIN, "check_jellyfin_integrity", fixture)
        self.assertIn("FAIL jellyfin-integrity cannot authenticate to Jellyfin", output)


if __name__ == "__main__":
    unittest.main()
