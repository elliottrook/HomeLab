import unittest
from dataclasses import replace

from application_b60_prelease import (
    BACKUP_SOURCE, MAC_SUBSET_SOURCE, RUNTIME_SOURCE, TRUENAS_SOURCE,
    BackupObservation, LeaseWindowObservation, MacSubsetObservation,
    PreLeaseSourceError, RuntimeObservation, TrueNASObservation,
    produce_prelease,
)


class Sources:
    def __init__(self):
        self.b = BackupObservation(BACKUP_SOURCE, "2026-10-18", 100, "application-chain:1", True)
        self.t = TrueNASObservation(TRUENAS_SOURCE, "2026-10-18", 101, True, True)
        self.m = MacSubsetObservation(MAC_SUBSET_SOURCE, "2026-10-18", ("104", "110", "116"), 102, True)
        self.r = RuntimeObservation(RUNTIME_SOURCE, "2026-10-18", "llama.cpp b11429 SYCL/Level Zero", True, True, True, True)
        self.w = LeaseWindowObservation("lease-1", 2, 110, 120, 121, 300)
    def backup(self): return self.b
    def truenas(self): return self.t
    def mac_subset(self): return self.m
    def runtime(self): return self.r
    def window(self): return self.w


class ApplicationB60PreLeaseTests(unittest.TestCase):
    def test_binds_all_fixed_sources_to_one_prelease(self):
        value = produce_prelease(Sources(), cycle="2026-10-18")
        self.assertEqual(value.lease_id, "lease-1")
        self.assertEqual(value.backup_receipt, "application-chain:1")
        self.assertEqual(value.restore_start_epoch, 121)

    def test_rejects_stale_or_wrong_source(self):
        for attr, replacement in (
            ("b", BackupObservation("caller", "2026-10-18", 100, "application-chain:1", True)),
            ("t", TrueNASObservation(TRUENAS_SOURCE, "2026-10-17", 101, True, True)),
            ("m", MacSubsetObservation(MAC_SUBSET_SOURCE, "2026-10-18", ("104",), 102, True)),
        ):
            with self.subTest(attr=attr):
                source = Sources(); setattr(source, attr, replacement)
                with self.assertRaises(PreLeaseSourceError):
                    produce_prelease(source, cycle="2026-10-18")

    def test_rejects_fabricated_runtime_or_partial_backup(self):
        source = Sources()
        source.r = replace(source.r, verified=False)
        with self.assertRaisesRegex(PreLeaseSourceError, "attestation"):
            produce_prelease(source, cycle="2026-10-18")
        source = Sources()
        source.b = replace(source.b, receipt="arbitrary-digest")
        with self.assertRaisesRegex(PreLeaseSourceError, "application-bound"):
            produce_prelease(source, cycle="2026-10-18")

    def test_rejects_invalid_window(self):
        source = Sources()
        source.w = replace(source.w, restore_start_epoch=110)
        with self.assertRaisesRegex(PreLeaseSourceError, "window"):
            produce_prelease(source, cycle="2026-10-18")


if __name__ == "__main__":
    unittest.main()
