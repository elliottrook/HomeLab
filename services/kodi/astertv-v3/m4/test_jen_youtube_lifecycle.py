import ast
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ACCOUNTS = ROOT.parent / "accounts"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


resolver = module("m4y_resolver", ACCOUNTS / "identity_resolver.py")
apply_overlay = module("m4y_apply", ROOT / "apply_jen_m4y.py")


class JenYouTubeLifecycleTests(unittest.TestCase):
    def test_nav_transform_removes_all_unconditional_private_providers(self):
        fixture = ("<window>" + "".join(apply_overlay.CONTENT) + "</window>").encode()
        result = apply_overlay.patch_nav(fixture).decode()
        self.assertNotIn("<content", result)
        for route in ("subscriptions/list", "special/recommendations", "special/playlist/WL"):
            self.assertNotIn(route, result)

    def test_root_helper_is_demand_driven_and_profile_gated(self):
        source = (ROOT / "youtube_root_focus.py").read_text()
        tree = ast.parse(source)
        self.assertIn('folder == ROOT', source)
        self.assertIn('folder and folder != ROOT', source)
        self.assertIn('"personal_youtube" in entitlements', source)
        self.assertIn('"youtube" in services', source)
        self.assertNotIn("Files.GetDirectory", source)
        self.assertNotIn("addItems", source)
        self.assertIn('Container.IsUpdating', source)
        self.assertNotIn("access_token", source)
        self.assertNotIn("refresh_token", source)

    def test_graceful_stop_is_bounded_and_keeps_systemd_fallback(self):
        source = (ROOT / "graceful_kodi_stop.py").read_text()
        ast.parse(source)
        self.assertIn('rpc("Application.Quit")', source)
        self.assertIn('rpc("Input.Home")', source)
        self.assertIn('Window(Home).Property(AsterMovie.Ready)', source)
        self.assertIn("time.monotonic() + 25", source)
        self.assertNotIn("SIGKILL", source)
        self.assertNotIn("os.kill", source)

    def test_installer_is_resumable_and_has_explicit_checkpoint_rollback(self):
        source = (ROOT / "install_jen_youtube_lifecycle.py").read_text()
        ast.parse(source)
        self.assertIn("def restore_checkpoint():", source)
        self.assertIn('mode.add_argument("--rollback"', source)
        self.assertIn('checkpoint-host-mismatch', source)
        self.assertIn('youtube-nav-overlay-drift', source)
        self.assertIn('(YOUTUBE, manifest.get("youtube_state_present", False))', source)

    def test_youtube_identity_requires_private_complete_signed_in_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / "storage/.kodi/userdata/addon_data/plugin.video.youtube"
            state.mkdir(parents=True)
            rows = {
                "access_manager.json": {"access_manager": {"current_user": 0,
                    "users": {"0": {"id": "household", "access_token": "access",
                                      "refresh_token": "refresh"}}}},
                "api_keys.json": {"keys": {"user": {"api_key": "key",
                    "client_id": "client", "client_secret": "secret"}}},
            }
            for name, value in rows.items():
                path = state / name; path.write_text(json.dumps(value)); path.chmod(0o600)
            settings = state / "settings.xml"; settings.write_text("<settings />"); settings.chmod(0o600)
            subjects = resolver.discover(root)
            self.assertRegex(subjects["youtube"], r"^local:youtube:sha256:[0-9a-f]{64}$")
            settings.chmod(0o644)
            self.assertNotIn("youtube", resolver.discover(root))


if __name__ == "__main__":
    unittest.main()
