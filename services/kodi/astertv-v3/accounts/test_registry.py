import copy
import importlib.util
import json
import stat
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("astertv_profile_registry", ROOT / "registry.py")
registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(registry)


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

    def test_registry_has_no_client_playback_ceiling(self):
        combined = json.dumps(fixture()) + (ROOT / "registry.py").read_text()
        for target_specific in ("1080", "18000", "passthrough_formats", "AsterTV-Jen"):
            self.assertNotIn(target_specific, combined)


if __name__ == "__main__":
    unittest.main()
