import importlib.util
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location("operator", Path(__file__).with_name("m1_ceremony_operator.py"))
OPERATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(OPERATOR)


class M1CeremonyOperatorTests(unittest.TestCase):
    def test_create_is_exact(self):
        seen = []
        def transaction(request):
            seen.append(request)
            return {"ok": True, "result": {"request_id": "r1", "payload_hash": OPERATOR.PAYLOAD_HASH,
                    "capability": OPERATOR.CAPABILITY, "risk_class": "red", "status": "pending"}}
        result = OPERATOR.create(transaction)
        self.assertEqual("created", result["phase"])
        self.assertEqual(OPERATOR.PAYLOAD, seen[0]["payload"])
        self.assertEqual(300, seen[0]["ttl_seconds"])

    def test_create_rejects_non_red_result(self):
        with self.assertRaisesRegex(OPERATOR.OperatorError, "exact pending Red"):
            OPERATOR.create(lambda _: {"ok": True, "result": {"request_id": "r1",
                "payload_hash": OPERATOR.PAYLOAD_HASH, "capability": OPERATOR.CAPABILITY,
                "risk_class": "yellow", "status": "pending"}})

    def test_consume_requires_positive_result_then_duplicate_denial(self):
        responses = iter([
            {"ok": True, "result": {"request_id": "r1", "status": "consumed", "synthetic": True}},
            {"ok": False, "error": "request is not approved"},
        ])
        result = OPERATOR.consume("r1", OPERATOR.PAYLOAD_HASH, lambda _: next(responses))
        self.assertTrue(result["duplicate_denied"])

    def test_uncertain_consume_is_never_retried(self):
        calls = []
        def transaction(request):
            calls.append(request)
            return {"ok": False, "error": "transport uncertain"}
        with self.assertRaisesRegex(OPERATOR.OperatorError, "without retry"):
            OPERATOR.consume("r1", OPERATOR.PAYLOAD_HASH, transaction)
        self.assertEqual(1, len(calls))

    def test_wrong_duplicate_result_fails(self):
        responses = iter([
            {"ok": True, "result": {"request_id": "r1", "status": "consumed", "synthetic": True}},
            {"ok": True, "result": {"request_id": "r1", "status": "consumed", "synthetic": True}},
        ])
        with self.assertRaisesRegex(OPERATOR.OperatorError, "duplicate consume"):
            OPERATOR.consume("r1", OPERATOR.PAYLOAD_HASH, lambda _: next(responses))


if __name__ == "__main__":
    unittest.main()
