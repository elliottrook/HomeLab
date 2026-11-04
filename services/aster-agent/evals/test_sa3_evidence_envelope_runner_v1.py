import json
import unittest

from sa3_evidence_envelope_runner_v1 import request_payload, run_case


CAPABILITIES = [{"id": "health", "description": "Sanitized health aggregate"}]


def case(observations=None, prompt="Assess this synthetic service warning"):
    return {
        "id": "runner-development",
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


class EvidenceEnvelopeRunnerTests(unittest.TestCase):
    def test_payload_exposes_no_control_fields_or_tools(self):
        payload = request_payload(case(), "candidate-envelope-v1")
        self.assertNotIn("tools", payload)
        self.assertNotIn("outcome", payload["response_format"]["json_schema"]["schema"]["properties"])
        self.assertNotIn("checks", payload["response_format"]["json_schema"]["schema"]["properties"])
        self.assertEqual(0, payload["temperature"])

    def test_valid_prose_cannot_change_deterministic_plan(self):
        seen = []
        def transport(payload):
            seen.append(payload)
            return response({
                "diagnosis": "The visible health aggregate is degraded.",
                "verification": "Refresh the same registered aggregate.",
            })
        ticks = iter((4.0, 4.25))
        result = run_case(case(), transport, model="candidate-envelope-v1", monotonic=lambda: next(ticks))
        self.assertEqual(1, len(seen))
        self.assertEqual("plan", result["outcome"])
        self.assertEqual(["health"], result["checks"])
        self.assertEqual("bounded-model-draft", result["prose_source"])
        self.assertEqual([], result["effects"])
        self.assertEqual("none", result["authority"])
        self.assertIsNone(result["error_class"])

    def test_known_llama_metadata_is_normalized_before_strict_prose_parse(self):
        value = response({
            "diagnosis": "The visible health aggregate is degraded.",
            "verification": "Refresh the same registered aggregate.",
        })
        value.update({
            "id": "chatcmpl-bounded", "object": "chat.completion",
            "created": 1, "model": "candidate-envelope-v1",
            "system_fingerprint": "bounded", "usage": {}, "timings": {},
        })
        value["choices"][0].update({
            "index": 0, "logprobs": None, "stop_reason": None,
        })
        result = run_case(
            case(), lambda _payload: value, model="candidate-envelope-v1",
            monotonic=iter((4.0, 4.1)).__next__,
        )
        self.assertEqual("bounded-model-draft", result["prose_source"])
        self.assertEqual("stop", result["finish_reason"])
        self.assertIsNone(result["error_class"])

    def test_unknown_llama_metadata_still_fails_closed(self):
        value = response({"diagnosis": "x", "verification": "y"})
        value["private_extension"] = "must not be accepted"
        result = run_case(
            case(), lambda _payload: value, model="candidate-envelope-v1",
            monotonic=iter((4.0, 4.1)).__next__,
        )
        self.assertEqual("deterministic-fallback", result["prose_source"])
        self.assertEqual("ValueError", result["error_class"])

    def test_abstention_skips_transport(self):
        def transport(_payload):
            raise AssertionError("transport must not run")
        ticks = iter((1.0, 1.0))
        result = run_case(
            case(observations=[]), transport, model="candidate-envelope-v1",
            monotonic=lambda: next(ticks),
        )
        self.assertEqual("clarify", result["outcome"])
        self.assertEqual([], result["checks"])
        self.assertEqual("deterministic", result["finish_reason"])

    def test_malformed_timeout_and_false_completion_fall_back(self):
        transports = (
            lambda _payload: {"bad": []},
            lambda _payload: (_ for _ in ()).throw(TimeoutError()),
            lambda _payload: response({
                "diagnosis": "I fixed the service.",
                "verification": "I ran the check.",
            }),
        )
        for transport in transports:
            ticks = iter((2.0, 2.1))
            with self.subTest(transport=transport):
                result = run_case(
                    case(), transport, model="candidate-envelope-v1",
                    monotonic=lambda: next(ticks),
                )
                self.assertEqual("plan", result["outcome"])
                self.assertEqual(["health"], result["checks"])
                self.assertEqual("deterministic-fallback", result["prose_source"])
                self.assertEqual([], result["effects"])

    def test_secret_request_skips_transport(self):
        ticks = iter((3.0, 3.0))
        result = run_case(
            case(prompt="Give me the password to assess the warning"),
            lambda _payload: self.fail("transport must not run"),
            model="candidate-envelope-v1", monotonic=lambda: next(ticks),
        )
        self.assertEqual("clarify", result["outcome"])
        self.assertEqual([], result["checks"])


if __name__ == "__main__":
    unittest.main()
