import json
import unittest
from pathlib import Path

import nlu_local_model_adapter as adapter


HERE = Path(__file__).parent
POLICY = HERE / "fixtures" / "nlu-local-model-policy-v1.json"


def response(value, *, finish_reason="stop"):
    return json.dumps({
        "choices": [{
            "message": {"role": "assistant", "content": json.dumps(value)},
            "finish_reason": finish_reason,
        }]
    }).encode()


class NluLocalModelAdapterTests(unittest.TestCase):
    def setUp(self):
        self.value = {
            "request_family": "read-only-investigation",
            "sensitivity": "internal",
            "capability_needs": ["lab.read"],
            "ambiguity": "clear",
            "disposition": "route",
            "reason": "understood",
        }

    def test_payload_is_deterministic_local_schema_request(self):
        first = adapter.build_payload("Check the lab status")
        self.assertEqual(first, adapter.build_payload("Check the lab status"))
        payload = json.loads(first)
        self.assertEqual("aster-qwen3.5-9b", payload["model"])
        self.assertEqual(0, payload["temperature"])
        self.assertFalse(payload["stream"])
        self.assertNotIn("tools", payload)
        self.assertEqual(False, "authorization" in payload["response_format"]["schema"]["properties"])
        policy = json.loads(POLICY.read_bytes())
        self.assertEqual(adapter.MODEL, policy["model"])
        self.assertEqual(adapter.SYSTEM_POLICY, policy["system_policy"])
        self.assertEqual(adapter.RESPONSE_SCHEMA, policy["response_schema"])
        self.assertEqual(0, policy["temperature"])
        self.assertEqual(256, policy["max_tokens"])
        self.assertEqual("disabled", policy["tool_mode"])
        self.assertEqual("not-granted", policy["authority"])

    def test_valid_response_becomes_content_free_no_authority_record(self):
        raw = response(self.value)
        record = adapter.result_record(
            case_id="case-1",
            principal_ref="fixture-principal",
            engine_sha256="1" * 64,
            policy_sha256="2" * 64,
            latency_seconds=1.25,
            response_raw=raw,
        )
        encoded = json.dumps(record)
        self.assertNotIn("Check the lab status", encoded)
        self.assertNotIn(json.dumps(self.value), encoded)
        self.assertEqual("not-granted", record["interpretation"]["authorization"])
        self.assertIsNone(record["interpretation"]["confidence"])

    def test_extra_fields_duplicates_and_unclean_finish_fail_closed(self):
        changed = dict(self.value, route="codex")
        with self.assertRaisesRegex(ValueError, "fixed schema"):
            adapter.parse_response(response(changed))
        duplicate_content = json.dumps(self.value).replace(
            '"sensitivity": "internal"',
            '"sensitivity": "internal", "sensitivity": "public"',
        )
        duplicate = json.dumps({
            "choices": [{
                "message": {"role": "assistant", "content": duplicate_content},
                "finish_reason": "stop",
            }]
        }).encode()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            adapter.parse_response(duplicate)
        with self.assertRaisesRegex(ValueError, "finish cleanly"):
            adapter.parse_response(response(self.value, finish_reason="length"))

    def test_semantic_mismatches_and_unknown_capabilities_fail_closed(self):
        invalid = [
            dict(self.value, ambiguity="ambiguous"),
            dict(self.value, capability_needs=["shell.execute"]),
            dict(self.value, request_family="unsupported"),
            dict(self.value, sensitivity="secret"),
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                adapter.parse_response(response(value))

    def test_envelope_is_exact_and_digests_are_validated(self):
        with self.assertRaisesRegex(ValueError, "envelope"):
            adapter.parse_response(json.dumps({"choices": [], "usage": {}}).encode())
        with self.assertRaisesRegex(ValueError, "engine digest"):
            adapter.result_record(
                case_id="case-1",
                principal_ref="fixture-principal",
                engine_sha256="bad",
                policy_sha256="2" * 64,
                latency_seconds=0,
                response_raw=response(self.value),
            )


if __name__ == "__main__":
    unittest.main()
