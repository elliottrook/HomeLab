import unittest
from contract import Job, route
from probe import MetadataClient


def event(method, **extra):
    return {"method": method, "params": {"threadId": "t", "turnId": "u", **extra}}


def answer(text="Verified result", ident="a"):
    return event("item/completed", item={"id": ident, "type": "agentMessage",
                 "phase": "final_answer", "text": text})


def end(status="completed"):
    return event("turn/completed", turn={"id": "u", "status": status})


class ContractTests(unittest.TestCase):
    def test_fast_path_survives_all_providers_unavailable(self):
        for intent in ("lights", "timer", "service_status", "doctor_report"):
            self.assertEqual(route(intent), "deterministic")

    def test_no_implicit_cloud_or_paid_fallback(self):
        self.assertEqual(route("sysadmin_investigation"), "blocked_privacy")
        for mode in (None, "apiKey", "chatgptAuthTokens"):
            self.assertEqual(route("explicit_codex", cloud_allowed=True,
                                   auth_mode=mode), "blocked_subscription_auth")

    def test_local_only_overrides_codex_request(self):
        self.assertEqual(route("explicit_codex", local_only=True, cloud_allowed=True,
                               auth_mode="chatgpt", capacity_available=True), "blocked_privacy")

    def test_capacity_and_unknown(self):
        self.assertEqual(route("explicit_codex", cloud_allowed=True,
                               auth_mode="chatgpt"), "queued_capacity")
        self.assertEqual(route("explicit_codex", cloud_allowed=True,
                               auth_mode="chatgpt", capacity_available=True), "codex")
        self.assertEqual(route("unknown"), "clarify")

    def test_final_requires_terminal_success(self):
        j = Job("j", "t", "u")
        j.apply(answer())
        self.assertEqual(j.final_text, "")
        j.apply(end())
        self.assertEqual((j.state, j.final_text), ("completed", "Verified result"))

    def test_failures_do_not_publish_partial_answer(self):
        for status in ("failed", "interrupted"):
            j = Job("j", "t", "u"); j.apply(answer()); j.apply(end(status))
            self.assertEqual(j.final_text, "")
            self.assertEqual(j.state, status)

    def test_empty_or_unknown_phase_is_not_a_usable_final(self):
        for text, phase in (("   ", "final_answer"), ("interim", None)):
            j = Job("j", "t", "u")
            m = answer(text); m["params"]["item"]["phase"] = phase
            j.apply(m); j.apply(end())
            self.assertEqual(j.state, "missing_final")
            self.assertEqual(j.final_text, "")

    def test_wrong_thread_turn_and_reasoning_ignored(self):
        j = Job("j", "t", "u")
        m = answer(); m["params"]["turnId"] = "wrong"; j.apply(m)
        m = answer(); m["params"]["threadId"] = "wrong"; j.apply(m)
        j.apply(event("item/reasoning/textDelta", delta="private"))
        j.apply(end())
        self.assertEqual(j.state, "missing_final")
        self.assertEqual(j.final_items, {})

    def test_cancel_is_not_completion(self):
        j = Job("j", "t", "u")
        self.assertEqual(j.cancel()["method"], "turn/interrupt")
        self.assertEqual(j.state, "cancel_requested")
        j.disconnect(); self.assertEqual(j.state, "unknown")
        j.apply(end("interrupted")); self.assertEqual(j.state, "interrupted")

    def test_duplicate_final_is_not_duplicated(self):
        j = Job("j", "t", "u")
        j.apply(answer()); j.apply(answer()); j.apply(end())
        self.assertEqual(j.final_text, "Verified result")

    def test_conflicting_duplicate_and_oversized_fail_closed(self):
        j = Job("j", "t", "u"); j.apply(answer()); j.apply(answer("different"))
        j.apply(end()); self.assertEqual(j.state, "invalid_output")
        j = Job("j", "t", "u", limit=2); j.apply(answer()); j.apply(end())
        self.assertEqual(j.state, "output_limit")

    def test_server_request_never_approved(self):
        j = Job("j", "t", "u")
        reply = j.apply({"id": 5, "method": "item/commandExecution/requestApproval"})
        self.assertIn("error", reply)
        j.apply(answer()); j.apply(end())
        self.assertEqual(j.state, "blocked_server_request")
        self.assertEqual(j.final_text, "")

    def test_metadata_probe_cannot_start_work(self):
        c = object.__new__(MetadataClient)
        for method in ("thread/start", "turn/start", "account/login/start"):
            with self.assertRaises(ValueError):
                c.call(method, {})


if __name__ == "__main__":
    unittest.main()
