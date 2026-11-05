import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location(
    "render_qwen_candidate", ROOT / "render_qwen_candidate.py"
)
candidate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(candidate)


FAKE_BINARY = """#!/usr/bin/env python3
import sys, time, wave
args = sys.argv[1:]
output = args[args.index('-o') + 1]
mode = open(__file__ + '.mode').read().strip()
if mode == 'timeout':
    open(output, 'wb').write(b'partial')
    time.sleep(5)
if mode == 'failure':
    open(output, 'wb').write(b'partial')
    raise SystemExit(2)
with wave.open(output, 'wb') as audio:
    audio.setnchannels(1)
    audio.setsampwidth(2)
    audio.setframerate(24000)
    audio.writeframes(b'\\0\\0' * 24000)
"""


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class QwenCandidateTests(unittest.TestCase):
    def fixture(self, root, mode="success"):
        binary = root / "qwen-tts"
        binary.write_text(FAKE_BINARY)
        binary.chmod(0o700)
        Path(str(binary) + ".mode").write_text(mode)
        model, codec = root / "model.gguf", root / "codec.gguf"
        reference_wav, reference_text = root / "reference.wav", root / "reference.txt"
        for path, content in ((model, b"model"), (codec, b"codec"),
                              (reference_wav, b"reference-wav")):
            path.write_bytes(content)
        reference_text.write_text("synthetic reference\n")
        plan = root / "plan.json"
        plan.write_text(json.dumps({
            "schema": "aster-tts-experiment-plan.v1",
            "passages": [{"id": "sample", "normalized_text": "A short sample.",
                          "normalized_sha256": hashlib.sha256(b"A short sample.").hexdigest()}],
        }))
        config = root / "config.json"
        config.write_text(json.dumps({
            "id": "fake-qwen", "mode": "base-clone", "seed": 7,
            "language": "English", "artifact_pins": {
                "binary_sha256": digest(binary), "model_sha256": digest(model),
                "codec_sha256": digest(codec),
                "reference_wav_sha256": digest(reference_wav),
                "reference_text_sha256": digest(reference_text),
            },
        }))
        return plan, config, binary, model, codec, reference_wav, reference_text

    def call(self, root, mode="success", timeout=10):
        values = self.fixture(root, mode)
        output = root / "output"
        result = candidate.render(*values[:2], output, *values[2:], "CPU", "sample", (1,), timeout)
        return output, result

    def test_success_is_complete_and_repeat_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            values = self.fixture(root)
            output = root / "output"
            result = candidate.render(*values[:2], output, *values[2:],
                                      "CPU", "sample", (1,), 10)
            self.assertEqual(result["renders"], ["sample-r1"])
            self.assertTrue((output / "sample-r1.wav").is_file())
            with self.assertRaises(FileExistsError):
                candidate.render(*values[:2], output, *values[2:], "CPU", "sample", (1,), 10)

    def test_corrupt_model_is_rejected_before_effect(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            values = self.fixture(root)
            values[3].write_bytes(b"corrupt")
            with self.assertRaisesRegex(ValueError, "model pin mismatch"):
                candidate.render(*values[:2], root / "output", *values[2:],
                                 "CPU", "sample", (1,), 10)

    def test_failed_render_removes_partial_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(RuntimeError, "exit 2"):
                output, _ = self.call(root, "failure")
            self.assertFalse(any(root.glob("output/*.partial")))

    def test_timeout_removes_partial_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                output, _ = self.call(root, "timeout", timeout=1)
            self.assertFalse(any(root.glob("output/*.partial")))


if __name__ == "__main__":
    unittest.main()
