"""Offline A1 orchestration fixtures; no host receipt or model call is made."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
from a1_admitted_batch import A1_TEST_ENDPOINT, run_admitted_batch
from client_display_clock import ClientDisplayClock
import holdout_answer_capture as holdout

PROFILE = {
    "schema": "aster-full-path-development-profile.v1",
    "result_class": "stream-a-candidate-path-baseline",
    "tool_mode": "disabled",
    "max_calls": 20,
    "batch_max_wall_seconds": 1200,
    "per_request_timeout_seconds": 60,
    "case_fixture_sha256": hashlib.sha256(b"fictional sealed cases").hexdigest(),
    "headless_client_sha256": hashlib.sha256(Path(__file__).with_name("a1_headless_client.py").read_bytes()).hexdigest(),
    "client_capture_sha256": hashlib.sha256(Path(__file__).with_name("a1_full_path_capture.py").read_bytes()).hexdigest(),
}


class A1AdmittedBatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)
        self.cases = self.root / "cases.jsonl"
        self.cases.write_bytes(b"fictional sealed cases")
        self.cases.chmod(0o600)
        self.token = self.root / "ingress.key"
        self.token.write_bytes(b"fictional-unique-test-key")
        self.token.chmod(0o600)
        self.profile = self.root / "profile.json"
        self.profile.write_text(json.dumps(PROFILE, sort_keys=True))
        self.pin = hashlib.sha256(self.profile.read_bytes()).hexdigest()
        self.output = self.root / "new-evidence"

    def run_batch(self, admission, transport, capture):
        with patch("a1_admitted_batch.load_cases", return_value=[{"id": "fictional"}]):
            return run_admitted_batch(
                cases_path=self.cases, profile_path=self.profile,
                expected_profile_sha256=self.pin,
                ingress_token_path=self.token,
                endpoint=A1_TEST_ENDPOINT,
                output_dir=self.output, assert_admitted=admission,
                transport=transport, capture=capture)

    def test_live_admission_rechecked_before_each_transport(self):
        calls = []

        def admission(profile_sha256, endpoint):
            self.assertEqual(profile_sha256, self.pin)
            self.assertEqual(endpoint, A1_TEST_ENDPOINT)
            calls.append("admit")
            return True

        def transport(case, **kwargs):
            self.assertEqual(kwargs["timeout_s"], 19)
            self.assertEqual(kwargs["ingress_token"], b"fictional-unique-test-key")
            calls.append("transport")
            return "fictional answer", object()

        def capture(raw, pin, out, callback, *, max_wall_s):
            self.assertEqual(max_wall_s, 1200)
            self.assertEqual(raw, b"fictional sealed cases")
            self.assertEqual(pin, self.pin)
            self.assertEqual(out, self.output)
            self.assertEqual(callback({"id": "fictional"}, timeout_s=19)[0],
                             "fictional answer")
            self.assertEqual(callback({"id": "fictional"}, timeout_s=19)[0],
                             "fictional answer")
            return {"planned": 20, "completed": 2}

        self.assertEqual(self.run_batch(admission, transport, capture)["completed"], 2)
        self.assertEqual(calls, ["admit", "admit", "transport", "admit", "transport"])

    def test_lost_admission_blocks_transport(self):
        calls = []

        def admission(_, endpoint):
            self.assertEqual(endpoint, A1_TEST_ENDPOINT)
            calls.append("admit")
            if len(calls) == 2:
                raise RuntimeError("lease lost")
            return True

        def transport(*args, **kwargs):
            calls.append("transport")

        def capture(raw, pin, out, callback, **kwargs):
            callback({"id": "fictional"}, timeout_s=60)

        with self.assertRaisesRegex(RuntimeError, "lease lost"):
            self.run_batch(admission, transport, capture)
        self.assertEqual(calls, ["admit", "admit"])

    def test_drift_or_unprotected_key_blocks_before_admission(self):
        def admission(_, endpoint):
            self.fail("admission should not run")

        self.token.chmod(0o644)
        with self.assertRaisesRegex(ValueError, "custody"):
            self.run_batch(admission, lambda *a, **k: None, lambda *a, **k: None)
        self.token.chmod(0o600)
        self.profile.write_text("{}")
        with self.assertRaisesRegex(ValueError, "profile drift"):
            self.run_batch(admission, lambda *a, **k: None, lambda *a, **k: None)

    def test_false_preview_receipt_cannot_start_capture(self):
        def capture(*args, **kwargs):
            self.fail("a false preview must not start evidence or transport")

        with self.assertRaisesRegex(RuntimeError, "admission unavailable"):
            self.run_batch(lambda *_: False, lambda *a, **k: None, capture)

    def test_client_source_drift_blocks_before_admission(self):
        profile = dict(PROFILE, headless_client_sha256="0" * 64)
        self.profile.write_text(json.dumps(profile, sort_keys=True))
        self.pin = hashlib.sha256(self.profile.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, "client source drift"):
            self.run_batch(lambda *_: self.fail("admission should not run"),
                           lambda *a, **k: None, lambda *a, **k: None)

    def test_fictional_twenty_case_pipeline_seals_private_output(self):
        cases = []
        for index in range(20):
            cases.append({
                "id": f"fictional-{index:02d}", "class": "synthetic",
                "fictional_user_request": f"Explain fictional event {index}.",
                "frozen_clock": "2026-01-01T00:00:00Z",
                "synthetic_source_records": [],
                "private_context_locality_constraint": "local_only",
                "permitted_capability_set": [], "maximum_tool_scope": "none",
            })
        raw = b"".join((json.dumps(row, sort_keys=True) + "\n").encode() for row in cases)
        self.cases.write_bytes(raw)
        profile = dict(PROFILE, case_fixture_sha256=hashlib.sha256(raw).hexdigest())
        self.profile.write_text(json.dumps(profile, sort_keys=True))
        self.pin = hashlib.sha256(self.profile.read_bytes()).hexdigest()
        calls = []

        def admission(_, endpoint):
            self.assertEqual(endpoint, A1_TEST_ENDPOINT)
            calls.append("admit")
            return True

        def transport(case, **kwargs):
            calls.append("transport")
            self.assertLessEqual(kwargs["timeout_s"], 60)
            pending = ClientDisplayClock()
            pending.response_identity("a" * 32, 200)
            return "Synthetic answer.", pending

        with patch.object(holdout, "CASE_SHA256", hashlib.sha256(raw).hexdigest()):
            summary = run_admitted_batch(
                cases_path=self.cases, profile_path=self.profile,
                expected_profile_sha256=self.pin,
                ingress_token_path=self.token,
                endpoint=A1_TEST_ENDPOINT,
                output_dir=self.output, assert_admitted=admission,
                transport=transport)
        self.assertEqual((summary["completed"], summary["client_clock_rows"]), (20, 20))
        self.assertEqual((calls.count("admit"), calls.count("transport")), (21, 20))
        for name in ("attempt-journal.jsonl", "raw-attempts.json", "client-clock.jsonl"):
            self.assertEqual(self.output.joinpath(name).stat().st_mode & 0o777, 0o600)

    def test_wrong_local_endpoint_blocks_before_admission_or_evidence(self):
        with patch("a1_admitted_batch.load_cases") as load:
            with self.assertRaisesRegex(ValueError, "pinned isolated sidecar"):
                run_admitted_batch(
                    cases_path=self.cases, profile_path=self.profile,
                    expected_profile_sha256=self.pin,
                    ingress_token_path=self.token,
                    endpoint="http://192.168.70.12:11435/v1/chat/completions",
                    output_dir=self.output,
                    assert_admitted=lambda *_: self.fail("must not admit"),
                    transport=lambda *a, **k: self.fail("must not send"),
                    capture=lambda *a, **k: self.fail("must not write"))
            load.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_non_pinned_endpoint_blocks_before_admission(self):
        with self.assertRaisesRegex(ValueError, "pinned isolated sidecar"):
            run_admitted_batch(
                cases_path=self.cases, profile_path=self.profile,
                expected_profile_sha256=self.pin,
                ingress_token_path=self.token,
                endpoint="http://192.168.70.11:19104/v1/chat/completions",
                output_dir=self.output, assert_admitted=lambda *_: True,
                transport=lambda *a, **k: None,
                capture=lambda *a, **k: None)


if __name__ == "__main__":
    unittest.main()
