#!/usr/bin/env python3
"""Static regression gates for the Bedroom Wi-Fi stability unit."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent
UNIT = (ROOT / "astertv-wifi-stability.service").read_text()
README = (ROOT / "README.md").read_text()


class WifiStabilityUnitTests(unittest.TestCase):
    def test_is_host_and_interface_bound(self):
        self.assertIn("ConditionHost=AsterTV-Bedroom", UNIT)
        self.assertIn("ConditionPathExists=/sys/class/net/wlan0", UNIT)

    def test_runs_after_network_and_before_kodi(self):
        self.assertIn("After=connman.service network-online.target", UNIT)
        self.assertIn("Before=kodi.service", UNIT)

    def test_only_changes_wifi_power_save(self):
        self.assertIn(
            "ExecStart=/usr/sbin/iw dev wlan0 set power_save off", UNIT
        )
        self.assertIn(
            "ExecStop=/usr/sbin/iw dev wlan0 set power_save on", UNIT
        )
        self.assertNotIn("ExecStart=/bin/sh", UNIT)
        self.assertNotIn("ExecStart=/bin/bash", UNIT)

    def test_rollback_and_installed_hash_are_documented(self):
        self.assertIn("systemctl disable --now astertv-wifi-stability.service", README)
        self.assertIn(
            "6a829d42832076bb8ec2756c5cd577939af8ab0a900462376c5dbb98ab1f6b90",
            README,
        )


if __name__ == "__main__":
    unittest.main()
