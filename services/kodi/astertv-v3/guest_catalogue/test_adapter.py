import ast
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ADDON = ROOT / "addon/plugin.video.asterguest"
spec = importlib.util.spec_from_file_location("guest_core", ADDON / "core.py")
core = importlib.util.module_from_spec(spec); spec.loader.exec_module(core)


class GuestAdapterTests(unittest.TestCase):
    def test_response_shape_drops_private_and_unapproved_fields(self):
        value = core.shape_item({
            "Id": "a" * 32, "Name": "Fixture", "Type": "Movie",
            "Overview": "Generic synopsis", "UserData": {"Played": True},
            "People": [{"Name": "Private fixture"}], "Path": "/private/file",
        })
        self.assertEqual(value["Name"], "Fixture")
        self.assertNotIn("UserData", value)
        self.assertNotIn("People", value)
        self.assertNotIn("Path", value)

    def test_route_and_proxy_reject_path_query_and_mutation_injection(self):
        for value in ("../Items", "a" * 31, "a" * 32 + "?api_key=x", "g" * 32):
            with self.subTest(value=value), self.assertRaises(core.GuestCatalogueError):
                core.item_id(value)
        safe = core.validate_hls_route(
            "hls1/main/0.ts",
            "MediaSourceId=" + "b" * 32 + "&VideoCodec=h264&runtimeTicks=0",
        )
        self.assertIn("VideoCodec=h264", safe)
        self.assertIn("runtimeTicks=0", safe)
        with self.assertRaises(core.GuestCatalogueError):
            core.proxy_target("delete", "b" * 32)
        with self.assertRaises(core.GuestCatalogueError):
            core.validate_hls_route("../Items/delete", "MediaSourceId=" + "b" * 32)
        with self.assertRaises(core.GuestCatalogueError):
            core.validate_hls_route("main.m3u8", "ApiKey=secret")

    def test_movie_and_episode_require_details_route_before_play(self):
        source = (ADDON / "default.py").read_text()
        self.assertIn('url("details", item=row["Id"])', source)
        self.assertIn('row["Type"] not in ("Movie", "Episode")', source)
        self.assertNotIn("Continue Watching", source)
        self.assertNotIn("Next Up", source)
        self.assertNotIn("Favorite", source)

    def test_token_is_confined_to_client_and_loopback_service(self):
        default = (ADDON / "default.py").read_text()
        core_source = (ADDON / "core.py").read_text()
        self.assertNotIn("access_token", default)
        self.assertNotIn("X-Emby-Token", default)
        self.assertNotIn("access_token", core_source)
        service = (ADDON / "service.py").read_text()
        self.assertIn('HOST = "127.0.0.1"', service)
        self.assertIn("def log_message", service)

    def test_proxy_exposes_get_and_head_only(self):
        tree = ast.parse((ADDON / "service.py").read_text())
        methods = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        self.assertIn("do_GET", methods)
        self.assertIn("do_HEAD", methods)
        self.assertTrue(methods.isdisjoint({"do_POST", "do_DELETE", "do_PUT", "do_PATCH"}))

    def test_clean_install_enables_and_verifies_exact_guest_addon(self):
        source = (ROOT / "install_candidate.py").read_text()
        self.assertIn('"addonid": "plugin.video.asterguest"', source)
        self.assertIn('"properties": ["enabled"]', source)
        self.assertIn('raise RuntimeError("guest-addon-not-enabled")', source)
        self.assertIn("enable_guest_addon()", source)


if __name__ == "__main__":
    unittest.main()
