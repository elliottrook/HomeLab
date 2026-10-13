import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import transport_a1_holdout_probe as transport
import holdout_answer_capture as capture


class TransportTests(unittest.TestCase):
    def test_source_files_are_pinned_before_remote_call(self):
        sources = {name: path.read_bytes() for name, path in transport.SOURCES.items()}
        transport.validate_sources(sources)
        modified = dict(sources)
        modified["holdout_answer_9b_adapter"] += b"\n# changed\n"
        with self.assertRaisesRegex(ValueError, "source digest mismatch"):
            transport.validate_sources(modified)

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

    def test_unexpected_primary_write_failure_seals_private_fallback(self):
        with tempfile.TemporaryDirectory() as dirname:
            target = Path(dirname) / "run"
            capture.reserve_private(target)
            real_open = os.open
            real_mkdtemp = tempfile.mkdtemp
            calls = 0

            def fail_primary_once(path, flags, mode=0o777):
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise PermissionError("synthetic primary write failure")
                return real_open(path, flags, mode)

            with patch.object(transport.os, "open", side_effect=fail_primary_once), \
                    patch.object(transport.tempfile, "mkdtemp",
                                 side_effect=lambda *, prefix, dir: real_mkdtemp(prefix=prefix, dir=dirname)):
                actual, digest = transport.seal_stdout(target, '{"fictional":"answer"}\n')
            self.assertNotEqual(actual, target)
            self.assertEqual(digest, hashlib.sha256((actual / "raw-attempts.json").read_bytes()).hexdigest())
            self.assertEqual(actual.stat().st_mode & 0o777, 0o700)
            self.assertEqual((actual / "raw-attempts.json").stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
