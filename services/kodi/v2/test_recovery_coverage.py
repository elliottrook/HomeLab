import unittest

from recovery_coverage import assess
from release_inventory import InventoryError


class RecoveryCoverageTests(unittest.TestCase):
    def setUp(self):
        self.inventory = {
            "kind": "aster-release-inventory.v1", "complete": True,
            "components": [
                {"name": "family", "status": "verified"},
                {"name": "old-recovery", "status": "verified"},
                {"name": "screensaver", "status": "verified"},
            ],
        }
        self.plan = {
            "schema": 1, "kind": "aster-recovery-plan.v1",
            "sources": [{"path": "/storage/.aster-staging/family",
                         "tree_sha256": "0" * 64}],
            "coverage": [
                {"component": "family", "disposition": "source",
                 "source": "/storage/.aster-staging/family"},
                {"component": "old-recovery", "disposition": "evidence-only"},
                {"component": "screensaver", "disposition": "identity-only"},
            ],
        }

    def test_identity_only_gap_blocks_recovery_readiness(self):
        result = assess(self.inventory, self.plan)
        self.assertFalse(result["ready"])
        self.assertEqual(result["identity_only"], ["screensaver"])

    def test_every_component_with_source_or_evidence_is_ready(self):
        self.plan["coverage"][2] = {
            "component": "screensaver", "disposition": "source",
            "source": "/storage/.aster-staging/family",
        }
        self.assertTrue(assess(self.inventory, self.plan)["ready"])

    def test_missing_duplicate_unknown_and_unsafe_sources_fail_closed(self):
        self.plan["coverage"].pop()
        result = assess(self.inventory, self.plan)
        self.assertFalse(result["ready"])
        self.assertEqual(result["missing"], ["screensaver"])
        self.plan["coverage"].append(dict(self.plan["coverage"][0]))
        with self.assertRaisesRegex(InventoryError, "component-identity"):
            assess(self.inventory, self.plan)
        self.plan["coverage"][-1]["component"] = "screensaver"
        self.plan["coverage"][-1]["source"] = "/tmp/arbitrary"
        with self.assertRaisesRegex(InventoryError, "recovery-source"):
            assess(self.inventory, self.plan)


if __name__ == "__main__":
    unittest.main()
