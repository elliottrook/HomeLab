import unittest

from application_b60_lease import (
    ACCEPTED_BACKEND,
    ALLOWED_CONSUMER_SERVICES,
    ApplicationLeaseError,
    ApplicationLeaseReceipt,
    SidecarObservation,
    command_for,
    validate,
)


class ApplicationB60LeaseTests(unittest.TestCase):
    def receipt(self, **changes):
        value = ApplicationLeaseReceipt(
            mode="application-b60-exclusive-v1", lease_id="lease-1", generation=2,
            backup_receipt="application-chain:abc", backend_identity=ACCEPTED_BACKEND,
            llama_service_active=True, exclusive_backend_claim=True, backend_listener_ipv4_only=True,
            consumers_quiesced=ALLOWED_CONSUMER_SERVICES,
            news_quiesced=True,
            sidecar=SidecarObservation("a" * 64, 3003, 1, 19120, True, True, True, True),
        )
        return ApplicationLeaseReceipt(**{**value.__dict__, **changes})

    def test_allows_only_non_backend_consumer_effects(self):
        self.assertEqual(command_for("104", "aster-agent.service", "stop")[0:3], ("pct", "exec", "104"))
        with self.assertRaises(ApplicationLeaseError):
            command_for("110", "aster-llama.service", "stop")

    def test_accepts_distinct_application_receipt(self):
        validate(self.receipt(), expected_lease_id="lease-1", expected_generation=2)

    def test_rejects_full_stop_receipt_or_missing_sidecar_proof(self):
        with self.assertRaisesRegex(ApplicationLeaseError, "full-stop"):
            validate(self.receipt(mode="full-stop-v1"), expected_lease_id="lease-1", expected_generation=2)
        with self.assertRaisesRegex(ApplicationLeaseError, "source-bound"):
            validate(self.receipt(backup_receipt="full-stop:abc"), expected_lease_id="lease-1", expected_generation=2)
        with self.assertRaisesRegex(ApplicationLeaseError, "sidecar"):
            validate(self.receipt(sidecar=SidecarObservation("a" * 64, 3003, 2, 19120, True, True, True, True)), expected_lease_id="lease-1", expected_generation=2)

    def test_rejects_idle_only_backend_claim(self):
        with self.assertRaisesRegex(ApplicationLeaseError, "exclusively"):
            validate(self.receipt(exclusive_backend_claim=False), expected_lease_id="lease-1", expected_generation=2)


if __name__ == "__main__":
    unittest.main()
