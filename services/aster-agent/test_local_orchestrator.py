import unittest

from local_orchestrator import (
    AnalysisContext, AnalysisDraft, Claim, Evidence, HouseholdDecision, HouseholdState,
    ProviderRegistrySnapshot, RecordingAdapter, RegistryRecordingAdapter, decide_analysis,
    execute_household, plan_household, validate_grounding,
)


STATE = HouseholdState(
    timers=("pasta",), rooms=("kitchen", "office"),
    entities=("kitchen lights", "office lamp"), media_available=True,
)


class HouseholdTests(unittest.TestCase):
    def test_exact_timer_reaches_recording_adapter(self):
        plan = plan_household("Set an egg timer for 6.5 minutes", STATE)
        adapter = RecordingAdapter()
        execute_household(plan, adapter)
        self.assertEqual(adapter.calls, [("timer.create", {"seconds": 390, "label": "egg"})])

    def test_conflicting_timer_cannot_execute(self):
        plan = plan_household("Set a timer for 5 minutes, make that 10 minutes", STATE)
        adapter = RecordingAdapter()
        with self.assertRaises(ValueError):
            execute_household(plan, adapter)
        self.assertEqual(adapter.calls, [])

    def test_ambiguous_alarm_cannot_execute(self):
        self.assertEqual(plan_household("Set an alarm for four", STATE).status, "clarify")

    def test_media_and_home_require_exact_registered_targets(self):
        media = plan_household("Play jazz in kitchen", STATE)
        home = plan_household("Turn off the kitchen lights", STATE)
        self.assertEqual(media.arguments, {"query": "jazz", "target": "kitchen"})
        self.assertEqual(home.arguments, {"target": "kitchen lights", "state": "off"})
        self.assertEqual(plan_household("Turn on the lamp", STATE).status, "clarify")

    def test_non_plan_is_rejected_even_if_capability_is_supplied(self):
        adapter = RecordingAdapter()
        with self.assertRaises(ValueError):
            execute_household(HouseholdDecision("clarify", "home.control", {"state": "on"}), adapter)

    def test_registry_snapshot_drives_planning_and_records_no_effect(self):
        snapshot = ProviderRegistrySnapshot(1, "fixture-20261010", ("pasta",), ("kitchen",),
                                            ("kitchen lights",), ("fixture-media",))
        decision = plan_household("Turn off the kitchen lights", snapshot.household_state())
        adapter = RegistryRecordingAdapter(snapshot)
        result = execute_household(decision, adapter)
        self.assertTrue(result["recorded"])
        self.assertFalse(result["effect_permitted"])
        self.assertEqual(result["snapshot_id"], "fixture-20261010")

    def test_registry_adapter_rejects_stale_schema_and_unknown_binding(self):
        with self.assertRaises(ValueError):
            ProviderRegistrySnapshot(2, "future").validate()
        snapshot = ProviderRegistrySnapshot(1, "fixture", entities=("kitchen lights",))
        adapter = RegistryRecordingAdapter(snapshot)
        with self.assertRaises(ValueError):
            adapter.apply("home.control", {"target": "office lamp", "state": "on"})
        self.assertEqual(adapter.calls, [])

    def test_registry_adapter_enforces_call_limit_and_capability_schema(self):
        snapshot = ProviderRegistrySnapshot(1, "fixture", timers=("pasta",))
        adapter = RegistryRecordingAdapter(snapshot, max_calls=1)
        adapter.apply("timer.cancel", {"label": "pasta"})
        with self.assertRaises(RuntimeError):
            adapter.apply("timer.cancel", {"label": "pasta"})
        with self.assertRaises(ValueError):
            RegistryRecordingAdapter(snapshot).apply("shell.run", {"command": "true"})


class GroundingTests(unittest.TestCase):
    def setUp(self):
        self.evidence = (
            Evidence("status", "Service alpha is active. Health status is ok at 12:00.", "internal"),
        )
        self.draft = AnalysisDraft(
            "Service alpha active; health ok at 12:00.",
            (Claim("Service alpha active health ok at 12:00", ("status",), "Service alpha is active. Health status is ok at 12:00."),),
        )

    def test_supported_claim_and_summary_pass(self):
        self.assertEqual(validate_grounding(self.draft, self.evidence), [])
        decision = decide_analysis(AnalysisContext(), self.draft, self.evidence)
        self.assertEqual((decision.outcome, decision.route), ("answer", "local"))

    def test_invented_model_prose_is_not_forwarded_to_cloud(self):
        draft = AnalysisDraft(
            "Kernel logs show disconnects.",
            (Claim("Kernel logs show disconnects", ("status",), "Service alpha is active."),),
        )
        decision = decide_analysis(AnalysisContext(deep_sysadmin=True), draft, self.evidence)
        self.assertEqual((decision.outcome, decision.route), ("escalate", "cloud_sysadmin"))
        self.assertNotIn("disconnects", repr(decision.cloud_packet))
        self.assertIn("Service alpha is active.", repr(decision.cloud_packet))

    def test_nonexistent_quote_and_source_fail_closed(self):
        draft = AnalysisDraft("Service failed", (Claim("Service failed", ("missing",), "failed"),))
        failures = validate_grounding(draft, self.evidence)
        self.assertTrue(any("unknown evidence" in item for item in failures))

    def test_untrusted_summary_is_not_emitted(self):
        draft = AnalysisDraft("Service active after network failure", self.draft.claims)
        decision = decide_analysis(AnalysisContext(), draft, self.evidence)
        self.assertNotIn("network failure", decision.grounded_facts)

    def test_conflict_is_code_owned_clarification(self):
        decision = decide_analysis(AnalysisContext(has_conflict=True), self.draft, self.evidence)
        self.assertEqual((decision.outcome, decision.route), ("clarify", "local"))

    def test_missing_material_evidence_clarifies_without_model_claim(self):
        empty = AnalysisDraft("", ())
        decision = decide_analysis(AnalysisContext(missing_material_evidence=True), empty, self.evidence)
        self.assertEqual((decision.outcome, decision.route), ("clarify", "local"))

    def test_retrieval_injection_and_family_boundary_are_code_owned(self):
        injection = decide_analysis(AnalysisContext(retrieved_instruction=True), self.draft, self.evidence)
        family = decide_analysis(AnalysisContext(cross_family=True), self.draft, self.evidence)
        self.assertEqual((injection.outcome, family.outcome), ("refuse", "refuse"))

    def test_grounded_internal_sysadmin_packet_is_sanitized(self):
        decision = decide_analysis(AnalysisContext(deep_sysadmin=True), self.draft, self.evidence)
        self.assertEqual((decision.outcome, decision.route), ("escalate", "cloud_sysadmin"))
        self.assertNotIn("statement", repr(decision.cloud_packet))

    def test_private_evidence_never_enters_cloud_packet(self):
        private = (Evidence("mail", "Plumber confirmed tomorrow at 09:00.", "private"),)
        draft = AnalysisDraft("Plumber confirmed tomorrow 09:00", (Claim("Plumber confirmed tomorrow 09:00", ("mail",), "Plumber confirmed tomorrow at 09:00."),))
        decision = decide_analysis(AnalysisContext(deep_sysadmin=True), draft, private)
        self.assertEqual((decision.outcome, decision.route), ("blocked", "none"))


if __name__ == "__main__":
    unittest.main()
