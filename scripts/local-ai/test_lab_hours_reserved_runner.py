import json
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch
from zoneinfo import ZoneInfo
import lab_hours_reserved_runner as runner

class ReservedRunnerTests(unittest.TestCase):
    def test_bounded_m3_failure_becomes_terminal_code(self):
        raw=json.dumps({
            "schema":"aster-m3-joint-semantic-35b-transaction-failure.v1",
            "state":"failed","failure_code":"M3_GUEST_WORKLOAD_FAILED",
            "production_restored":True,
            "guest_failure_code":"M3_PUBLIC_RESULT_INCOMPLETE",
            "attempted":1,"valid":0,
            "first_record_failure":"http_4xx"})
        self.assertEqual("M3_GUEST_WORKLOAD_FAILED_HTTP_4XX_ATTEMPTED_1_VALID_0",
                         runner.bounded_owner_failure(raw))

    def test_unbounded_m3_failure_is_not_promoted(self):
        self.assertIsNone(runner.bounded_owner_failure('{"failure_code":"secret"}'))

    def test_bounded_m3_quality_failure_becomes_terminal_code(self):
        raw=json.dumps({
            "schema":"aster-m3-joint-semantic-35b-transaction-failure.v1",
            "state":"failed","failure_code":"M3_PUBLIC_QUALITY_GATE_FAILED",
            "production_restored":True,"exact":21,"unsafe_false_routes":0,
            "routed_privacy_underclassifications":0,
            "result_sha256":"a"*64,"result_bytes":12345})
        self.assertEqual("M3_PUBLIC_QUALITY_GATE_FAILED_EXACT_21_UNSAFE_0_PRIVACY_0",
                         runner.bounded_owner_failure(raw))

    def test_m3_runner_kind_is_admitted(self):
        spec = runner.workload("m3-joint-semantic-35b-public-v1")
        self.assertIn(spec.runner_kind, runner.REGISTERED_RUNNER_KINDS)

    def test_candidate_g_runner_kind_is_admitted(self):
        spec = runner.workload("sa3-evidence-envelope-quality-v1")
        self.assertIn(spec.runner_kind, runner.REGISTERED_RUNNER_KINDS)

    def test_commands_bind_exact_booking_identity_and_deadline(self):
        booking={"booking_id":"test-booking-01","end_epoch":4600,
                 "workload":"accepted-9b-direct-control-smoke-v1"}
        guardian_unit,owner_unit,guardian,owner=runner.commands(booking,"lh-12345678",1000)
        self.assertIn("lh-12345678",guardian_unit)
        self.assertIn("lh-12345678",owner_unit)
        self.assertEqual(guardian[guardian.index("--rescue-at")+1],"2800")
        self.assertEqual(guardian[guardian.index("--hard-deadline")+1],"5500")
        self.assertEqual(owner[owner.index("--admin-path-evidence")+1],"reserved:test-booking-01")
        self.assertIn("--effect-authorized",owner)

    def test_owner_loss_exercise_has_early_bounded_rescue(self):
        booking={"booking_id":"loss-booking-01","end_epoch":4600,
                 "workload":"accepted-9b-owner-loss-exercise-v1"}
        _,_,guardian,_=runner.commands(booking,"lh-12345678",1000)
        self.assertEqual(guardian[guardian.index("--rescue-at")+1],"1120")

    def test_sa3_guardian_deadline_uses_registered_2700_second_budget(self):
        booking={"booking_id":"sa3-booking-01","end_epoch":4600,
                 "workload":"sa3-expanded-source-quality-v1"}
        _,_,guardian,_=runner.commands(booking,"lh-12345678",1000)
        self.assertEqual(guardian[guardian.index("--rescue-at")+1],"3700")
        self.assertEqual(guardian[guardian.index("--hard-deadline")+1],"5500")

    def test_m3_uses_mount_aware_guardian_and_exact_profile(self):
        booking={"booking_id":"m3-booking-01","end_epoch":5500,
                 "workload":"m3-joint-semantic-35b-public-v1"}
        _,_,guardian,owner=runner.commands(booking,"lh-12345678",1000)
        self.assertTrue(any(str(item).endswith("m3_joint_semantic_35b_guardian.py")
                            for item in guardian))
        self.assertFalse(any(str(item).endswith("full_inference_lab_deadline_guardian.py")
                             for item in guardian))
        self.assertEqual(guardian[guardian.index("--rescue-at")+1],"3700")
        self.assertEqual(owner[owner.index("--workload-profile")+1],
                         "m3-joint-semantic-35b-public-v1")

    def test_guardian_is_settled_only_after_durable_state_is_absent(self):
        calls=[]
        original=runner.STATE_ROOT
        from tempfile import TemporaryDirectory
        from pathlib import Path
        try:
            with TemporaryDirectory() as tmp:
                runner.STATE_ROOT=Path(tmp)
                old_call=runner.call
                runner.call=lambda command, timeout=30: calls.append(tuple(command))
                try:
                    runner.settle_guardian("guardian.service")
                    self.assertEqual(calls,[("systemctl","stop","guardian.service"),
                                            ("systemctl","reset-failed","guardian.service")])
                    calls.clear()
                    (runner.STATE_ROOT/"full-inference-drain.json").write_text("{}")
                    runner.settle_guardian("guardian.service")
                    self.assertEqual(calls,[])
                finally:
                    runner.call=old_call
        finally:
            runner.STATE_ROOT=original

    def test_registered_m3_booking_reaches_complete_terminal_path(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path

        class Store:
            finished=[]
            def __init__(self, _root): pass
            def claim(self, booking_id, *, claimant):
                return {"booking_id":booking_id,"end_epoch":5000,
                        "workload":"m3-joint-semantic-35b-public-v1"}
            def finish(self, booking_id, *, claimant, success, result_code):
                self.finished.append((booking_id,claimant,success,result_code))

        receipt={"effects":"m3-joint-semantic-public-complete",
                 "production_restored":True,
                 "receipt":{"exit_status":0,
                            "profile":"m3-joint-semantic-35b-public-v1",
                            "request_count":24,"result_sha256":"a"*64,
                            "exact":23,"public_pass":True}}
        def call(command, timeout=30):
            output=json.dumps(receipt) if any(
                str(item).endswith("full_inference_lab_runtime.py") for item in command) else ""
            return SimpleNamespace(returncode=0,stdout=output,stderr="")

        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            with patch.object(runner,"ReservationStore",Store), \
                 patch.object(runner,"ATTEMPTS",root/"attempts"), \
                 patch.object(runner,"STATE_ROOT",root/"state"), \
                 patch.object(runner,"load_manifest",lambda:{"pin":"a"*64}), \
                 patch.object(runner,"require_quiet",lambda:None), \
                 patch.object(runner,"postcheck",lambda _unit:None), \
                 patch.object(runner,"settle_guardian",lambda _unit:None), \
                 patch.object(runner,"call",call), \
                 patch.object(runner.os,"geteuid",lambda:0), \
                 patch.object(runner.time,"time",lambda:1000):
                self.assertEqual(0,runner.run("m3-joined-path-test"))
            terminal=json.loads((root/"attempts"/"reservation-m3-joined-path-test"/
                                 "terminal.json").read_text())
            self.assertEqual("complete",terminal["state"])
            self.assertEqual(24,terminal["request_count"])
            self.assertEqual(("m3-joined-path-test",
                              "lh-"+runner.hashlib.sha256(b"m3-joined-path-test").hexdigest()[:20],
                              True,"COMPLETE"),Store.finished[-1])

    def test_registered_candidate_g_booking_reaches_complete_terminal_path(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path

        class Store:
            finished=[]
            def __init__(self, _root): pass
            def claim(self, booking_id, *, claimant):
                return {"booking_id":booking_id,"end_epoch":5000,
                        "workload":"sa3-evidence-envelope-quality-v1"}
            def finish(self, booking_id, *, claimant, success, result_code):
                self.finished.append((booking_id,claimant,success,result_code))

        receipt={"effects":"sa3-evidence-envelope-quality-complete",
                 "production_restored":True,
                 "receipt":{"exit_status":0,
                            "profile":"sa3-evidence-envelope-quality-v1",
                            "request_count":20,"model_request_count":14,
                            "case_count":20,"prediction_sha256":"a"*64,
                            "error_count":0}}
        def call(command, timeout=30):
            output=json.dumps(receipt) if any(
                str(item).endswith("full_inference_lab_runtime.py") for item in command) else ""
            return SimpleNamespace(returncode=0,stdout=output,stderr="")

        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            with patch.object(runner,"ReservationStore",Store), \
                 patch.object(runner,"ATTEMPTS",root/"attempts"), \
                 patch.object(runner,"STATE_ROOT",root/"state"), \
                 patch.object(runner,"load_manifest",lambda:{"pin":"a"*64}), \
                 patch.object(runner,"require_quiet",lambda:None), \
                 patch.object(runner,"postcheck",lambda _unit:None), \
                 patch.object(runner,"settle_guardian",lambda _unit:None), \
                 patch.object(runner,"call",call), \
                 patch.object(runner.os,"geteuid",lambda:0), \
                 patch.object(runner.time,"time",lambda:1000):
                self.assertEqual(0,runner.run("candidate-g-joined-path-test"))
            terminal=json.loads((root/"attempts"/
                "reservation-candidate-g-joined-path-test"/"terminal.json").read_text())
            self.assertEqual("complete",terminal["state"])
            self.assertEqual(20,terminal["request_count"])

if __name__=="__main__": unittest.main()
