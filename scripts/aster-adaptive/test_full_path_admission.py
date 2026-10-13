"""Synthetic preflight tests; no host, lease, endpoint or model is contacted."""
import sys
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))
from full_path_admission import AdmissionDenied, CASE_SHA256, admit

NOW = datetime(2026, 10, 14, 3, 20, tzinfo=ZoneInfo("America/Vancouver"))
A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64


def card():
    return {"schema_version": "aster-full-path-admission.v0",
            "case_sha256": CASE_SHA256, "profile_sha256": A,
            "gateway_sha256": B, "scorer_sha256": C,
            "accepted_restore_sha256": D,
            "max_calls": 20, "max_wall_s": 1200,
            "per_request_timeout_s": 60, "output_token_cap": 256,
            "temperature": 0, "reasoning_mode": "off", "tool_mode": "disabled",
            "client_boundary": "headless_synthetic_display",
            "candidate_id": "synthetic-candidate", "lease_id": "test-lease-20261014"}


def observed():
    return {
        "backup": {"source": "platform-backup-chain",
                   "completed_at": "2026-10-14T03:05:00-07:00",
                   "archive_complete": True, "mirror_verified": True,
                   "receipt_sha256": A},
        "lease": {"source": "platform-host-controller", "id": "test-lease-20261014",
                  "state": "leased", "issued_at": "2026-10-14T03:10:00-07:00",
                  "expires_at": "2026-10-14T04:10:00-07:00",
                  "host_lock_held": True, "owner": "aster-stream-a"},
        "watchdog": {"source": "proxmox-systemd", "lease_id": "test-lease-20261014",
                     "armed": True, "deadline_at": "2026-10-14T04:05:00-07:00",
                     "independent_of_mini": True},
        "consumers": {"source": "platform-host-controller", "news_quiesced": True,
                      "other_ai_quiesced": True, "no_new_starts": True},
        "gateway": {"source": "aster-test-adapter", "profile_sha256": B,
                    "model_profile_sha256": A, "scorer_sha256": C,
                    "accepted_restore_sha256": D,
                    "auth_scope": "test_only", "egress": "lan_only",
                    "test_only": True, "tools_disabled": True,
                    "production_route_unchanged": True,
                    "candidate_id": "synthetic-candidate"},
        "evidence": {"source": "aster-owner-custody", "owner_only": True,
                     "writable": True, "new_empty_run_directory": True},
    }


class FullPathAdmissionTests(unittest.TestCase):
    def deny(self, expected, change, *, change_card=False, now=NOW):
        requested, live = card(), observed()
        change(requested if change_card else live)
        with self.assertRaisesRegex(AdmissionDenied, expected):
            admit(requested, live, now=now)

    def test_complete_snapshot_passes_without_claiming_authority(self):
        result = admit(card(), observed(), now=NOW)
        self.assertEqual(result["state"], "preflight_passed_not_authority")
        self.assertEqual(result["latest_batch_end_at"], "2026-10-14T03:50:00-07:00")
        self.assertNotIn("http", str(result))

    def test_missing_watchdog_and_wrong_lease_fail_closed(self):
        self.deny("watchdog_unverified", lambda x: x["watchdog"].update(armed=False))
        self.deny("watchdog_unverified", lambda x: x["watchdog"].update(lease_id="other-lease"))
        self.deny("lease_unverified", lambda x: x["lease"].update(host_lock_held=False))
        self.deny("lease_unverified", lambda x: x["lease"].update(owner="other-lane"))

    def test_backup_must_be_source_bound_and_same_night(self):
        self.deny("backup_unverified", lambda x: x["backup"].update(mirror_verified=False))
        self.deny("stale_or_unbound_receipt", lambda x: x["backup"].update(
            completed_at="2026-10-13T03:05:00-07:00"))
        self.deny("stale_or_unbound_receipt", lambda x: x["lease"].update(
            issued_at="2026-10-14T03:00:00-07:00"))

    def test_consumer_and_gateway_isolation_are_required(self):
        self.deny("consumer_conflict", lambda x: x["consumers"].update(news_quiesced=False))
        self.deny("consumer_conflict", lambda x: x["consumers"].update(no_new_starts=False))
        self.deny("gateway_unverified", lambda x: x["gateway"].update(
            production_route_unchanged=False))
        self.deny("gateway_unverified", lambda x: x["gateway"].update(tools_disabled=False))
        self.deny("gateway_unverified", lambda x: x["gateway"].update(egress="cloud"))

    def test_exact_candidate_and_restore_pins_are_required(self):
        self.deny("gateway_unverified", lambda x: x["gateway"].update(
            model_profile_sha256=B))
        self.deny("gateway_unverified", lambda x: x["gateway"].update(
            accepted_restore_sha256=A))
        self.deny("gateway_unverified", lambda x: x["gateway"].update(
            candidate_id="other-candidate"))

    def test_evidence_must_be_new_private_and_writable(self):
        self.deny("evidence_unready", lambda x: x["evidence"].update(writable=False))
        self.deny("evidence_unready", lambda x: x["evidence"].update(
            new_empty_run_directory=False))

    def test_deadlines_leave_restoration_budget(self):
        self.deny("insufficient_recovery_time", lambda x: x["watchdog"].update(
            deadline_at="2026-10-14T03:40:00-07:00"))
        self.deny("insufficient_recovery_time", lambda x: x["lease"].update(
            expires_at="2026-10-14T03:40:00-07:00"))
        self.deny("insufficient_recovery_time", lambda x: x, now=datetime(
            2026, 10, 14, 4, 15, tzinfo=ZoneInfo("America/Vancouver")))

    def test_no_tools_and_pinned_cases(self):
        self.deny("invalid_card", lambda x: x.update(tool_mode="read_only"), change_card=True)
        self.deny("invalid_card", lambda x: x.update(case_sha256=B), change_card=True)
        self.deny("invalid_card", lambda x: x.update(max_calls=19), change_card=True)
        self.deny("invalid_card", lambda x: x.update(client_boundary="native_companion"),
                  change_card=True)

    def test_unexpected_fields_cannot_carry_request_content(self):
        self.deny("invalid_card", lambda x: x.update(prompt="private"), change_card=True)
        self.deny("missing_observation", lambda x: x.update(answer="private"))


if __name__ == "__main__":
    unittest.main()
