import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import nlu_k2_sealed_macbook_wrapper_v1 as wrapper


def digest(raw): return hashlib.sha256(raw).hexdigest()


class Completed:
    def __init__(self, returncode, stdout):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = b""


class K2SealedMacBookWrapperTests(unittest.TestCase):
    def fixture(self, root):
        runtime = root / "runtime"; runtime.mkdir(mode=0o700)
        corpus = root / "corpus.json"; corpus.write_bytes(b"corpus")
        evaluation = root / "evaluation.json"; evaluation.write_bytes(b"evaluation")
        os.chmod(corpus, 0o600); os.chmod(evaluation, 0o600)
        pins = {}
        for name in wrapper.RUNTIME_PINS:
            raw = (name + "\n").encode(); (runtime / name).write_bytes(raw)
            os.chmod(runtime / name, 0o600); pins[name] = digest(raw)
        attempts = root / "attempts"; attempts.mkdir(mode=0o700)
        return runtime, corpus, evaluation, attempts, pins

    def test_one_shortlist_and_one_evaluation_with_private_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime, corpus, evaluation, attempts, pins = self.fixture(root)
            calls = []
            def run(command, **_kwargs):
                calls.append(command)
                if len(calls) == 1:
                    Path(command[-1]).write_bytes(b"private shortlist")
                    os.chmod(command[-1], 0o600)
                    return Completed(0, json.dumps({
                        "schema": "aster-nlu-k2-sealed-shortlist-summary.v1",
                        "dimension": 300, "evaluation_rows": 32,
                        "authority": "not-granted"}).encode())
                values = dict(zip(command[3::2], command[4::2]))
                records = Path(values["--records"]); metrics = Path(values["--metrics"])
                journal = Path(values["--journal"])
                records.write_bytes(b"records"); metrics.write_bytes(b"metrics")
                journal.write_bytes(b"journal")
                for path in (records, metrics, journal): os.chmod(path, 0o600)
                return Completed(0, json.dumps({"state": "complete", "cases": 32,
                    "model_requests": 32, "status": "pass",
                    "records_sha256": digest(b"records"),
                    "metrics_sha256": digest(b"metrics"),
                    "authority": "not-granted"}).encode())
            with mock.patch.object(wrapper, "RUNTIME_PINS", pins), \
                 mock.patch.object(wrapper, "CORPUS_SHA256", digest(b"corpus")), \
                 mock.patch.object(wrapper, "EVALUATION_SHA256", digest(b"evaluation")):
                result = wrapper.run(
                    session_id="k2-sealed-0123456789abcdef", relay_token="r" * 32,
                    runtime_root=runtime, attempt_parent=attempts, corpus=corpus,
                    evaluation=evaluation, command_runner=run)
            self.assertEqual("complete", result["state"])
            self.assertEqual(2, len(calls))
            attempt = attempts / "k2-sealed-0123456789abcdef"
            self.assertFalse((attempt / "relay-token").exists())
            self.assertEqual(0o600, (attempt / "metrics.json").stat().st_mode & 0o777)

    def test_failure_removes_nonce_without_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime, corpus, evaluation, attempts, pins = self.fixture(root)
            calls = []
            def fail(command, **_kwargs): calls.append(command); return Completed(1, b"")
            with mock.patch.object(wrapper, "RUNTIME_PINS", pins), \
                 mock.patch.object(wrapper, "CORPUS_SHA256", digest(b"corpus")), \
                 mock.patch.object(wrapper, "EVALUATION_SHA256", digest(b"evaluation")):
                with self.assertRaises(wrapper.WrapperError):
                    wrapper.run(session_id="k2-sealed-0123456789abcdef",
                                relay_token="r" * 32, runtime_root=runtime,
                                attempt_parent=attempts, corpus=corpus,
                                evaluation=evaluation, command_runner=fail)
            self.assertEqual(1, len(calls))
            self.assertFalse((attempts / "k2-sealed-0123456789abcdef" /
                              "relay-token").exists())

    def test_runtime_or_input_drift_fails_before_effect(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime, corpus, evaluation, attempts, pins = self.fixture(root)
            (runtime / next(iter(pins))).write_bytes(b"changed")
            with mock.patch.object(wrapper, "RUNTIME_PINS", pins), \
                 mock.patch.object(wrapper, "CORPUS_SHA256", digest(b"corpus")), \
                 mock.patch.object(wrapper, "EVALUATION_SHA256", digest(b"evaluation")):
                with self.assertRaises(wrapper.WrapperError):
                    wrapper.run(session_id="k2-sealed-0123456789abcdef",
                                relay_token="r" * 32, runtime_root=runtime,
                                attempt_parent=attempts, corpus=corpus,
                                evaluation=evaluation)


if __name__ == "__main__":
    unittest.main()
