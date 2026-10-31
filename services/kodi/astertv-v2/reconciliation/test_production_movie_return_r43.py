import importlib.util
import json
from pathlib import Path
import unittest


SCRIPT = Path(__file__).with_name("apply_production_movie_return_r43_fix.py")
SPEC = importlib.util.spec_from_file_location("r43", SCRIPT)
R43 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(R43)


class ProductionMovieReturnR43Tests(unittest.TestCase):
    def test_installer_contains_guarded_return_contract(self):
        source = SCRIPT.read_text()
        self.assertIn("source_window=xbmcgui.getCurrentWindowId()", source)
        self.assertIn("ActivateWindow(1130)", source)
        self.assertIn("movie-return-not-ready", source)
        self.assertIn("source_window==11127", source)
        self.assertIn("ActivateWindow(1127)", source)
        self.assertIn("search-return-not-ready", source)

    def test_reconciles_component_and_family_manifests(self):
        self.assertIn('row["sha256"] = digest(new_movie)', SCRIPT.read_text())
        self.assertIn(
            'component_row["manifest_sha256"] = digest(new_manifest)',
            SCRIPT.read_text())


if __name__ == "__main__":
    unittest.main()
