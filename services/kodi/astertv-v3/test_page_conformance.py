import importlib.util
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "astertv_v3_page_audit", HERE / "audit_page_conformance.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PageConformanceTests(unittest.TestCase):
    def test_every_v3_page_passes_the_structural_design_contract(self):
        result = MODULE.audit()
        self.assertEqual(result["page_count"], 15)
        self.assertEqual(result["failure_count"], 0, result["pages"])
        self.assertEqual(result["outcome"], "pass")


if __name__ == "__main__":
    unittest.main()
