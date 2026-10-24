"""Static safety checks for dormant M1 independent-ingress unit candidates."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parent / "deploy"
INGRESS = (ROOT / "aster-approval-ingress.service.candidate").read_text()
BROKER = (ROOT / "homelab-broker-approval-independent.service.candidate").read_text()


class IndependentApprovalUnitTests(unittest.TestCase):
    def test_candidates_are_inactive_artifacts(self):
        self.assertNotIn("[Install]", INGRESS)
        self.assertNotIn("[Install]", BROKER)
        self.assertTrue(INGRESS.endswith("\n"))
        self.assertTrue(BROKER.endswith("\n"))

    def test_ai_facing_identity_is_absent_from_authority_path(self):
        self.assertRegex(INGRESS, r"(?m)^User=aster-approval$")
        self.assertRegex(INGRESS, r"(?m)^Group=aster-approval$")
        self.assertNotRegex(INGRESS, r"(?m)^(User|Group|SupplementaryGroups)=aster$")
        self.assertIn("--approver-user aster-approval", BROKER)
        self.assertIn("--socket-group aster-approval", BROKER)
        self.assertNotIn("--approver-user aster ", BROKER)
        self.assertNotIn("hlabroker-approvers", BROKER)

    def test_approval_socket_has_independent_runtime_directory(self):
        self.assertRegex(BROKER, r"(?m)^RuntimeDirectory=homelab-broker-approval$")
        self.assertIn("--socket /run/homelab-broker-approval/approval.sock", BROKER)
        self.assertNotIn("/run/homelab-broker/approval.sock", BROKER)
        self.assertIn("ASTER_APPROVAL_BROKER_SOCKET", Path(
            __file__).resolve().parents[1].joinpath("approval_ingress_service.py").read_text())

    def test_both_processes_share_one_explicit_subject_allowlist_source(self):
        environment = "EnvironmentFile=/etc/aster/approval-ingress.env"
        self.assertIn(environment, INGRESS)
        self.assertIn(environment, BROKER)
        self.assertIn("--approver-subject-hash ${ASTER_APPROVAL_SUBJECT_HASHES}", BROKER)
        self.assertNotIn("ASTER_BROKER_APPROVER_SUBJECT_HASHES", BROKER)
        self.assertRegex(BROKER, r"(?m)^SupplementaryGroups=aster-approval$")

    def test_ingress_is_approval_only_and_private(self):
        command = re.search(r"(?m)^ExecStart=(.+)$", INGRESS).group(1)
        self.assertIn("approval_ingress_service:create_app", command)
        self.assertIn("--host 192.168.70.10 --port 9121", command)
        self.assertNotIn("aster_agent", command)
        self.assertIn("Requires=homelab-broker-approval-independent.service", INGRESS)

    def test_hardening_and_address_families_are_bounded(self):
        for text in (INGRESS, BROKER):
            self.assertRegex(text, r"(?m)^NoNewPrivileges=yes$")
            self.assertRegex(text, r"(?m)^ProtectSystem=strict$")
            self.assertRegex(text, r"(?m)^ProtectHome=yes$")
            self.assertRegex(text, r"(?m)^CapabilityBoundingSet=$")
        self.assertRegex(BROKER, r"(?m)^RestrictAddressFamilies=AF_UNIX$")
        self.assertRegex(INGRESS, r"(?m)^RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX$")


if __name__ == "__main__":
    unittest.main()
