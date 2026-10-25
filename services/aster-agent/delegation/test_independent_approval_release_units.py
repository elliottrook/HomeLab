"""Static safety checks for permanent Yellow-only approval-plane units."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parent / "deploy"
INGRESS = (ROOT / "aster-approval-ingress.service.release").read_text()
BROKER = (ROOT / "homelab-broker-approval-independent.service.release").read_text()


class IndependentApprovalReleaseUnitTests(unittest.TestCase):
    def test_units_are_explicitly_boot_enabled_candidates(self):
        for text in (INGRESS, BROKER):
            self.assertRegex(text, r"(?ms)^\[Install\]\nWantedBy=multi-user\.target$")
            self.assertTrue(text.endswith("\n"))

    def test_broker_conflicts_with_old_ai_facing_approval_service(self):
        self.assertRegex(BROKER, r"(?m)^Conflicts=homelab-broker-approval\.service$")
        self.assertRegex(BROKER, r"(?m)^Before=aster-approval-ingress\.service$")
        self.assertNotIn("--approver-user aster ", BROKER)
        self.assertIn("--approver-user aster-approval", BROKER)

    def test_runtime_boundary_matches_passed_pilot(self):
        self.assertRegex(BROKER, r"(?m)^RuntimeDirectoryMode=0711$")
        self.assertIn("--socket-group aster-approval", BROKER)
        self.assertIn("--socket /run/homelab-broker-approval/approval.sock", BROKER)
        self.assertNotIn("/run/homelab-broker/approval.sock", BROKER)

    def test_ingress_requires_independent_broker(self):
        self.assertRegex(
            INGRESS,
            r"(?m)^Requires=homelab-broker-approval-independent\.service$",
        )
        self.assertRegex(
            INGRESS,
            r"(?m)^After=network-online\.target homelab-broker-approval-independent\.service$",
        )
        self.assertRegex(INGRESS, r"(?m)^User=aster-approval$")
        self.assertIn("--host 192.168.70.10 --port 9121", INGRESS)

    def test_no_execution_broker_coupling_or_extra_authority(self):
        for text in (INGRESS, BROKER):
            self.assertNotIn("homelab-broker.service", text)
            self.assertNotIn("ASTER_DELEGATION", text)
            self.assertRegex(text, r"(?m)^CapabilityBoundingSet=$")
        self.assertNotIn("PartOf=", INGRESS + BROKER)


if __name__ == "__main__":
    unittest.main()
