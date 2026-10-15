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
    "temperatures": {"sensor.hall_temperature": "hall temperature"},
}


class ContractTests(unittest.TestCase):
    def test_exact_aliases_only(self):
        report = CONTRACT.build_snapshot(
            snapshot_id="fixture", aliases=ALIASES,
            entity_ids={"light.kitchen", "timer.pasta", "media_player.jellyfin",
                        "sensor.hall_temperature", "lock.private"},
            area_ids={"kitchen", "private"},
            states={"light.kitchen": "on", "timer.pasta": "active",
                    "media_player.jellyfin": "idle", "sensor.hall_temperature": "20.6",
                    "lock.private": "locked"},
            units={"sensor.hall_temperature": "°C"},
        )
        self.assertEqual(report["entities"], ["kitchen lights"])
        self.assertEqual(report["rooms"], ["kitchen"])
        self.assertEqual(report["timers"], ["pasta"])
        self.assertEqual(report["media_providers"], ["jellyfin"])
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(report["lights"], [{"alias": "kitchen lights", "state": "on"}])
        self.assertEqual(report["temperatures"], [
            {"alias": "hall temperature", "value": 20.6, "unit": "°C"}])
        self.assertNotIn("private", repr(report))

    def test_default_empty_map_exports_nothing(self):
        aliases = {group: {} for group in ("entities", "rooms", "timers", "media", "temperatures")}
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
        bad_sensor = dict(ALIASES, temperatures={"binary_sensor.motion": "motion"})
        with self.assertRaises(ValueError):
            CONTRACT.validate_aliases(bad_sensor)

    def test_temperature_missing_invalid_and_out_of_range_fail_closed(self):
        base = dict(snapshot_id="fixture", aliases=ALIASES,
                    entity_ids={"sensor.hall_temperature"}, area_ids=set())
        for state, unit in (("unknown", "°C"), ("nan", "°C"), ("99", "°C"),
                            ("20", "K"), ("-1", None)):
            report = CONTRACT.build_snapshot(**base,
                                             states={"sensor.hall_temperature": state},
                                             units={"sensor.hall_temperature": unit})
            self.assertEqual(report["temperatures"], [])
        report = CONTRACT.build_snapshot(**base,
                                         states={"sensor.hall_temperature": "68"},
                                         units={"sensor.hall_temperature": "°F"})
        self.assertEqual(report["temperatures"][0]["value"], 68.0)

    def test_switch_is_not_presented_as_a_light(self):
        aliases = dict(ALIASES, entities={"switch.fan": "fan switch"})
        report = CONTRACT.build_snapshot(snapshot_id="fixture", aliases=aliases,
                                         entity_ids={"switch.fan"}, area_ids=set(),
                                         states={"switch.fan": "on"})
        self.assertEqual(report["lights"], [])
        self.assertEqual(report["entities"], ["fan switch"])

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
