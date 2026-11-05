import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astertv_design_build", HERE / "build_pattern_library.py")
BUILD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BUILD
SPEC.loader.exec_module(BUILD)


class DesignSystemTests(unittest.TestCase):
    def test_outputs_are_deterministic(self):
        first = BUILD.outputs()
        second = BUILD.outputs()
        self.assertEqual(first, second)

    def test_focus_graphs_are_closed(self):
        self.assertEqual(BUILD.validate_focus(BUILD.load("focus-graphs.json")), [])

    def test_icon_context_is_exclusive(self):
        contexts = BUILD.load("tokens.json")["icon_context"]
        self.assertEqual(contexts["stone"], ["floating-side-rail", "launcher"])
        self.assertFalse(set(contexts["stone"]) & set(contexts["plain"]))

    def test_component_catalogue_has_required_states(self):
        components = {item["id"]: item for item in BUILD.load("catalogue.json")["components"]}
        self.assertTrue({"rest", "focus", "pressed", "disabled"} <= set(components["button"]["states"]))
        self.assertTrue({"rest", "focus", "watched", "unwatched", "missing-art"} <= set(components["artwork-tile"]["states"]))

    def test_fixtures_are_privacy_safe(self):
        raw = (HERE / "catalogue.json").read_text().lower()
        for forbidden in ["password", "api_key", "token_value", "camera_url"]:
            self.assertNotIn(forbidden, raw)

    def test_runtime_assets_have_hashes(self):
        records = BUILD.runtime_assets()
        self.assertGreater(len(records), 10)
        for record in records:
            self.assertRegex(record["sha256"], r"^[0-9a-f]{64}$")

    def test_plain_compass_resolves_to_exact_approved_exports(self):
        catalogue = BUILD.load("catalogue.json")
        assets = {item["id"]: item for item in catalogue["semantic_assets"]}
        plain = assets["plain-compass"]
        self.assertEqual(plain["master"], "SVG/15-aster-compass.svg")
        self.assertRegex(plain["master_sha256"], r"^[0-9a-f]{64}$")
        self.assertGreaterEqual(len(plain["runtime_exports"]), 4)
        self.assertNotIn("floating-side-rail", plain["allowed_contexts"])
        self.assertIn("floating-side-rail", plain["forbidden_contexts"])
        for export in plain["runtime_exports"]:
            self.assertRegex(export["sha256"], r"^[0-9a-f]{64}$")

    def test_button_focus_does_not_change_geometry(self):
        tokens = BUILD.load("tokens.json")
        self.assertEqual(tokens["geometry"]["pill_radius"], 28)
        # One geometry token governs every state; state-specific geometry is forbidden.
        self.assertNotIn("focus_geometry", tokens)

    def test_generated_outputs_match(self):
        for path, expected in BUILD.outputs().items():
            self.assertTrue(path.exists(), path)
            self.assertEqual(path.read_text(), expected, path)

    def test_all_required_page_families_are_mapped(self):
        catalogue = BUILD.load("catalogue.json")
        mapped = {page["family"] for page in catalogue["pages"]}
        self.assertEqual(set(catalogue["required_page_families"]) - mapped, set())
        for page in catalogue["pages"]:
            self.assertTrue((BUILD.ROOT / page["template"]).is_file(), page["template"])

    def test_schema_documents_are_valid_json_schema(self):
        for path in sorted((HERE / "schemas").glob("*.schema.json")):
            schema = json.loads(path.read_text())
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertEqual(schema["type"], "object")

    def test_every_component_and_page_has_1080p_fixture(self):
        catalogue = BUILD.load("catalogue.json")
        outputs = BUILD.outputs()
        for component in catalogue["components"]:
            path = BUILD.GENERATED / "renders/components" / f'{component["id"]}.svg'
            self.assertIn(path, outputs)
        for page in catalogue["pages"]:
            path = BUILD.GENERATED / "renders/pages" / f'{page["id"]}.svg'
            self.assertIn(path, outputs)
        for path, content in outputs.items():
            if path.suffix == ".svg":
                root = BUILD.ET.fromstring(content)
                self.assertEqual(root.attrib["width"], "1920")
                self.assertEqual(root.attrib["height"], "1080")


if __name__ == "__main__":
    unittest.main()
