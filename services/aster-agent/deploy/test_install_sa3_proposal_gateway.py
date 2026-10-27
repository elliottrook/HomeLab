import re
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("install_sa3_proposal_gateway.sh")


class Sa3ProposalGatewayInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text()

    def test_pins_one_predecessor_and_four_candidate_files(self):
        files = self.source.split("files=(", 1)[1].split(")", 1)[0].split()
        self.assertEqual([
            "aster_agent.py", "sysadmin_proposal_boundary.py",
            "sysadmin_proposal_transport.py", "sysadmin_proposal_gateway.py",
        ], files)
        candidates = self.source.split("candidate_shas=(", 1)[1].split(")", 1)[0]
        self.assertEqual(4, len(re.findall(r"(?m)^  [0-9a-f]{64}$", candidates)))
        self.assertIn("live_agent_sha=43af11c9", self.source)
        self.assertIn('test "$#" -eq 0', self.source)
        self.assertIn('packet=/tmp/aster-sa3-proposal-gateway-20261027', self.source)
        self.assertNotIn('packet=${1:-', self.source)

    def test_preexisting_modules_are_required_absent(self):
        for name in (
            "sysadmin_proposal_boundary.py",
            "sysadmin_proposal_transport.py",
            "sysadmin_proposal_gateway.py",
        ):
            self.assertIn(f'test ! -e "$target_root/{name}"', self.source)

    def test_checkpoint_precedes_install_and_rollback_removes_additions(self):
        checkpoint = self.source.index('cp -p "$target_root/aster_agent.py" "$checkpoint/aster_agent.py"')
        install = self.source.index('install -o root -g root -m 0644 "$packet/$name"')
        self.assertLess(checkpoint, install)
        rollback = self.source.split("restore_checkpoint()", 1)[1].split("cleanup_partial_installs()", 1)[0]
        self.assertIn('mv -f "$target_root/aster_agent.py.new"', rollback)
        self.assertEqual(3, rollback.count('$target_root/sysadmin_proposal_'))
        cleanup = self.source.split("cleanup_partial_installs()", 1)[1].split("rollback()", 1)[0]
        self.assertEqual(4, cleanup.count(".py.new"))
        rollback_body = self.source.split("rollback()", 1)[1].split("trap rollback", 1)[0]
        self.assertIn('if [ "$staged_new" -eq 1 ]', rollback_body)
        self.assertIn("cleanup_partial_installs", rollback_body)
        self.assertIn('test ! -e "$target_root/$name.new"', self.source)
        self.assertLess(
            self.source.index('test ! -e "$target_root/$name.new"'),
            self.source.index("staged_new=1", self.source.index("trap rollback")),
        )

    def test_only_aster_agent_is_restarted_and_auth_remains_closed(self):
        self.assertEqual(2, self.source.count("systemctl restart aster-agent.service"))
        self.assertNotIn("aster-llama.service", self.source)
        self.assertNotIn("systemctl daemon-reload", self.source)
        self.assertIn("http://192.168.70.10:9120/v1/models", self.source)
        self.assertIn("/v1/sysadmin/incidents/inc-auth-check/propose", self.source)
        self.assertIn("-X POST", self.source)
        self.assertIn(')" = 401', self.source)

    def test_preinstall_import_requires_exact_proposal_route(self):
        import_check = self.source.index("PYTHONDONTWRITEBYTECODE=1")
        first_install = self.source.index('install -o root -g root -m 0644 "$packet/$name"')
        self.assertLess(import_check, first_install)
        self.assertIn('/v1/sysadmin/incidents/{incident_id}/propose', self.source)


if __name__ == "__main__":
    unittest.main()
