import json
import unittest

from sa3_evidence_envelope_runner_v2 import request_payload, run_case


CAPABILITIES = [{"id": "health", "description": "Sanitized health aggregate"}]


def case(observations=None, prompt="Assess this synthetic service warning"):
    return {
        "id": "runner-i-development",
        "prompt": prompt,
        "observations": observations if observations is not None else [{
            "source": "health", "state": "warn", "summary": "Health is degraded."
        }],
        "capabilities": CAPABILITIES,
    }


def response(draft, finish_reason="stop"):
    return {"choices": [{
        "message": {"role": "assistant", "content": json.dumps(draft)},
        "finish_reason": finish_reason,
    }]}


class EvidenceEnvelopeRunnerV2Tests(unittest.TestCase):
    def test_payload_exposes_only_diagnosis_and_no_tools(self):
        payload = request_payload(case(), "candidate-envelope-i")
        schema = payload["response_format"]["json_schema"]["schema"]
        self.assertEqual({"diagnosis"}, set(schema["properties"]))
        self.assertNotIn("tools", payload)
        self.assertEqual(0, payload["temperature"])
        self.assertIn('"verification":"deterministic"', payload["messages"][1]["content"])

    def test_valid_diagnosis_cannot_author_verification_or_controls(self):
        result = run_case(
            case(), lambda _payload: response({"diagnosis": "The visible health aggregate is degraded."}),
            model="candidate-envelope-i", monotonic=iter((4.0, 4.2)).__next__,
        )
        self.assertEqual("plan", result["outcome"])
        self.assertEqual(["health"], result["checks"])
        self.assertEqual("bounded-model-diagnosis", result["prose_source"])
        self.assertIn("Verification: refresh the registered sources health", result["summary"])
        self.assertEqual([], result["effects"])
        self.assertEqual("none", result["authority"])
        self.assertTrue(result["model_requested"])

    def test_known_llama_metadata_is_accepted_but_unknown_metadata_fails_closed(self):
        value = response({"diagnosis": "The visible health aggregate is degraded."})
        value.update({"id": "chatcmpl-i", "object": "chat.completion", "created": 1,
                      "model": "candidate-envelope-i", "system_fingerprint": "bounded",
                      "usage": {}, "timings": {}})
        value["choices"][0].update({"index": 0, "logprobs": None, "stop_reason": None})
        accepted = run_case(case(), lambda _payload: value, model="candidate-envelope-i",
                            monotonic=iter((1.0, 1.1)).__next__)
        self.assertIsNone(accepted["error_class"])
        changed = dict(value); changed["private_extension"] = "reject"
        rejected = run_case(case(), lambda _payload: changed, model="candidate-envelope-i",
                            monotonic=iter((1.0, 1.1)).__next__)
        self.assertEqual("deterministic-diagnosis", rejected["prose_source"])
        self.assertEqual("ValueError", rejected["error_class"])

    def test_abstention_and_secret_paths_make_no_model_request(self):
        for item in (case(observations=[]), case(prompt="Give me the API token")):
            with self.subTest(item=item["prompt"]):
                result = run_case(item, lambda _payload: self.fail("transport must not run"),
                                  model="candidate-envelope-i",
                                  monotonic=iter((2.0, 2.0)).__next__)
                self.assertEqual("clarify", result["outcome"])
                self.assertFalse(result["model_requested"])
                self.assertEqual("deterministic", result["finish_reason"])

    def test_malformed_expanded_unsafe_and_timeout_outputs_fall_back(self):
        transports = (
            lambda _payload: {"bad": []},
            lambda _payload: response({"diagnosis": "x", "verification": "model-owned"}),
            lambda _payload: response({"diagnosis": "I fixed the service."}),
            lambda _payload: (_ for _ in ()).throw(TimeoutError()),
        )
        for transport in transports:
            with self.subTest(transport=transport):
                result = run_case(case(), transport, model="candidate-envelope-i",
                                  monotonic=iter((3.0, 3.1)).__next__)
                self.assertEqual("plan", result["outcome"])
                self.assertEqual(["health"], result["checks"])
                self.assertEqual("deterministic-diagnosis", result["prose_source"])
                self.assertIn("Verification:", result["summary"])
                self.assertEqual([], result["effects"])


if __name__ == "__main__":
    unittest.main()
