import ast
import importlib.util
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ADDON = ROOT / "addon/script.asterprofiles.v3lab"
spec = importlib.util.spec_from_file_location("jen_candidate", ROOT / "build_jen_candidate.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class AddonPackageTests(unittest.TestCase):
    def test_addon_identity_is_isolated_v3_lab_namespace(self):
        root = ET.parse(ADDON / "addon.xml").getroot()
        self.assertEqual(root.attrib["id"], "script.asterprofiles.v3lab")
        self.assertEqual(root.attrib["version"], "0.4.0")
        extensions = {node.attrib["point"]: node.attrib.get("library") for node in root.findall("extension")}
        self.assertEqual(extensions["xbmc.service"], "service.py")
        self.assertIn("Jen-only", " ".join(root.itertext()))

    def test_entry_point_has_no_network_or_service_client_imports(self):
        tree = ast.parse((ADDON / "default.py").read_text())
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        )
        self.assertTrue({"xbmc", "xbmcgui", "xbmcvfs", "registry"} <= imports)
        self.assertTrue(imports.isdisjoint({"requests", "urllib", "socket", "websocket"}))

    def test_fixture_is_packaged_but_contains_only_synthetic_disabled_mappings(self):
        fixture = json.loads((ROOT / "synthetic-fixture.json").read_text())
        for profile in fixture["profiles"]:
            for mapping in profile["service_mappings"]:
                self.assertTrue(mapping["opaque_subject_id"].startswith("synthetic:"))
                self.assertFalse(mapping["enabled"])

    def test_runtime_files_are_present_for_package_copy(self):
        self.assertTrue((ROOT / "registry.py").is_file())
        self.assertTrue((ROOT / "access_policy.py").is_file())
        self.assertTrue((ROOT / "authority.py").is_file())
        self.assertTrue((ROOT / "identity_resolver.py").is_file())
        self.assertTrue((ROOT / "synthetic-fixture.json").is_file())
        self.assertTrue((ADDON / "default.py").is_file())
        self.assertTrue((ADDON / "service.py").is_file())
        self.assertTrue((ROOT / "keymaps/z-astertv-v3-m2-profile-gate.xml").is_file())

    def test_candidate_is_reproducible_and_excludes_client_limits(self):
        first = candidate.build_bytes()
        second = candidate.build_bytes()
        self.assertEqual(first, second)
        manifest = candidate.validate_archive(first)
        self.assertEqual(manifest["target"], "AsterTV-Jen")
        self.assertFalse(manifest["release"])
        self.assertFalse(manifest["production_service_mappings"])
        self.assertTrue(manifest["local_service_resolution"])
        self.assertFalse(manifest["client_capability_policy_included"])
        self.assertNotIn(b"1080", first)
        self.assertNotIn(b"passthrough_formats", first)

    def test_installer_is_bound_to_jen_and_only_isolated_paths_are_removed(self):
        source = (ROOT / "install_jen_candidate.py").read_text()
        self.assertIn('EXPECTED_HOST = "AsterTV-Jen"', source)
        self.assertIn('ADDON = KODI / "addons/script.asterprofiles.v3lab"', source)
        self.assertIn('STATE = KODI / "userdata/addon_data/script.asterprofiles.v3lab"', source)
        self.assertNotIn("1920", source)
        self.assertNotIn("passthrough", source)
        tree = ast.parse(source)
        removed_names = {
            ast.unparse(call.args[0])
            for call in ast.walk(tree)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "rmtree"
            and call.args
        }
        self.assertEqual(removed_names, {"ADDON", "STATE"})

    def test_guest_gate_wraps_existing_dispatcher_and_denies_private_surfaces(self):
        source = (ADDON / "default.py").read_text()
        service = (ADDON / "service.py").read_text()
        policy = (ROOT / "access_policy.py").read_text()
        self.assertIn("special://skin/tools/select_dispatch.py", source)
        self.assertIn("script.astervoice.v2lab", source)
        self.assertIn("select_decision(current, focused)", source)
        self.assertIn("private_surface(current, current_window, folder)", service)
        self.assertIn("11110", policy)
        self.assertIn("11112", policy)
        self.assertIn("11132", policy)
        self.assertIn("plugin.video.youtube", policy)

    def test_missing_state_recovers_from_local_authority_not_synthetic_fixture(self):
        source = (ADDON / "default.py").read_text()
        authority_branch = source.index("if AUTHORITY.exists():")
        fixture_branch = source.index("fixture = validate", authority_branch)
        self.assertLess(authority_branch, fixture_branch)
        self.assertIn("recover_store(STATE, build_registry(authority, now()))", source)

    def test_candidate_keymap_routes_only_global_select_voice_and_click(self):
        keymap = ET.parse(ROOT / "keymaps/z-astertv-v3-m2-profile-gate.xml").getroot()
        tags = {node.tag for node in keymap.findall("./global/keyboard/*")}
        self.assertEqual(tags, {"select", "key", "return", "enter", "browser_search"})
        self.assertEqual(
            keymap.findtext("./global/keyboard/browser_search"),
            "RunScript(script.asterprofiles.v3lab,action=voice)",
        )


if __name__ == "__main__":
    unittest.main()
