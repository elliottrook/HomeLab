import importlib.util
import json
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PATH = Path(__file__).parent / "custom_components" / "aster_home_registry" / "contract.py"
SPEC = importlib.util.spec_from_file_location("aster_home_contract", PATH)
CONTRACT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTRACT)


class ContractTests(unittest.TestCase):
    def test_exact_three_values(self):
        result = CONTRACT.build_snapshot(
            {CONTRACT.LIGHT: "off", CONTRACT.HALL: "20.64", CONTRACT.OUTSIDE: "68"},
            {CONTRACT.HALL: "°C", CONTRACT.OUTSIDE: "°F"})
        self.assertEqual(result["lights"], [{"alias": "laundry lights", "state": "off"}])
        self.assertEqual(result["temperatures"], [
            {"alias": "hall temperature", "value": 20.6, "unit": "°C"},
            {"alias": "outside temperature", "value": 68.0, "unit": "°F"}])
        self.assertEqual(result["schema_version"], 2)

    def test_unknown_and_unavailable_fail_closed(self):
        for value in ("unknown", "unavailable", "nan", "999"):
            result = CONTRACT.build_snapshot({CONTRACT.LIGHT: value, CONTRACT.HALL: value},
                                             {CONTRACT.HALL: "°C"})
            self.assertEqual(result["lights"], [])
            self.assertEqual(result["temperatures"], [])
        self.assertEqual(CONTRACT.build_snapshot({}, {})["temperatures"], [])

    def test_approved_closet_temperature_with_unavailable_hue_sensors(self):
        result = CONTRACT.build_snapshot(
            {CONTRACT.HALL: "unavailable", CONTRACT.OUTSIDE: "unavailable",
             CONTRACT.CLOSET: "17.0"},
            {CONTRACT.HALL: "°C", CONTRACT.OUTSIDE: "°C", CONTRACT.CLOSET: "°C"})
        self.assertEqual(result["temperatures"], [
            {"alias": "closet temperature", "value": 17.0, "unit": "°C"}])

    def test_rejects_unreviewed_ids(self):
        with self.assertRaises(ValueError):
            CONTRACT.build_snapshot({"lock.front": "locked"}, {})
        with self.assertRaises(ValueError):
            CONTRACT.build_snapshot({}, {"sensor.other": "°C"})

    def test_private_atomic_output(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(CONTRACT, "OUTPUT", Path(directory) / "latest.json"):
                CONTRACT.write_atomic(CONTRACT.build_snapshot({}, {}))
                target = Path(directory) / "latest.json"
                self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
                self.assertEqual(json.loads(target.read_text())["schema_version"], 2)


if __name__ == "__main__":
    unittest.main()
