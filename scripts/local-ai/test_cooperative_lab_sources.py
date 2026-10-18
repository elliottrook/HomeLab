import unittest
from cooperative_lab_sources import (SOURCES, CooperativeSourceError, HostWindow,
    produce_preflight)
from application_b60_host_sources import AttestedSource
from application_b60_lease import ACCEPTED_BACKEND


class CooperativeLabSourcesTests(unittest.TestCase):
    def bundle(self):
        payloads = {
            "backup": {"receipt": "application-chain:1"},
            "truenas": {"schedules_fixed": True},
            "mac_subset": {"guest_ids": ["104", "110", "116"]},
            "runtime": {"backend_identity": ACCEPTED_BACKEND, "gpu_visible": True,
                        "authentication_verified": True, "consumers_healthy": True,
                        "news_timers_active": True, "deny_new_starts_supported": True,
                        "direct_client_admission_enforced": False},
            "news": {"next_ingest_epoch": 2000},
        }
        return {name: AttestedSource(SOURCES[name], "cycle-1", 990, payload, "digest")
                for name, payload in payloads.items()}

    def test_produces_typed_preflight_from_complete_attested_bundle(self):
        value = produce_preflight(self.bundle(), cycle="cycle-1",
            window=HostWindow("lab-1", 1, 1000, 1000, 2800, 3700))
        self.assertEqual(value.backend_identity, ACCEPTED_BACKEND)
        self.assertEqual(value.next_news_ingest_epoch, 2000)

    def test_rejects_missing_or_untrusted_source(self):
        bundle = self.bundle()
        bundle.pop("runtime")
        with self.assertRaisesRegex(CooperativeSourceError, "incomplete"):
            produce_preflight(bundle, cycle="cycle-1",
                window=HostWindow("lab-1", 1, 1000, 1000, 2800, 3700))


if __name__ == "__main__":
    unittest.main()
