import importlib.util
import json
import stat
import tempfile
import unittest
from pathlib import Path


PATH = Path(__file__).parent / "custom_components" / "aster_registry" / "contract.py"
SPEC = importlib.util.spec_from_file_location("aster_registry_contract", PATH)
CONTRACT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTRACT)


ALIASES = {
    "entities": {"light.kitchen": "kitchen lights"},
    "rooms": {"kitchen": "kitchen"},
    "timers": {"timer.pasta": "pasta"},
    "media": {"media_player.jellyfin": "jellyfin"},
}


class ContractTests(unittest.TestCase):
    def test_exact_aliases_only(self):
        report = CONTRACT.build_snapshot(
            snapshot_id="fixture", aliases=ALIASES,
            entity_ids={"light.kitchen", "timer.pasta", "media_player.jellyfin", "lock.private"},
            area_ids={"kitchen", "private"},
            states={"light.kitchen": "on", "timer.pasta": "active",
                    "media_player.jellyfin": "idle", "lock.private": "locked"},
        )
        self.assertEqual(report["entities"], ["kitchen lights"])
        self.assertEqual(report["rooms"], ["kitchen"])
        self.assertEqual(report["timers"], ["pasta"])
        self.assertEqual(report["media_providers"], ["jellyfin"])
        self.assertNotIn("private", repr(report))

    def test_default_empty_map_exports_nothing(self):
        aliases = {group: {} for group in ("entities", "rooms", "timers", "media")}
        report = CONTRACT.build_snapshot(snapshot_id="empty", aliases=aliases,
                                         entity_ids=set(), area_ids=set(), states={})
        self.assertEqual(sum(len(value) for key, value in report.items() if isinstance(value, list)), 0)

    def test_rejects_unregistered_state_and_effectful_domain(self):
        with self.assertRaises(ValueError):
            CONTRACT.build_snapshot(snapshot_id="bad", aliases=ALIASES, entity_ids=set(), area_ids=set(),
                                    states={"light.kitchen": "on"})
        bad = dict(ALIASES, entities={"lock.front": "front door"})
        with self.assertRaises(ValueError):
            CONTRACT.validate_aliases(bad)

    def test_output_path_is_fixed(self):
        self.assertEqual(str(CONTRACT.safe_output_path("/share/aster-registry/latest.json")),
                         "/share/aster-registry/latest.json")
        for path in ("/config/secrets.yaml", "/share/aster-registry/other.json", "latest.json"):
            with self.assertRaises(ValueError):
                CONTRACT.safe_output_path(path)

    def test_atomic_writer_uses_mode_0600(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "latest.json"
            CONTRACT.write_atomic(path, {"schema_version": 1})
            self.assertEqual(json.loads(path.read_text()), {"schema_version": 1})
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)


if __name__ == "__main__":
    unittest.main()
