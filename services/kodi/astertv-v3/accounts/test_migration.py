import ast
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("astertv_migration", ROOT / "migrate_jen_authority.py")
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)
build_spec = importlib.util.spec_from_file_location("astertv_candidate", ROOT / "build_jen_candidate.py")
candidate = importlib.util.module_from_spec(build_spec)
build_spec.loader.exec_module(candidate)


class MigrationTests(unittest.TestCase):
    def test_archive_is_exact_and_contains_no_identity_state(self):
        payload = candidate.build_bytes()
        manifest = candidate.validate_archive(payload)
        self.assertEqual(manifest["target"], "AsterTV-Jen")
        self.assertFalse(manifest["release"])
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "candidate.tar.gz"
            archive.write_bytes(payload)
            migration.validate_archive(archive, hashlib.sha256(payload).hexdigest())
        for forbidden in (b"Jason", b"real-subject-fixture-must-not-appear"):
            self.assertNotIn(forbidden, payload)

    def test_migration_is_host_idle_guard_bound_and_has_no_network_client(self):
        source = (ROOT / "migrate_jen_authority.py").read_text()
        self.assertIn('EXPECTED_HOST = "AsterTV-Jen"', source)
        self.assertIn('json_rpc("Player.GetActivePlayers")', source)
        self.assertIn('result.get("files") != 528', source)
        self.assertIn("restore(destination)", source)
        tree = ast.parse(source)
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertTrue(imports.isdisjoint({"requests", "urllib", "http", "websocket"}))

    def test_restore_targets_only_candidate_and_pinned_boundary_files(self):
        source = (ROOT / "migrate_jen_authority.py").read_text()
        self.assertNotIn("Family", source)
        self.assertNotIn("Bedroom", source)
        self.assertNotIn("guisettings.xml", source)
        self.assertNotIn("profiles.xml", source)

    def test_checkpoint_and_restore_are_exact_for_candidate_boundary(self):
        names = ("ADDON", "STATE", "PROFILES", "AUTHORITY", "KEYMAP",
                 "ACCEPTED", "POLICY", "CHECKPOINT_ROOT")
        original = {name: getattr(migration, name) for name in names}
        self.addCleanup(lambda: [setattr(migration, name, value) for name, value in original.items()])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            migration.ADDON = root / "storage/.kodi/addons/script.asterprofiles.v3lab"
            migration.STATE = root / "storage/.kodi/userdata/addon_data/script.asterprofiles.v3lab"
            migration.PROFILES = migration.STATE / "profiles.json"
            migration.AUTHORITY = migration.STATE / "authority.json"
            migration.KEYMAP = root / "storage/.kodi/userdata/keymaps/profile.xml"
            migration.ACCEPTED = root / "storage/.aster-release/accepted/accepted-manifest.json"
            migration.POLICY = root / "storage/.aster-policy/jellyfin_client_policy.py"
            migration.CHECKPOINT_ROOT = root / "storage/.aster-checkpoints"
            fixtures = {
                migration.ADDON / "addon.xml": "r6-addon",
                migration.PROFILES: "r6-state",
                migration.KEYMAP: "r6-keymap",
                migration.ACCEPTED: "accepted",
                migration.POLICY: "policy",
            }
            for path, value in fixtures.items():
                path.parent.mkdir(parents=True, exist_ok=True); path.write_text(value)
            checkpoint = migration.checkpoint("fixture")
            for path in fixtures:
                if path.exists():
                    path.write_text("changed")
            migration.restore(checkpoint)
            for path, value in fixtures.items():
                self.assertEqual(path.read_text(), value)


if __name__ == "__main__":
    unittest.main()
