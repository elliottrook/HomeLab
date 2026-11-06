import hashlib
from pathlib import Path
import unittest
import sa4_effect_controller_inactive_install_plan_v1 as install

class Tests(unittest.TestCase):
    def test_sources(self):
        root=Path(__file__).parents[2]
        for item in install.CHANGES:
            self.assertEqual(item.after_sha256,hashlib.sha256((root/item.source).read_bytes()).hexdigest())
    def test_rollback(self):
        value=install.plan()
        self.assertTrue(all(x["operation"]=="create-exclusive" for x in value["changes"]))
        self.assertEqual([x.destination for x in reversed(install.CHANGES)],value["rollback"]["remove-only-exact-after-hashes"])
    def test_inactive(self):
        value=install.plan(); self.assertFalse(value["effect_authorized"])
        self.assertIn("no-controller-invocation",value["exclusions"])

if __name__ == "__main__": unittest.main()
