import importlib.util
import json
import stat
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "aster_homeassistant_producer", ROOT / "scripts/produce-aster-homeassistant-report.py"
)
producer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(producer)


SAMPLE_STATES = [
    {"entity_id": "light.hall", "state": "on"},
    {"entity_id": "light.laundry", "state": "off"},
    {"entity_id": "light.garage", "state": "unavailable"},
    {"entity_id": "lock.front_door", "state": "locked"},
    {"entity_id": "climate.living_room", "state": "heat"},
    {"entity_id": "vacuum.roomba", "state": "docked"},
    {"entity_id": "automation.laundry_motion_lighting", "state": "on"},
    {"entity_id": "automation.stale_disabled_one", "state": "off"},
    {"entity_id": "sensor.outdoor_temp", "state": "12.4"},  # not an allowed domain -- must be dropped
    {"entity_id": "person.jason", "state": "home"},  # not an allowed domain -- must be dropped
]


class ClassifyTests(unittest.TestCase):
    def test_classifies_known_domain_states(self):
        self.assertEqual(producer._classify("light", "on"), "entity_on")
        self.assertEqual(producer._classify("lock", "locked"), "entity_on")
        self.assertEqual(producer._classify("lock", "unlocked"), "entity_off")
        self.assertEqual(producer._classify("cover", "open"), "entity_on")
        self.assertEqual(producer._classify("climate", "off"), "entity_off")

    def test_classifies_unavailable_and_unknown(self):
        self.assertEqual(producer._classify("light", "unavailable"), "entity_unavailable")
        self.assertEqual(producer._classify("light", "unknown"), "entity_unknown")

    def test_unrecognized_state_string_is_unknown_not_unavailable(self):
        self.assertEqual(producer._classify("vacuum", "some_future_firmware_state"), "entity_unknown")


class BuildReportTests(unittest.TestCase):
    def test_aggregates_only_allowed_domains(self):
        report = producer.build_report(SAMPLE_STATES, generated_at=datetime(2026, 9, 10, tzinfo=timezone.utc))
        self.assertNotIn("sensor", report["domains"])
        self.assertNotIn("person", report["domains"])
        self.assertNotIn("scene", report["domains"])

    def test_light_domain_counts_are_correct_and_consistent(self):
        report = producer.build_report(SAMPLE_STATES, generated_at=datetime(2026, 9, 10, tzinfo=timezone.utc))
        light = report["domains"]["light"]
        self.assertEqual(light["entity_total"], 3)
        self.assertEqual(light["entity_on"], 1)
        self.assertEqual(light["entity_off"], 1)
        self.assertEqual(light["entity_unavailable"], 1)
        self.assertEqual(light["status"], "warning")

    def test_automation_domain_reuses_same_schema(self):
        report = producer.build_report(SAMPLE_STATES, generated_at=datetime(2026, 9, 10, tzinfo=timezone.utc))
        automation = report["domains"]["automation"]
        self.assertEqual(automation["entity_on"], 1)
        self.assertEqual(automation["entity_off"], 1)

    def test_unseen_domain_is_reported_as_unknown_coverage_not_zero_counts(self):
        report = producer.build_report(SAMPLE_STATES, generated_at=datetime(2026, 9, 10, tzinfo=timezone.utc))
        switch = report["domains"]["switch"]
        self.assertEqual(switch["coverage"], [])
        self.assertIsNone(switch["entity_total"])

    def test_report_passes_the_contract_validator(self):
        import sys

        sys.path.insert(0, str(ROOT / "services/aster-agent"))
        from home_assistant_report import get_home_assistant_report

        report = producer.build_report(SAMPLE_STATES)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "latest.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            result = get_home_assistant_report(path)
        self.assertNotIn("error", result)
        self.assertEqual(result["domains"]["light"]["entity_on"], 1)

    def test_entity_ids_never_appear_in_the_written_report(self):
        report = producer.build_report(SAMPLE_STATES, generated_at=datetime(2026, 9, 10, tzinfo=timezone.utc))
        serialized = json.dumps(report)
        self.assertNotIn("light.hall", serialized)
        self.assertNotIn("front_door", serialized)
        self.assertNotIn("jason", serialized)


class TokenAndWriteTests(unittest.TestCase):
    def test_rejects_group_or_other_readable_token_file(self):
        with tempfile.TemporaryDirectory() as directory:
            token_path = Path(directory) / "token"
            token_path.write_text("secret-token", encoding="utf-8")
            token_path.chmod(0o640)
            with patch.object(producer, "TOKEN_FILE", token_path):
                with self.assertRaises(ValueError):
                    producer._read_token()

    def test_reads_a_correctly_permissioned_token_file(self):
        with tempfile.TemporaryDirectory() as directory:
            token_path = Path(directory) / "token"
            token_path.write_text("secret-token\n", encoding="utf-8")
            token_path.chmod(0o600)
            with patch.object(producer, "TOKEN_FILE", token_path):
                self.assertEqual(producer._read_token(), "secret-token")

    def test_write_report_is_atomic_and_mode_restricted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reports/latest.json"
            producer.write_report({"schema_version": 1}, path)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["schema_version"], 1)

    def test_main_writes_no_secret_on_fetch_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reports/latest.json"
            with (
                patch.object(producer, "REPORT_PATH", path),
                patch.object(producer, "_read_token", return_value="secret-token"),
                patch.object(producer, "_fetch_states", side_effect=OSError("connection refused")),
            ):
                self.assertEqual(producer.main(), 1)
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
