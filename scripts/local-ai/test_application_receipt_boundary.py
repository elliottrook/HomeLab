import unittest

from application_receipt_boundary import ApplicationReceipt, CONSUMERS, MODE, SCHEMA, validate


class ApplicationReceiptBoundaryTests(unittest.TestCase):
    def receipt(self, **changes):
        value = ApplicationReceipt(SCHEMA, MODE, "lease-1", 4, "application-backup:x", 300,
            "llama.cpp b11429 SYCL/Level Zero", True, True, True, CONSUMERS, True,
            "a" * 64, 1904, 1, 19104, True, True, True)
        return ApplicationReceipt(**{**value.__dict__, **changes})

    def test_accepts_complete_host_receipt(self):
        validate(self.receipt(), expected_lease_id="lease-1", expected_generation=4, now_epoch=200)

    def test_rejects_receipt_without_exclusive_or_ipv4_proof(self):
        for field in ("exclusive_backend_claim", "backend_listener_ipv4_only"):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "backend"):
                    validate(self.receipt(**{field: False}), expected_lease_id="lease-1", expected_generation=4, now_epoch=200)

    def test_rejects_past_deadline_and_wrong_identity(self):
        with self.assertRaisesRegex(ValueError, "deadline"):
            validate(self.receipt(), expected_lease_id="lease-1", expected_generation=4, now_epoch=301)
        with self.assertRaisesRegex(ValueError, "identity"):
            validate(self.receipt(), expected_lease_id="other", expected_generation=4, now_epoch=200)
