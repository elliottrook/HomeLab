import unittest
import sa4_fixed_runner_inactive_install_plan_v1 as plan
class Tests(unittest.TestCase):
    def test_exact_source(self): plan.validate()
    def test_create_and_rollback(self):
        value=plan.plan(); self.assertEqual("absent",value["before"]); self.assertEqual("create-exclusive",value["operation"]); self.assertTrue(value["rollback"]["remove-only-if-after-hash-matches"])
    def test_inactive(self):
        value=plan.plan(); self.assertFalse(value["effect_authorized"]); self.assertIn("no-runner-invocation",value["exclusions"])
if __name__=="__main__": unittest.main()
