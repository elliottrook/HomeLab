import hashlib
import json
import unittest

import nlu_k2_shadow_reconciliation_v1 as reconciliation
from test_nlu_k2_no_effect_shadow_v1 import fixture


def raw(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def evidence():
    envelope_raw = raw(fixture())
    terminal = {"schema":"aster-nlu-k2-shadow-terminal.v1",
        "state":"complete", "booking_id":"aster-stream-a-m5-k2-20261107-1200-r1",
        "workload_id":reconciliation.WORKLOAD_ID, "requests":60,
        "retries":0, "errors":0, "production_restored":True,
        "result_sha256":hashlib.sha256(envelope_raw).hexdigest(),
        "route_execution_attempted":False, "provider_egress_attempted":False,
        "external_cost_microunits":0}
    return envelope_raw, terminal


class K2ShadowReconciliationTests(unittest.TestCase):
    def test_exact_terminal_binds_passing_no_effect_score(self):
        envelope, terminal = evidence()
        value = reconciliation.reconcile(envelope, raw(terminal))
        self.assertTrue(value["shadow_gate_passed"])
        self.assertTrue(value["production_restored"])
        self.assertFalse(value["route_execution_attempted"])

    def test_unrestored_or_incomplete_terminal_fails_closed(self):
        for field, changed in (("production_restored",False),("state","failed")):
            envelope, terminal = evidence(); terminal[field]=changed
            with self.assertRaisesRegex(ValueError,"terminal"):
                reconciliation.reconcile(envelope,raw(terminal))

    def test_count_retry_or_error_drift_fails_closed(self):
        for field, changed in (("requests",59),("retries",1),("errors",1)):
            envelope, terminal = evidence(); terminal[field]=changed
            with self.assertRaisesRegex(ValueError,"terminal"):
                reconciliation.reconcile(envelope,raw(terminal))

    def test_boolean_values_cannot_masquerade_as_integer_zero(self):
        for field in ("retries", "errors", "external_cost_microunits"):
            envelope, terminal = evidence(); terminal[field] = False
            with self.assertRaisesRegex(ValueError, "terminal"):
                reconciliation.reconcile(envelope, raw(terminal))

    def test_result_digest_and_booking_identity_are_exact(self):
        envelope, terminal = evidence(); terminal["result_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"terminal"):
            reconciliation.reconcile(envelope,raw(terminal))
        envelope, terminal = evidence(); terminal["booking_id"]="wrong"
        with self.assertRaisesRegex(ValueError,"terminal"):
            reconciliation.reconcile(envelope,raw(terminal))

    def test_any_effect_or_unknown_field_fails_closed(self):
        for field, changed in (("route_execution_attempted",True),
                              ("provider_egress_attempted",True),
                              ("external_cost_microunits",1)):
            envelope, terminal = evidence(); terminal[field]=changed
            with self.assertRaisesRegex(ValueError,"terminal"):
                reconciliation.reconcile(envelope,raw(terminal))
        envelope, terminal = evidence(); terminal["extra"]=True
        with self.assertRaisesRegex(ValueError,"terminal"):
            reconciliation.reconcile(envelope,raw(terminal))


if __name__ == "__main__": unittest.main()
