import unittest

from admission_gate import (
    EXPECTED_BACKUP_SOURCE,
    EXPECTED_CONSUMERS,
    AdmissionEvidence,
    AdmissionEvidenceError,
    require_aster_benchmark,
    validate_evidence_shape,
)


class AdmissionGateTests(unittest.TestCase):
    def evidence(self, **changes):
        values = dict(
            source=EXPECTED_BACKUP_SOURCE,
            backup_receipt="backup-chain-sha256",
            backup_completed_minute=220,
            backup_verified=True,
            consumers_quiesced=EXPECTED_CONSUMERS,
            news_quiesced=True,
            source_observed=True,
        )
        values.update(changes)
        return AdmissionEvidence(**values)

    def test_requires_source_bound_evidence_before_aster_benchmark(self):
        with self.assertRaisesRegex(AdmissionEvidenceError, "source-bound"):
            require_aster_benchmark(None, now_minute=221, window_end_minute=255)

    def test_shape_guard_accepts_complete_candidate_shape_but_benchmark_stays_blocked(self):
        self.assertEqual(validate_evidence_shape(self.evidence(), now_minute=221, window_end_minute=255), "backup-chain-sha256")
        with self.assertRaisesRegex(AdmissionEvidenceError, "trusted source-adapter"):
            require_aster_benchmark(self.evidence(), now_minute=221, window_end_minute=255)
        with self.assertRaisesRegex(AdmissionEvidenceError, "trusted source-adapter"):
            require_aster_benchmark(self.evidence(adapter_attested=True), now_minute=221, window_end_minute=255)
        for changes, message in (
            ({"source_observed": False}, "independently"),
            ({"backup_verified": False}, "backup"),
            ({"news_quiesced": False}, "News"),
            ({"consumers_quiesced": ("aster-agent",)}, "consumers"),
        ):
            with self.subTest(changes=changes), self.assertRaisesRegex(AdmissionEvidenceError, message):
                require_aster_benchmark(self.evidence(**changes), now_minute=221, window_end_minute=255)


if __name__ == "__main__":
    unittest.main()
