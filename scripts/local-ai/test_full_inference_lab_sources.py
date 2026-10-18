import unittest

from application_b60_lease import ACCEPTED_BACKEND
from full_inference_lab_sources import AcceptedBaseline, FullDrainSourceError, FullDrainSourceProducer, TrustedOwnerAttestation


class FullInferenceLabSourcesTests(unittest.TestCase):
    def test_rejects_unattested_owner_before_host_probes(self):
        calls = []
        producer = FullDrainSourceProducer(lambda command, timeout: calls.append(command) or (0, ""),
            AcceptedBaseline("a" * 64, "b" * 64, "c" * 64), TrustedOwnerAttestation("", ""),
            wall_clock=lambda: 1000)
        with self.assertRaisesRegex(FullDrainSourceError, "attestation"):
            producer.collect(cycle="2026_10_18", session_start_epoch=1000)
        self.assertEqual(calls, [])

    def test_baseline_identity_is_explicit(self):
        baseline = AcceptedBaseline("a" * 64, "b" * 64, "c" * 64)
        self.assertEqual(ACCEPTED_BACKEND, "llama.cpp b11429 SYCL/Level Zero")
        self.assertEqual(len(baseline.model_sha256), 64)


if __name__ == "__main__":
    unittest.main()
