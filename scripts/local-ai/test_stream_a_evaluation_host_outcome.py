import json
import subprocess
import unittest

from stream_a_evaluation_guest_outcome import SCHEMA as GUEST_SCHEMA
from stream_a_evaluation_host_outcome import (
    COMMANDS, SCHEMA, HostOutcomeError, HostOutcomeVerifier,
)


def completed(value, code=0, stderr=""):
    return subprocess.CompletedProcess((), code, json.dumps(value) + "\n", stderr)


class HostOutcomeTests(unittest.TestCase):
    def test_host_projection_schema_matches_guest_projection(self):
        self.assertEqual(SCHEMA, GUEST_SCHEMA)

    def value(self, name="d4-candidate-h"):
        return {"schema": SCHEMA, "name": name, "journal_digest": "a" * 64,
                "result_digest": "b" * 64,
                "calls": 12 if name == "d4-candidate-h" else 60}

    def test_exact_guest_command_becomes_typed_outcome(self):
        calls = []
        def runner(command, **kwargs):
            calls.append((command, kwargs)); return completed(self.value())
        outcome = HostOutcomeVerifier(runner=runner)("d4-candidate-h", 71)
        self.assertEqual(calls[0][0], COMMANDS["d4-candidate-h"])
        self.assertEqual(outcome.elapsed_seconds, 71)
        self.assertEqual(outcome.calls, 12)

    def test_foreign_schema_duplicate_keys_and_failure_reject(self):
        bad = self.value(); bad["name"] = "m3-nlu-calibration"
        with self.assertRaises(HostOutcomeError):
            HostOutcomeVerifier(runner=lambda *_a, **_k: completed(bad))(
                "d4-candidate-h", 1)
        duplicate = '{"schema":"x","schema":"y"}\n'
        result = subprocess.CompletedProcess((), 0, duplicate, "")
        with self.assertRaises(HostOutcomeError):
            HostOutcomeVerifier(runner=lambda *_a, **_k: result)("d4-candidate-h", 1)
        with self.assertRaises(HostOutcomeError):
            HostOutcomeVerifier(runner=lambda *_a, **_k: completed(self.value(), 1))(
                "d4-candidate-h", 1)

    def test_invalid_elapsed_and_call_bound_reject(self):
        with self.assertRaises(HostOutcomeError):
            HostOutcomeVerifier(runner=lambda *_a, **_k: completed(self.value()))(
                "d4-candidate-h", -1)
        value = self.value(); value["calls"] = 37
        with self.assertRaises(HostOutcomeError):
            HostOutcomeVerifier(runner=lambda *_a, **_k: completed(value))(
                "d4-candidate-h", 1)


if __name__ == "__main__":
    unittest.main()
