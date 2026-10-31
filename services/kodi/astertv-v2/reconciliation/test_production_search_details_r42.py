import importlib.util
import json
from pathlib import Path
import unittest


SCRIPT = Path(__file__).with_name("apply_production_search_details_r42_fix.py")
SPEC = importlib.util.spec_from_file_location("r42", SCRIPT)
R42 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(R42)


class ProductionSearchDetailsR42Tests(unittest.TestCase):
    def fixtures(self):
        default = (R42.IMPORT_ANCHOR + "value = read_details(rpc, hit)\n").encode()
        manifest = R42.encode({
            "files": [{"path": "default.py", "bytes": len(default),
                       "sha256": R42.digest(default)}]})
        family = R42.encode({
            "components": {"aster-global-search-ui22": {
                "manifest_sha256": R42.digest(manifest)}}})
        return default, manifest, family

    def test_restores_import_and_reconciles_integrity_chain(self):
        default, manifest, family = self.fixtures()
        new_default, new_manifest, new_family = R42.patched(
            default, manifest, family)
        self.assertIn(R42.DETAILS_IMPORT.encode(), new_default)
        component = json.loads(new_manifest)
        self.assertEqual(component["files"][0]["sha256"], R42.digest(new_default))
        accepted = json.loads(new_family)
        self.assertEqual(
            accepted["components"]["aster-global-search-ui22"]
            ["manifest_sha256"], R42.digest(new_manifest))

    def test_rejects_reapplication(self):
        default, manifest, family = self.fixtures()
        default = default.replace(
            R42.IMPORT_ANCHOR.encode(),
            (R42.IMPORT_ANCHOR + R42.DETAILS_IMPORT).encode())
        with self.assertRaisesRegex(RuntimeError, "unexpected Search import"):
            R42.patched(default, manifest, family)


if __name__ == "__main__":
    unittest.main()
