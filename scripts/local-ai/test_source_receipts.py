import unittest

from admission_gate import EXPECTED_BACKUP_SOURCE, EXPECTED_CONSUMERS, AdmissionEvidenceError
from source_receipts import EXPECTED_QUIESCENCE_SOURCE, BackupSourceReceipt, QuiescenceSourceReceipt, compose_candidate_evidence


class SourceReceiptTests(unittest.TestCase):
    def backup(self, **changes):
        values = dict(
            source=EXPECTED_BACKUP_SOURCE,
            chain_id=EXPECTED_BACKUP_SOURCE,
            completed_minute=220,
            integrity_receipt="sha256:guest-chain",
            integrity_verified=True,
            source_observed=True,
        )
        values.update(changes)
        return BackupSourceReceipt(**values)

    def quiescence(self, **changes):
        values = dict(
            source=EXPECTED_QUIESCENCE_SOURCE,
            observed_minute=221,
            consumers=EXPECTED_CONSUMERS,
            news_quiesced=True,
            no_new_starts=True,
            source_observed=True,
        )
        values.update(changes)
        return QuiescenceSourceReceipt(**values)

    def test_composes_complete_candidate_receipts(self):
        result = compose_candidate_evidence(self.backup(), self.quiescence(), now_minute=221, window_end_minute=255)
        self.assertEqual(result.backup_receipt, "sha256:guest-chain")
        self.assertTrue(result.news_quiesced)

    def test_rejects_unverified_integrity_or_new_start_activity(self):
        with self.assertRaisesRegex(AdmissionEvidenceError, "backup"):
            compose_candidate_evidence(self.backup(integrity_verified=False), self.quiescence(), now_minute=221, window_end_minute=255)
        with self.assertRaisesRegex(AdmissionEvidenceError, "quiescence"):
            compose_candidate_evidence(self.backup(), self.quiescence(no_new_starts=False), now_minute=221, window_end_minute=255)

    def test_rejects_wrong_source_and_consumer_set(self):
        with self.assertRaisesRegex(AdmissionEvidenceError, "source"):
            compose_candidate_evidence(self.backup(source="truenas"), self.quiescence(), now_minute=221, window_end_minute=255)
        with self.assertRaisesRegex(AdmissionEvidenceError, "consumer"):
            compose_candidate_evidence(self.backup(), self.quiescence(consumers=("aster-agent",)), now_minute=221, window_end_minute=255)


if __name__ == "__main__":
    unittest.main()
