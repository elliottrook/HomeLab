import copy
import unittest

from recovery_recipe import validate
from release_inventory import InventoryError


class RecoveryRecipeTests(unittest.TestCase):
    def setUp(self):
        self.plan = {"sources": [{"path": "/storage/.aster-staging/base"},
                                 {"path": "/storage/.aster-staging/delta"}]}
        self.recipe = {
            "schema": 1, "kind": "aster-recovery-recipe.v1",
            "prerequisites": [
                {"id": "os", "kind": "platform", "requirement": "LibreELEC"},
                {"id": "key", "kind": "restricted-provisioning",
                 "requirement": "Provision separately; never bundle"},
            ],
            "steps": [
                {"order": 1, "id": "base", "action": "install-base-archives",
                 "sources": ["/storage/.aster-staging/base"], "kodi_restart": True},
                {"order": 2, "id": "delta", "action": "apply-successor",
                 "sources": ["/storage/.aster-staging/delta"]},
                {"order": 3, "id": "verify", "action": "verify-release",
                 "sources": []},
            ],
        }

    def test_valid_recipe_covers_every_source(self):
        result = validate(self.plan, self.recipe)
        self.assertEqual(result, {"valid": True, "steps": 3, "sources": 2,
                                  "prerequisites": 2, "kodi_restarts": [1]})

    def test_missing_duplicate_unknown_and_out_of_order_sources_fail(self):
        cases = []
        value = copy.deepcopy(self.recipe); value["steps"][1]["sources"] = []; cases.append(value)
        value = copy.deepcopy(self.recipe); value["steps"][1]["sources"] = ["/tmp/nope"]; cases.append(value)
        value = copy.deepcopy(self.recipe); value["steps"][1]["sources"] = ["/storage/.aster-staging/base"]; cases.append(value)
        value = copy.deepcopy(self.recipe); value["steps"][1]["order"] = 3; cases.append(value)
        for value in cases:
            with self.assertRaises(InventoryError): validate(self.plan, value)

    def test_final_step_and_restart_bound_are_enforced(self):
        value = copy.deepcopy(self.recipe); value["steps"][-1]["action"] = "apply-successor"
        with self.assertRaisesRegex(InventoryError, "final-verify"):
            validate(self.plan, value)
        value = copy.deepcopy(self.recipe)
        for row in value["steps"]: row["kodi_restart"] = True
        value["steps"].insert(2, {"order": 3, "id": "extra",
            "action": "verify-release", "sources": [], "kodi_restart": True})
        value["steps"][3]["order"] = 4
        with self.assertRaisesRegex(InventoryError, "restart-bound"):
            validate(self.plan, value)


if __name__ == "__main__": unittest.main()
