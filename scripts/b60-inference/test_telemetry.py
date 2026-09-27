#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("b60_telemetry", HERE / "telemetry.py")
assert SPEC and SPEC.loader
telemetry = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(telemetry)


class TelemetryTests(unittest.TestCase):
    def setUp(self):
        self.text = (HERE / "fixtures/telemetry-snapshot.txt").read_text(encoding="utf-8")

    def test_snapshot_parses_to_schema_compatible_measurement(self):
        result = telemetry.measurement(telemetry.parse_snapshot(self.text))
        self.assertEqual(result["gpu_temperature_c"], 60.0)
        self.assertEqual(result["vram_used_bytes"], 13762772 * 1024)
        self.assertTrue(result["gpu_resident"])
        self.assertIsNone(result["gpu_frequency_mhz"])
        self.assertIsNone(result["gpu_power_w"])
        self.assertIsNone(result["cpu_fallback_detected"])

    def test_unknown_duplicate_and_secret_like_fields_are_rejected(self):
        for bad in (
            self.text + "unknown=1\n",
            self.text + "source_pid=442\n",
            self.text + "api_key=synthetic-not-a-real-key\n",
        ):
            with self.assertRaises(telemetry.TelemetryError):
                telemetry.parse_snapshot(bad)

    def test_impossible_ram_and_invalid_affinity_are_rejected(self):
        with self.assertRaises(telemetry.TelemetryError):
            telemetry.parse_snapshot(self.text.replace("ram_available_kib=7547627", "ram_available_kib=99999999"))
        with self.assertRaises(telemetry.TelemetryError):
            telemetry.parse_snapshot(self.text.replace("cpu_affinity=3,9,19,20", "cpu_affinity=all"))

    def test_cpu_fallback_requires_affirmative_evidence(self):
        snapshot = telemetry.parse_snapshot(self.text)
        accepted = "Vulkan0: Intel BMG G21; offloaded 65/65 layers to GPU"
        self.assertFalse(telemetry.classify_cpu_fallback(accepted, snapshot))
        self.assertTrue(telemetry.classify_cpu_fallback("CPU backend only; offloaded 0/65 layers", snapshot))
        self.assertIsNone(telemetry.classify_cpu_fallback("backend details unavailable", snapshot))


if __name__ == "__main__":
    unittest.main()
