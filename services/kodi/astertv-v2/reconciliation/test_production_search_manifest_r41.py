import importlib.util
import json
from pathlib import Path
import unittest


SCRIPT = Path(__file__).with_name("apply_production_search_manifest_r41_fix.py")
SPEC = importlib.util.spec_from_file_location("r41", SCRIPT)
R41 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(R41)


class ProductionSearchManifestR41Tests(unittest.TestCase):
    def test_reconciles_only_dispatcher_acceptance(self):
        family = {
            "skin": {
                "tools/select_dispatch.py": R41.OLD_ACCEPTED_DISPATCH,
                "1080i/Home.xml": "home-hash",
            },
            "components": {"search": {"manifest_sha256": "component-hash"}},
        }
        updated = json.loads(R41.reconciled_family(
            (json.dumps(family) + "\n").encode(), R41.EXPECTED_DISPATCH))
        self.assertEqual(
            updated["skin"]["tools/select_dispatch.py"], R41.EXPECTED_DISPATCH)
        self.assertEqual(updated["skin"]["1080i/Home.xml"], "home-hash")
        self.assertEqual(updated["components"], family["components"])

    def test_rejects_unknown_manifest_predecessor(self):
        family = {"skin": {"tools/select_dispatch.py": "changed"}}
        with self.assertRaisesRegex(
                RuntimeError, "unexpected accepted dispatcher predecessor"):
            R41.reconciled_family(
                (json.dumps(family) + "\n").encode(), R41.EXPECTED_DISPATCH)


if __name__ == "__main__":
    unittest.main()
