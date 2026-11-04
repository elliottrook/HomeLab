import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("astertv_authority", ROOT / "authority.py")
authority = importlib.util.module_from_spec(spec)
spec.loader.exec_module(authority)


class AuthorityTests(unittest.TestCase):
    def populate(self, root):
        jellyfin = root / "storage/.kodi/userdata/addon_data/plugin.video.jellyfin"
        books = root / "storage/.kodi/userdata/addon_data/plugin.audio.asterbooks"
        private = root / "storage/.aster-private"
        jellyfin.mkdir(parents=True); books.mkdir(parents=True); private.mkdir(parents=True)
        user_id = "fixture-user"
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()
        rows = {
            jellyfin / "data.json": {"Servers": [{"UserId": user_id, "AccessToken": "fixture-access"}]},
            jellyfin / "provisioning.json": {"user_id_sha256": user_hash},
            books / "client.json": {"api_key": "fixture-key", "server_url": "https://fixture.invalid"},
            books / "progress-enabled.json": {"account_sha256": "b" * 64, "enabled": True},
        }
        for path, value in rows.items():
            path.write_text(json.dumps(value)); path.chmod(0o600)
        (private / "seerr-token").write_text("fixture-token"); (private / "seerr-token").chmod(0o600)

    def add_guest(self, root):
        private = root / "storage/.aster-private"
        guest_id = "guest-user"
        value = {
            "schema": 1, "server_url": "http://fixture.invalid",
            "user_id": guest_id,
            "user_id_sha256": hashlib.sha256(guest_id.encode()).hexdigest(),
            "access_token": "guest-fixture-access",
            "device_id": "astertv-jen-guest-catalogue",
            "allowed_folders": [
                {"id": "1", "name": "Movies", "type": "movies"},
                {"id": "2", "name": "Shows", "type": "tvshows"},
                {"id": "3", "name": "Archive Movies", "type": "movies"},
                {"id": "4", "name": "Archive TV", "type": "tvshows"},
            ],
        }
        path = private / "jellyfin-guest.json"
        path.write_text(json.dumps(value)); path.chmod(0o600)

    def test_builds_recovery_admin_and_restricted_guest_without_credentials(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); self.populate(root)
            config = {"schema": 1, "recovery_admin_display_name": "Fixture Admin", "profile_id": "fixture-admin"}
            result = authority.build_registry(config, "2026-11-04T01:02:03Z", root)
            self.assertEqual(result["active_profile_id"], "guest")
            admin = result["profiles"][0]
            self.assertEqual(admin["role"], "recovery_admin")
            self.assertEqual({x["service"] for x in admin["service_mappings"]},
                             {"jellyfin", "audiobookshelf", "seerr"})
            self.assertTrue(all(x["enabled"] for x in admin["service_mappings"]))
            self.assertEqual(result["profiles"][1]["service_mappings"], [])
            encoded = json.dumps(result).casefold()
            for forbidden in ("fixture-access", "fixture-key", "fixture-token", "api_key", "access_token"):
                self.assertNotIn(forbidden, encoded)

    def test_authority_config_is_exact_and_credential_free(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "authority.json"
            path.write_text(json.dumps({"schema": 1, "recovery_admin_display_name": "Fixture", "profile_id": "fixture"}))
            self.assertEqual(authority.load_authority(path)["profile_id"], "fixture")
            path.write_text(json.dumps({"schema": 1, "recovery_admin_display_name": "Fixture", "profile_id": "fixture", "token": "x"}))
            with self.assertRaises(authority.AuthorityError):
                authority.load_authority(path)

    def test_guest_credential_adds_only_dedicated_guest_mapping(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); self.populate(root); self.add_guest(root)
            config = {"schema": 1, "recovery_admin_display_name": "Fixture Admin",
                      "profile_id": "fixture-admin"}
            result = authority.build_registry(config, "2026-11-04T01:02:03Z", root)
            guest = result["profiles"][1]
            self.assertEqual({x["service"] for x in guest["service_mappings"]},
                             {"jellyfin_guest"})
            self.assertIn("guest_media_playback", guest["entitlements"])
            self.assertNotIn("guest-fixture-access", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
