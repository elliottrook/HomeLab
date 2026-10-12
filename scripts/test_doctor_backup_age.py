"""Exercise Doctor's guest-backup age gates with synthetic remote results."""

import os
from pathlib import Path
import subprocess
import time
import unittest


SOURCE = Path(__file__).with_name("doctor.sh").read_text()
FUNCTIONS = SOURCE[
    SOURCE.index("check_proxmox_guest_backup_age() {"):
    SOURCE.index("check_aster() {")
]


class GuestBackupAgeDoctorTests(unittest.TestCase):
    def run_check(self, function, epoch, guest_type="lxc"):
        script = r'''set -u
ssh() { printf '%s\n' "$FIXTURE"; }
pass() { printf 'PASS %s\n' "$1"; }
warn() { printf 'WARN %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1"; }
''' + FUNCTIONS + f'\n{function} "Aster Speech LXC 116" 116 30 {guest_type}\n'
        result = subprocess.run(
            ["/bin/bash", "-c", script],
            text=True,
            capture_output=True,
            env=dict(os.environ, FIXTURE=epoch),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_fresh_proxmox_archive_passes(self):
        output = self.run_check(
            "check_proxmox_guest_backup_age", str(time.time() - 6 * 3600)
        )
        self.assertIn("PASS Aster Speech LXC 116 Proxmox backup is 6 hour(s) old", output)

    def test_stale_proxmox_archive_fails(self):
        output = self.run_check(
            "check_proxmox_guest_backup_age", str(time.time() - 31 * 3600)
        )
        self.assertIn("FAIL Aster Speech LXC 116 Proxmox backup is 31 hour(s) old", output)

    def test_missing_proxmox_archive_fails(self):
        output = self.run_check("check_proxmox_guest_backup_age", "")
        self.assertIn("FAIL Aster Speech LXC 116 has no Proxmox backup archive", output)

    def test_future_proxmox_timestamp_warns(self):
        output = self.run_check(
            "check_proxmox_guest_backup_age", str(time.time() + 3600)
        )
        self.assertIn("WARN Aster Speech LXC 116 backup timestamp is ahead", output)

    def test_fresh_truenas_mirror_passes(self):
        output = self.run_check(
            "check_truenas_guest_mirror_age", str(time.time() - 6 * 3600)
        )
        self.assertIn("PASS Aster Speech LXC 116 TrueNAS mirror is 6 hour(s) old", output)

    def test_stale_truenas_mirror_fails(self):
        output = self.run_check(
            "check_truenas_guest_mirror_age", str(time.time() - 31 * 3600)
        )
        self.assertIn("FAIL Aster Speech LXC 116 TrueNAS mirror is 31 hour(s) old", output)


if __name__ == "__main__":
    unittest.main()
