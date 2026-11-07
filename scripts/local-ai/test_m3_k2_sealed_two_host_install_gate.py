import copy
import hashlib
import unittest
from unittest import mock

import m3_k2_sealed_two_host_install_gate as gate


def reconciliation():
    return {
        "schema": "aster-m3-k2-development-reconciliation.v1",
        "state": "complete", "booking_id": gate.BOOKING_ID,
        "requests": 192, "retries": 0, "errors": 0,
        "production_restored": True, "development_gate_passed": True,
        "status": "pass", "result_sha256": "a" * 64,
    }


def raw(value):
    import json
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


class K2TwoHostInstallGateTests(unittest.TestCase):
    def invoke(self, value=None):
        bundle = b"bundle"; installer = b"installer"
        with mock.patch.object(gate, "BUNDLE_SHA256",
                               hashlib.sha256(bundle).hexdigest()), \
             mock.patch.object(gate, "INSTALLER_SHA256",
                               hashlib.sha256(installer).hexdigest()):
            return gate.plan(reconciliation_raw=raw(value or reconciliation()),
                             bundle_raw=bundle, installer_raw=installer)

    def test_exact_passing_restored_result_produces_non_authorizing_plan(self):
        value = self.invoke()
        self.assertEqual("ready-for-separate-approval", value["state"])
        self.assertEqual(["macbook", "mac_mini"], value["install_order"])
        self.assertFalse(value["effect_authorized"])
        self.assertFalse(value["service_restart"])

    def test_reject_or_failed_restoration_fails_closed(self):
        for field, changed in (("status", "reject"),
                               ("development_gate_passed", False),
                               ("production_restored", False)):
            value = copy.deepcopy(reconciliation()); value[field] = changed
            with self.assertRaisesRegex(gate.GateError, "PREREQUISITE"):
                self.invoke(value)

    def test_unknown_field_or_duplicate_json_fails_closed(self):
        value = reconciliation(); value["extra"] = True
        with self.assertRaises(gate.GateError): self.invoke(value)
        with self.assertRaisesRegex(gate.GateError, "DUPLICATE"):
            gate.decode(b'{"state":"complete","state":"failed"}')

    def test_bundle_and_installer_identities_are_independent(self):
        value = raw(reconciliation())
        with mock.patch.object(gate, "BUNDLE_SHA256", "0" * 64), \
             mock.patch.object(gate, "INSTALLER_SHA256",
                               hashlib.sha256(b"installer").hexdigest()), \
             self.assertRaisesRegex(gate.GateError, "BUNDLE"):
            gate.plan(reconciliation_raw=value, bundle_raw=b"bundle",
                      installer_raw=b"installer")
        with mock.patch.object(gate, "BUNDLE_SHA256",
                               hashlib.sha256(b"bundle").hexdigest()), \
             mock.patch.object(gate, "INSTALLER_SHA256", "0" * 64), \
             self.assertRaisesRegex(gate.GateError, "INSTALLER"):
            gate.plan(reconciliation_raw=value, bundle_raw=b"bundle",
                      installer_raw=b"installer")


if __name__ == "__main__":
    unittest.main()
