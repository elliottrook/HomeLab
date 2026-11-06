import importlib.util
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parent
V3 = ROOT.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


overlay = load("m6_home_overlay", ROOT / "home_overlay.py")
registry = load("m6_registry", V3 / "accounts/registry.py")
policy = load("m6_policy", V3 / "accounts/access_policy.py")
resolver = load("m6_resolver", V3 / "accounts/identity_resolver.py")


class HomeOverlayTests(unittest.TestCase):
    def test_home_transform_separates_camera_runtime_and_preserves_status_list(self):
        source = (ROOT / "fixtures/custom_1112_home.predecessor.xml").read_bytes()
        output = overlay.transform_home(source)
        root = ET.fromstring(output)
        self.assertIsNotNone(root.find(".//control[@id='500']"))
        self.assertEqual(root.findtext(".//control[@id='308']/onclick"),
                         "ActivateWindow(11134)")
        self.assertEqual(root.findtext(".//control[@id='302']/onclick"),
                         "ActivateWindow(11134)")
        self.assertNotIn("aster-camera2", output.decode())
        self.assertIn("aster-home-status1", output.decode())
        self.assertIn("AsterHub.HomeSourceNotice", output.decode())

    def test_camera_window_has_bounded_lifecycle_and_closed_focus_graph(self):
        root = ET.parse(ROOT / "addon/skin/custom_1134_cameras.xml").getroot()
        self.assertEqual(root.attrib["id"], "1134")
        self.assertIn("aster-camera2,view,entry", " ".join(
            (node.text or "") for node in root.findall("onload")))
        self.assertIn("aster-camera2,view,leave", " ".join(
            (node.text or "") for node in root.findall("onunload")))
        controls = {int(node.attrib["id"]): node for node in root.findall(".//control[@id]")}
        for identity in (139, 300, 301, 302):
            self.assertIn(identity, controls)
            for direction in ("onleft", "onright", "onup", "ondown"):
                target = controls[identity].findtext(direction)
                self.assertTrue(target and target.isdecimal())
        self.assertEqual(controls[301].findtext("onclick"), "ActivateWindow(11112)")

    def test_registry_extension_is_jason_only_and_read_only(self):
        data = {
            "schema": 1, "active_profile_id": "jason",
            "profiles": [{
                "id": "jason", "display_name": "Jason", "role": "recovery_admin",
                "service_mappings": [], "entitlements": ["clock"],
                "preferences": {"clock": "24h", "captions": False},
            }, {
                "id": "guest", "display_name": "Guest", "role": "guest",
                "service_mappings": [], "entitlements": ["clock"],
                "preferences": {"clock": "24h", "captions": False},
            }], "updated_at": "2026-11-04T00:00:00Z",
        }
        marker = json.dumps({"schema": 1, "kind": "astertv-home-display",
                             "authority": "ha-home-dashboard-v4"},
                            sort_keys=True).encode() + b"\n"
        candidate = overlay.extend_registry(data, overlay.display_subject(marker))
        validated = registry.validate(candidate)
        admin, guest = validated["profiles"]
        self.assertEqual({"home_status", "camera_view"},
                         set(admin["entitlements"]) - {"clock"})
        self.assertNotIn("home_control", admin["entitlements"])
        self.assertNotIn("cameras", admin["entitlements"])
        self.assertFalse(policy.private_surface(validated, 11112))
        self.assertFalse(policy.private_surface(validated, 11134))
        signed_out = registry.sign_out(validated, "2026-11-04T01:03:00Z")
        self.assertTrue(policy.private_surface(signed_out, 11112))
        self.assertTrue(policy.private_surface(signed_out, 11134))
        self.assertEqual(guest["service_mappings"], [])

    def test_display_identity_resolves_without_credential(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "storage/.aster-home"
            home.mkdir(parents=True)
            marker = home / "display-identity.json"
            marker.write_text(json.dumps({
                "schema": 1, "kind": "astertv-home-display",
                "authority": "ha-home-dashboard-v4",
            }, sort_keys=True) + "\n")
            marker.chmod(0o600)
            subjects = resolver.discover(root)
            self.assertEqual(set(subjects), {"home_assistant"})
            self.assertEqual(subjects["home_assistant"], overlay.display_subject(marker.read_bytes()))

    def test_display_identity_ignores_json_serialization(self):
        value = {"schema": 1, "kind": "astertv-home-display",
                 "authority": "ha-home-dashboard-v4"}
        compact = (json.dumps(value, sort_keys=True) + "\n").encode()
        rendered = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
        reordered = b'{"schema":1,"authority":"ha-home-dashboard-v4","kind":"astertv-home-display"}'
        self.assertEqual(overlay.display_subject(compact),
                         overlay.display_subject(rendered))
        self.assertEqual(overlay.display_subject(compact),
                         overlay.display_subject(reordered))
        with self.assertRaisesRegex(ValueError, "display-marker-invalid"):
            overlay.display_subject(b'{"schema":1,"kind":"astertv-home-display"}')

    def test_camera_runtime_targets_only_separate_window(self):
        source = (ROOT / "addon/aster-camera2/view.py").read_text()
        self.assertIn("11134", source)
        self.assertNotIn("11112", source)
        self.assertIn("/view/stop", source)
        self.assertIn("camera_service('stop')", source)
        self.assertIn("00:02", source)

    def test_installer_is_jen_idle_bound_and_rolls_back_all_profile_state(self):
        source = (ROOT / "install_jen_home_cameras.py").read_text()
        ast.parse(source)
        self.assertIn('HOST = "AsterTV-Jen"', source)
        self.assertIn('rpc("Player.GetActivePlayers")', source)
        self.assertIn('"profiles.previous.json"', source)
        self.assertIn('After=astertv-v3-m5p-jen.service', source)
        self.assertIn('Before=kodi.service', source)
        self.assertIn('preflight(); checkpoint()', source)
        self.assertLess(source.index('preflight(); checkpoint()'),
                        source.index('run("systemctl", "stop", "kodi")'))
        self.assertNotIn("homeassistant", source.casefold())
        self.assertIn('return False', source)
        self.assertIn('checkpoint-drift:', source)
        self.assertNotIn('shutil.rmtree(CHECKPOINT)', source)

    def test_apply_overlay_has_no_home_write_or_network_client(self):
        source = (ROOT / "apply_jen_home_cameras.py").read_text()
        tree = ast.parse(source)
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree) if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertTrue(imported.isdisjoint({"urllib", "requests", "socketio", "websocket"}))
        self.assertNotIn("service.call", source)
        self.assertIn('{"home_control", "cameras"} & set', source)
        self.assertIn('["systemctl", "disable", "--now", "aster-camera.service"]', source)

    def test_camera_lifecycle_installer_is_bounded_and_reversible(self):
        source = (ROOT / "install_jen_camera_on_demand.py").read_text()
        ast.parse(source)
        self.assertIn('HOST = "AsterTV-Jen"', source)
        self.assertIn('UNIT = "aster-camera.service"', source)
        self.assertIn('PREDECESSOR = "4aad7acc', source)
        self.assertIn('run("systemctl", "disable", "--now", UNIT)', source)
        self.assertIn('"unit_enabled": state("enabled") == "enabled"', source)
        self.assertIn('"unit_active": state("active") == "active"', source)
        self.assertNotIn("homeassistant", source.casefold())


if __name__ == "__main__":
    unittest.main()
