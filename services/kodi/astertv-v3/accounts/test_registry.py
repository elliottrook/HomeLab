import copy
import importlib.util
import json
import stat
import tempfile
import unittest
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("astertv_profile_registry", ROOT / "registry.py")
registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(registry)
policy_spec = importlib.util.spec_from_file_location("astertv_access_policy", ROOT / "access_policy.py")
policy = importlib.util.module_from_spec(policy_spec)
policy_spec.loader.exec_module(policy)
resolver_spec = importlib.util.spec_from_file_location(
    "astertv_identity_resolver", ROOT / "identity_resolver.py"
)
resolver = importlib.util.module_from_spec(resolver_spec)
resolver_spec.loader.exec_module(resolver)


def fixture():
    return json.loads((ROOT / "synthetic-fixture.json").read_text())


class RegistryTests(unittest.TestCase):
    def test_fixture_has_two_synthetic_members_and_restricted_guest(self):
        data = registry.validate(fixture())
        members = [row for row in data["profiles"] if row["role"] == "member"]
        guest = [row for row in data["profiles"] if row["role"] == "guest"]
        self.assertEqual(len(members), 2)
        self.assertEqual(len(guest), 1)
        self.assertEqual(guest[0]["service_mappings"], [])
        self.assertTrue(all(row["display_name"].startswith("Synthetic ") for row in members))
        self.assertTrue(all(
            mapping["opaque_subject_id"].startswith("synthetic:") and not mapping["enabled"]
            for row in members for mapping in row["service_mappings"]
        ))

    def test_switch_sign_out_and_restart_persist_atomically(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "profiles.json"
            first = registry.activate(fixture(), "synthetic-member-b", "2026-11-04T01:02:03Z")
            registry.store(path, first)
            loaded, status = registry.load(path)
            self.assertEqual(status, "valid")
            self.assertEqual(loaded["active_profile_id"], "synthetic-member-b")
            signed_out = registry.sign_out(loaded, "2026-11-04T01:03:00Z")
            registry.store(path, signed_out)
            restarted, status = registry.load(path)
            self.assertEqual(status, "valid")
            self.assertEqual(restarted["active_profile_id"], "guest")
            previous, status = registry.load(path.with_suffix(".json.previous"))
            self.assertEqual(status, "valid")
            self.assertEqual(previous["active_profile_id"], "synthetic-member-b")
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(path.with_suffix(".json.previous").stat().st_mode), 0o600)

    def test_missing_and_malformed_state_fail_to_guest_without_private_mappings(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "profiles.json"
            for payload in (None, "{broken", json.dumps({"schema": 1})):
                if payload is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_text(payload)
                loaded, status = registry.load(path)
                self.assertEqual(status, "restricted-guest-fallback")
                self.assertEqual(loaded["active_profile_id"], "guest")
                self.assertEqual(loaded["profiles"][0]["service_mappings"], [])

    def test_unknown_secret_real_subject_and_guest_mapping_are_denied(self):
        cases = []
        unknown = fixture(); unknown["unexpected"] = True; cases.append(unknown)
        secret = fixture(); secret["profiles"][0]["token"] = "fixture-value"; cases.append(secret)
        real_subject = fixture(); real_subject["profiles"][0]["service_mappings"][0]["opaque_subject_id"] = "real-user-1"; cases.append(real_subject)
        guest_mapping = fixture(); guest_mapping["profiles"][2]["service_mappings"] = [copy.deepcopy(guest_mapping["profiles"][0]["service_mappings"][0])]; cases.append(guest_mapping)
        for case in cases:
            with self.subTest(case=cases.index(case)), self.assertRaises(registry.RegistryError):
                registry.validate(case)

    def test_invalid_current_state_is_not_promoted_to_previous_copy(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "profiles.json"
            path.write_text("not-json")
            with self.assertRaises(registry.RegistryError):
                registry.store(path, fixture())
            self.assertFalse(path.with_suffix(".json.previous").exists())

    def test_explicit_recovery_replaces_malformed_state_without_backing_it_up(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "profiles.json"
            path.write_text("malformed-secret-like-input")
            registry.recover_store(path, fixture())
            recovered, status = registry.load(path)
            self.assertEqual(status, "valid")
            self.assertEqual(recovered["active_profile_id"], "synthetic-member-a")
            self.assertFalse(path.with_suffix(".json.previous").exists())
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_registry_has_no_client_playback_ceiling(self):
        combined = json.dumps(fixture()) + (ROOT / "registry.py").read_text()
        for target_specific in ("1080", "18000", "passthrough_formats", "AsterTV-Jen"):
            self.assertNotIn(target_specific, combined)

    def test_guest_policy_denies_private_routes_and_allows_public_media_news(self):
        guest = registry.sign_out(fixture(), "2026-11-04T01:03:00Z")
        self.assertEqual(policy.active_role(guest), "guest")
        for focus in (9001, 9002, 9004, 9007, 9009, 100, 110, 120, 121,
                      130, 131, 132, 133, 134, 135, 136, 139, 140, 146):
            self.assertEqual(policy.select_decision(guest, focus), "deny")
        self.assertEqual(policy.select_decision(guest, 9005), "profiles")
        for focus in (9003,):
            self.assertEqual(policy.select_decision(guest, focus), "allow")
        for window in (11110, 11112, 11113, 11118, 11120, 11127, 11132, 11133):
            self.assertTrue(policy.private_surface(guest, window))
        self.assertTrue(policy.private_surface(guest, 10025, "plugin://plugin.video.youtube/"))
        self.assertFalse(policy.private_surface(guest, 11111))
        self.assertTrue(policy.private_surface(guest, 10000))
        self.assertTrue(policy.private_surface(guest, 10025, "videodb://movies/titles/"))

    def test_member_requires_both_entitlement_and_enabled_mapping(self):
        data = fixture()
        self.assertEqual(policy.active_role(data), "member")
        self.assertEqual(policy.select_decision(data, 9009), "deny")
        self.assertTrue(policy.private_surface(data, 11112))
        data["profiles"][0]["entitlements"].append("requests_submit")
        self.assertEqual(policy.select_decision(data, 9009), "deny")
        data["profiles"][0]["service_mappings"].append({
            "service": "seerr", "opaque_subject_id": "synthetic:member-a:seerr", "enabled": True,
        })
        self.assertEqual(policy.select_decision(data, 9009), "allow")
        self.assertFalse(policy.private_surface(data, 11132))

    def test_catalogue_requires_entitlement_and_enabled_jellyfin_mapping(self):
        data = fixture()
        data["profiles"][0]["entitlements"].append("public_catalogue_browse")
        self.assertTrue(policy.private_surface(data, 10000))
        data["profiles"][0]["service_mappings"][0]["enabled"] = True
        self.assertFalse(policy.private_surface(data, 10000))
        self.assertEqual(policy.select_decision(data, 9001), "allow")

    def test_local_subject_references_are_allowlisted_but_arbitrary_values_are_not(self):
        data = fixture()
        data["profiles"][0]["service_mappings"][0] = {
            "service": "jellyfin",
            "opaque_subject_id": "local:jellyfin:sha256:" + "a" * 64,
            "enabled": True,
        }
        self.assertEqual(
            registry.validate(data)["profiles"][0]["service_mappings"][0]["enabled"],
            True,
        )
        data["profiles"][0]["service_mappings"][0]["opaque_subject_id"] = "local:jellyfin:current"
        with self.assertRaises(registry.RegistryError):
            registry.validate(data)

    def test_guest_accepts_only_dedicated_guest_jellyfin_mapping(self):
        data = fixture()
        guest = data["profiles"][2]
        guest["service_mappings"] = [{
            "service": "jellyfin_guest",
            "opaque_subject_id": "local:jellyfin-guest:sha256:" + "d" * 64,
            "enabled": True,
        }]
        guest["entitlements"].extend(["guest_catalogue_browse", "guest_media_playback"])
        data["active_profile_id"] = "guest"
        validated = registry.validate(data)
        self.assertEqual(validated["profiles"][2]["service_mappings"][0]["service"],
                         "jellyfin_guest")
        self.assertEqual(policy.select_decision(validated, 9001), "guest-catalogue")
        self.assertTrue(policy.guest_playback_allowed(validated))
        self.assertFalse(policy.private_surface(
            validated, 10025, "plugin://plugin.video.asterguest/"
        ))

    def test_identity_resolution_matches_existing_custody_and_denies_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            jellyfin = root / "storage/.kodi/userdata/addon_data/plugin.video.jellyfin"
            books = root / "storage/.kodi/userdata/addon_data/plugin.audio.asterbooks"
            private = root / "storage/.aster-private"
            jellyfin.mkdir(parents=True); books.mkdir(parents=True); private.mkdir(parents=True)
            user_id = "fixture-user"
            user_hash = hashlib.sha256(user_id.encode()).hexdigest()
            files = {
                jellyfin / "data.json": {"Servers": [{"UserId": user_id, "AccessToken": "fixture-access"}]},
                jellyfin / "provisioning.json": {"user_id_sha256": user_hash},
                books / "client.json": {"api_key": "fixture-key", "server_url": "https://fixture.invalid"},
                books / "progress-enabled.json": {"account_sha256": "b" * 64, "enabled": True},
            }
            for path, value in files.items():
                path.write_text(json.dumps(value)); path.chmod(0o600)
            (private / "seerr-token").write_text("fixture-token"); (private / "seerr-token").chmod(0o600)
            (private / "astertv-broker.key").write_text("fixture-broker-key-which-is-at-least-32-bytes")
            (private / "astertv-broker.key").chmod(0o600)
            subjects = resolver.discover(root)
            self.assertEqual(subjects["jellyfin"], "local:jellyfin:sha256:" + user_hash)
            self.assertEqual(subjects["audiobookshelf"], "local:audiobookshelf:sha256:" + "b" * 64)
            self.assertEqual(subjects["seerr"], "local:seerr:client:astertv-jen")
            self.assertTrue(subjects["aster_tv"].startswith("local:astertv-broker:sha256:"))
            data = fixture()
            data["profiles"][0]["service_mappings"] = [{
                "service": "jellyfin", "opaque_subject_id": subjects["jellyfin"], "enabled": True,
            }]
            resolved, status = resolver.resolve_registry(data, root)
            self.assertEqual(status, "resolved")
            self.assertTrue(resolved["profiles"][0]["service_mappings"][0]["enabled"])
            data["profiles"][0]["service_mappings"][0]["opaque_subject_id"] = (
                "local:jellyfin:sha256:" + "c" * 64
            )
            resolved, status = resolver.resolve_registry(data, root)
            self.assertEqual(status, "identity-mismatch")
            self.assertFalse(resolved["profiles"][0]["service_mappings"][0]["enabled"])


if __name__ == "__main__":
    unittest.main()
