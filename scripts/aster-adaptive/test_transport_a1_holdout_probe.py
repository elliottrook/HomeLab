import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import transport_a1_holdout_probe as transport
import holdout_answer_capture as capture


class TransportTests(unittest.TestCase):
    def test_profile_pin_and_label_free_program(self):
        cases_raw = b'{"id":"fictional"}\n'
        profile = {"case_fixture_sha256": hashlib.sha256(cases_raw).hexdigest(),
                   "system_prompt_sha256": hashlib.sha256(transport.SYSTEM.encode()).hexdigest(),
                   "model_id": "aster-qwen3.5-9b", "tool_mode": "disabled",
                   "egress": "local", "per_request_timeout_seconds": 60,
                   "batch_max_wall_seconds": 600}
        profile_raw = json.dumps(profile).encode()
        with patch.object(transport, "PROFILE_SHA256", hashlib.sha256(profile_raw).hexdigest()), \
                patch.object(transport, "CASE_SHA256", hashlib.sha256(cases_raw).hexdigest()):
            transport.validate_profile(profile_raw, cases_raw)
            program = transport.remote_program(cases_raw, {"a1_9b_synthetic_answer_probe": b"x=1\n",
                                                   "holdout_answer_capture": b"x=2\n",
                                                   "holdout_answer_9b_adapter": b"x=3\n"})
        compile(program, "<remote-program>", "exec")
        self.assertNotIn("answer-key.jsonl", program)
        self.assertNotIn("review-receipt", program)
        with self.assertRaisesRegex(ValueError, "scope mismatch"):
            with patch.object(transport, "PROFILE_SHA256", hashlib.sha256(profile_raw).hexdigest()), \
                    patch.object(transport, "CASE_SHA256", hashlib.sha256(cases_raw).hexdigest()):
                transport.validate_profile(profile_raw, cases_raw + b"tamper")

    def test_raw_output_is_sealed_before_validation(self):
        with tempfile.TemporaryDirectory() as dirname:
            target = Path(dirname) / "run"
            capture.reserve_private(target)
            actual, digest = transport.seal_stdout(target, '{"fictional":"answer"}\n')
            self.assertEqual(actual, target)
            self.assertEqual(digest, hashlib.sha256((target / "raw-attempts.json").read_bytes()).hexdigest())
            self.assertEqual((target / "raw-attempts.json").stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
