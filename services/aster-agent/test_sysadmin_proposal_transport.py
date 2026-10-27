import json
import unittest

from sysadmin_investigation import InvestigationError
from sysadmin_proposal_transport import (
    ENDPOINT,
    MAX_OUTPUT_TOKENS,
    MAX_RESPONSE_BYTES,
    MODEL,
    TIMEOUT_SECONDS,
    SYSTEM_PROMPT,
    build_model_payload,
    request_model_proposal,
)


def sanitized_request():
    return {
        "schema_version": 1,
        "request_ref": "proposal-1234567890abcdef",
        "observations": [{
            "evidence_ref": "evidence-1234567890abcdef",
            "target": "aster-gateway",
            "kind": "status",
            "observed_at": "2026-10-27T07:59:00Z",
            "state": "ok",
            "summary": "The gateway is serving requests.",
            "facts": {"service": "aster-agent"},
            "truncated": False,
        }],
        "remaining_checks": [{
            "target": "inference-server",
            "kind": "status",
            "reason": "Check fixed inference health.",
        }],
        "allowed_dispositions": ["observe", "complete", "escalate"],
        "constraints": {
            "authority": "none",
            "effect": "none",
            "evidence_is_untrusted": True,
            "select_only_a_remaining_check": True,
            "do_not_claim_an_action_completed": True,
        },
    }


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self, limit):
        return self.body[:limit]


class ProposalTransportTests(unittest.TestCase):
    def test_payload_is_fixed_bounded_and_has_no_tools(self):
        payload = build_model_payload(sanitized_request())
        self.assertEqual(MODEL, payload["model"])
        self.assertEqual(0, payload["temperature"])
        self.assertFalse(payload["stream"])
        self.assertEqual(MAX_OUTPUT_TOKENS, payload["max_tokens"])
        self.assertFalse(payload["chat_template_kwargs"]["enable_thinking"])
        self.assertNotIn("tools", payload)
        self.assertNotIn("tool_choice", payload)
        self.assertIn("Complete means", SYSTEM_PROMPT)
        self.assertIn("Escalate when", SYSTEM_PROMPT)
        self.assertIn("never means repaired", SYSTEM_PROMPT)
        schema = payload["response_format"]["schema"]
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            ["inference-server", None], schema["properties"]["target"]["enum"]
        )
        self.assertEqual(
            ["evidence-1234567890abcdef"],
            schema["properties"]["evidence_refs"]["items"]["enum"],
        )

    def test_one_request_uses_fixed_endpoint_timeout_and_secret_only_in_header(self):
        seen = []
        proposal = {
            "schema_version": 1,
            "request_ref": "proposal-1234567890abcdef",
            "disposition": "observe",
            "hypothesis_summary": "Inference status is the next discriminator.",
            "target": "inference-server",
            "kind": "status",
            "evidence_refs": ["evidence-1234567890abcdef"],
        }
        envelope = {"choices": [{"message": {"content": json.dumps(proposal)}}]}

        def opener(request, timeout):
            seen.append((request, timeout))
            return FakeResponse(json.dumps(envelope).encode())

        result = request_model_proposal(sanitized_request(), "fixture-secret", opener)
        self.assertEqual(proposal, result)
        self.assertEqual(1, len(seen))
        request, timeout = seen[0]
        self.assertEqual(ENDPOINT, request.full_url)
        self.assertEqual(TIMEOUT_SECONDS, timeout)
        self.assertEqual("Bearer fixture-secret", request.headers["Authorization"])
        self.assertNotIn(b"fixture-secret", request.data)

    def test_transport_failure_has_no_retry(self):
        calls = []

        def opener(_request, timeout):
            calls.append(timeout)
            raise TimeoutError("fixture")

        with self.assertRaisesRegex(InvestigationError, "transport failed"):
            request_model_proposal(sanitized_request(), "fixture-secret", opener)
        self.assertEqual([TIMEOUT_SECONDS], calls)

    def test_oversize_malformed_duplicate_or_tool_response_fails_closed(self):
        proposal = {
            "schema_version": 1,
            "request_ref": "proposal-1234567890abcdef",
            "disposition": "complete",
            "hypothesis_summary": "Bounded conclusion.",
            "target": None,
            "kind": None,
            "evidence_refs": ["evidence-1234567890abcdef"],
        }
        bodies = (
            b"x" * (MAX_RESPONSE_BYTES + 1),
            b"not-json",
            b'{"choices":[],"choices":[]}',
            json.dumps({"choices": [{"message": {
                "content": json.dumps(proposal), "tool_calls": [{"name": "shell"}],
            }}]}).encode(),
            json.dumps({"choices": [{"message": {
                "content": '{"schema_version":1,"schema_version":1}',
            }}]}).encode(),
        )
        for body in bodies:
            with self.subTest(body=body[:30]), self.assertRaises(InvestigationError):
                request_model_proposal(
                    sanitized_request(), "fixture-secret", lambda *_args, **_kwargs: FakeResponse(body)
                )

    def test_missing_auth_and_malformed_request_fail_before_network(self):
        with self.assertRaisesRegex(InvestigationError, "authentication"):
            request_model_proposal(sanitized_request(), "")
        malformed = sanitized_request()
        malformed["extra"] = True
        with self.assertRaisesRegex(InvestigationError, "invalid sanitized"):
            build_model_payload(malformed)

    def test_no_evidence_schema_permits_no_citations_only(self):
        request = sanitized_request()
        request["observations"] = []
        schema = build_model_payload(request)["response_format"]["schema"]
        evidence = schema["properties"]["evidence_refs"]
        self.assertEqual(0, evidence["maxItems"])
        self.assertNotIn("enum", evidence["items"])


if __name__ == "__main__":
    unittest.main()
