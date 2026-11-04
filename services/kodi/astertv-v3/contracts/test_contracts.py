import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text())


class WorkflowContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = load("v2-workflows.json")
        self.workflows = {row["id"]: row for row in self.contract["workflows"]}

    def test_release_and_required_workflows_are_pinned(self):
        self.assertEqual(self.contract["schema"], 1)
        self.assertRegex(self.contract["baseline_release_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            set(self.workflows),
            {"media", "movie_details", "tv_series", "youtube", "music",
             "books", "requests", "news", "home_and_cameras", "settings"},
        )

    def test_focus_controls_and_actions_are_nonempty_and_unique(self):
        for workflow in self.workflows.values():
            controls = workflow["controls"]
            actions = workflow["required_actions"]
            self.assertIn(workflow["initial_focus"], controls, workflow["id"])
            self.assertEqual(len(controls), len(set(controls)), workflow["id"])
            self.assertEqual(len(actions), len(set(actions)), workflow["id"])
            self.assertTrue(workflow["back_target"])

    def test_known_v2_regressions_are_explicitly_blocked(self):
        global_rules = set(self.contract["global_invariants"])
        self.assertIn("details_precede_movie_playback", global_rules)
        self.assertIn("home_is_not_an_implicit_back_target", global_rules)
        self.assertIn("no_queue_or_recovery_confirmation_for_normal_playback", global_rules)
        self.assertIn("return_restores_top_pill_navigation",
                      self.workflows["youtube"]["required_actions"])
        self.assertIn("content_can_return_to_top_pills",
                      self.workflows["music"]["required_actions"])
        self.assertIn("season_zero_hidden", self.workflows["tv_series"]["invariants"])
        self.assertIn("retained_completed_queue_does_not_block_playback",
                      self.workflows["news"]["required_actions"])


class AccountContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = load("account-profile-contract.json")

    def test_registry_contains_only_metadata_and_opaque_mappings(self):
        allowed = set(self.contract["registry_fields"] + self.contract["profile_fields"]
                      + self.contract["service_mapping_fields"])
        forbidden = set(self.contract["forbidden_fields"])
        self.assertTrue(forbidden.isdisjoint(allowed))
        self.assertIn("opaque_subject_id", allowed)
        self.assertNotIn("credential", allowed)

    def test_guest_fails_closed_for_private_surfaces(self):
        denied = set(self.contract["guest_denied"])
        self.assertTrue({"personal_youtube", "requests_submit", "books_private",
                         "home_control", "cameras", "aster_private_context"}
                        <= denied)
        self.assertEqual(self.contract["malformed_registry_fallback"]
                         if "malformed_registry_fallback" in self.contract
                         else self.contract["recovery_rules"][-1],
                         "malformed_registry_fails_to_restricted_guest")


class CapabilityContractTests(unittest.TestCase):
    def setUp(self):
        self.schema = load("client-capability-profile.schema.json")
        self.jen = load("client-capability-jen.json")

    def test_profile_is_capability_not_hostname_driven(self):
        self.assertNotIn("hostname", self.schema["properties"])
        self.assertIn("profile_is_selected_by_measured_capability_not_hostname",
                      self.schema["x-aster-invariants"])

    def test_security_and_recovery_cannot_be_optional(self):
        self.assertIn(
            "privacy_navigation_recovery_and_credential_isolation_are_not_optional",
            self.schema["x-aster-invariants"],
        )
        self.assertTrue({"video", "audio", "resources", "ui"}
                        <= set(self.schema["required"]))

    def test_jen_profile_encodes_measured_limits_not_identity_branches(self):
        self.assertEqual(self.jen["profile_id"], "low-spec-1080p-haswell")
        self.assertEqual(self.jen["video"]["max_width"], 1920)
        self.assertEqual(self.jen["video"]["max_height"], 1080)
        self.assertEqual(self.jen["video"]["max_bitrate_mbps"], 18)
        self.assertNotIn("hevc", self.jen["video"]["hardware_codecs"])
        self.assertIn("direct-4k-hevc", self.jen["video"]["excluded_classes"])
        self.assertEqual(self.jen["audio"]["passthrough_formats"], [])
        self.assertNotIn("hostname", json.dumps(self.jen).casefold())


class BrokerContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = load("aster-broker-contract.json")

    def test_allowlist_and_high_risk_denials_are_explicit(self):
        allowed = set(self.contract["allowed_intents"])
        denied = set(self.contract["denied_capabilities"])
        self.assertEqual(
            allowed,
            {"media.search", "page.open", "playback.play_named",
             "playback.resume_named", "news.play", "news.open",
             "home.alias_execute"},
        )
        self.assertTrue({"shell", "credential_read", "arbitrary_json_rpc",
                         "arbitrary_home_assistant_service", "general_aster_tools"}
                        <= denied)

    def test_context_and_audit_exclude_sensitive_content(self):
        context = set(self.contract["context_fields"])
        forbidden = set(self.contract["forbidden_context_fields"])
        self.assertTrue(context.isdisjoint(forbidden))
        self.assertNotIn("utterance", self.contract["audit_fields"])
        self.assertIn("utterance", self.contract["audit_excludes"])
        self.assertLessEqual(self.contract["limits"]["result_count"], 12)
        self.assertLessEqual(self.contract["limits"]["max_alias_targets"], 1)


class FixturePrivacyTests(unittest.TestCase):
    def test_contracts_have_no_private_addresses_or_secret_assignments(self):
        combined = "\n".join(
            path.read_text() for path in ROOT.glob("*.json")
        )
        self.assertIsNone(re.search(r"\b(?:10|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d+\.\d+\b", combined))
        self.assertIsNone(re.search(
            r'(?i)(?:password|token|api_key|secret)\s*[=:]\s*["\'][^"\']+["\']',
            combined,
        ))


if __name__ == "__main__":
    unittest.main()
