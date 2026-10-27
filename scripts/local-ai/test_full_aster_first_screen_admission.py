import json
import unittest

import full_aster_first_screen_admission as admission


def fixture():
    f2=b'{"f2":1}\n';f3=b'{"f3":1}'
    lease="aster-full-screen-owner-0123456789abcdef:123"
    f4=(json.dumps({"receipt":{"lease_id":lease,"generation":1}},sort_keys=True,separators=(",",":"))+"\n").encode()
    import hashlib
    f5=(json.dumps({"f2_result_sha256":hashlib.sha256(f2).hexdigest(),
        "f3_receipt_sha256":hashlib.sha256(f3).hexdigest(),
        "f4_receipt_sha256":hashlib.sha256(f4).hexdigest()},sort_keys=True,separators=(",",":"))+"\n").encode()
    return dict(cycle_date="2026-10-27",lease_id=lease,created_epoch=1000,
                expires_epoch=1900,f2_bytes=f2,f3_bytes=f3,f4_bytes=f4,f5_bytes=f5)


class AdmissionTests(unittest.TestCase):
    def test_binds_exact_evidence_contract_artifact_baseline_and_workload(self):
        value=admission.build(**fixture())
        self.assertEqual(value["contract_sha256"],admission.CONTRACT_SHA256)
        self.assertEqual(value["artifact"]["sha256"],admission.ARTIFACT_SHA256)
        self.assertEqual(value["workload"],{"name":"qwen36-35b-first-screen","requests":2,
            "timeout_seconds_each":60,"reasoning":"on","speculation":"off","retries":0})
        self.assertFalse(value["live_effect_authorized"])

    def test_foreign_lease_stale_window_and_cross_binding_fail(self):
        for changes in ({"lease_id":"other"},{"expires_epoch":1901},{"f2_bytes":b"changed"}):
            values=fixture();values.update(changes)
            with self.subTest(changes=changes),self.assertRaises(admission.AdmissionError):
                admission.build(**values)


if __name__=="__main__":unittest.main()
