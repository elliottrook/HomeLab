import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import full_inference_lab_runtime as runtime


class FakeProducer:
    def __init__(self, runner, baseline, owner, *, wall_clock):
        self.preflight = SimpleNamespace(name="preflight")

    def collect(self, *, cycle, session_start_epoch):
        return self.preflight


class FakeController:
    def __init__(self, *args, **kwargs):
        pass


class PilotHarness:
    receipt = {"profile": "accepted-9b-direct-control-smoke-v1",
               "request_count": 3, "exit_status": 0}

    def __init__(self, *, begin_error=None, smoke_error=None, restore_error=None):
        self.begin_error = begin_error
        self.smoke_error = smoke_error
        self.restore_error = restore_error
        self.active = False
        self.restore_calls = 0

    def begin(self, preflight):
        if self.begin_error:
            raise self.begin_error
        self.active = True
        return SimpleNamespace(lease_id="lease-1", generation=2)

    def run_smoke_bounded(self, *, heartbeat):
        if self.smoke_error:
            raise self.smoke_error
        return self.receipt

    def heartbeat(self, now):
        return None

    def restore(self, *, now_epoch, owner_present):
        self.restore_calls += 1
        if self.restore_error:
            raise self.restore_error
        self.active = False


class FakeSupervisorFactory:
    def __init__(self, harness):
        self.harness = harness

    def __call__(self, *args, **kwargs):
        return self.harness


class FullInferenceRuntimePilotTests(unittest.TestCase):
    def test_production_mask_uses_the_runtime_symlink_boundary(self):
        def runner(command, timeout):
            if "is-active" in command:
                return 3, "inactive\n"
            if "readlink" in command:
                return 0, "/dev/null\n"
            return 1, ""
        self.assertTrue(runtime._production_masked(runner))

    def args(self):
        return runtime._parser().parse_args([
            "--phase", "pilot", "--state-root", "/tmp/pilot-test-state",
            "--cycle", "2026_10_18", "--session-start-epoch", "100",
            "--owner-id", "owner-1", "--admin-path-evidence", "attested",
            "--owner-unit", "aster-local-ai-pilot-owner-owner-1.scope",
            "--model-sha256", "model", "--binary-sha256", "binary",
            "--unit-sha256", "unit", "--effect-authorized",
        ])

    def run_harness(self, harness):
        with TemporaryDirectory() as tmp:
            args = self.args()
            args.state_root = Path(tmp) / "state"
            with patch.object(runtime, "LocalProxmoxFullDrainSourceProducer", FakeProducer), \
                 patch.object(runtime, "LocalProxmoxFullDrainValidator", lambda *a, **k: object()), \
                 patch.object(runtime, "FullInferenceDrainController", FakeController), \
                 patch.object(runtime, "PersistentFullDrainSupervisor", FakeSupervisorFactory(harness)), \
                 patch.object(runtime, "_gpu_users", lambda: frozenset()):
                return runtime._run_pilot(args, runtime.FullDrainPaths(args.state_root),
                                          runner=lambda *a: (0, ""),
                                          gpu_users=lambda: frozenset(), wall_clock=lambda: 100)

    def test_success_runs_single_bounded_orchestration_and_restore(self):
        harness = PilotHarness()
        self.assertEqual(self.run_harness(harness), 0)
        self.assertEqual(harness.restore_calls, 1)

    def test_slow_preflight_aborts_before_supervisor_begin(self):
        harness = PilotHarness()
        with TemporaryDirectory() as tmp:
            args = self.args()
            args.state_root = Path(tmp) / "state"
            with patch.object(runtime, "LocalProxmoxFullDrainSourceProducer", FakeProducer), \
                 patch.object(runtime, "LocalProxmoxFullDrainValidator", lambda *a, **k: object()), \
                 patch.object(runtime, "FullInferenceDrainController", FakeController), \
                 patch.object(runtime, "PersistentFullDrainSupervisor", FakeSupervisorFactory(harness)):
                with self.assertRaisesRegex(runtime.SupervisorError, "outside the bounded"):
                    runtime._run_pilot(args, runtime.FullDrainPaths(args.state_root),
                                       runner=lambda *a: (0, ""),
                                       gpu_users=lambda: frozenset(),
                                       wall_clock=lambda: 101, sleep=lambda _: None)
            self.assertFalse(harness.active)

    def test_partial_drain_failure_is_propagated_before_workload(self):
        harness = PilotHarness(begin_error=RuntimeError("mask failed"))
        with self.assertRaisesRegex(RuntimeError, "mask failed"):
            self.run_harness(harness)
        self.assertEqual(harness.restore_calls, 0)

    def test_workload_timeout_or_owner_loss_attempts_recovery_and_retains_uncertainty(self):
        harness = PilotHarness(smoke_error=RuntimeError("deadline"),
                               restore_error=RuntimeError("restore uncertain"))
        with self.assertRaisesRegex(RuntimeError, "deadline"):
            self.run_harness(harness)
        self.assertEqual(harness.restore_calls, 1)
        self.assertTrue(harness.active)

    def test_restoration_failure_is_retried_but_not_hidden(self):
        harness = PilotHarness(restore_error=RuntimeError("postcheck failed"))
        with self.assertRaisesRegex(RuntimeError, "postcheck failed"):
            self.run_harness(harness)
        self.assertEqual(harness.restore_calls, 2)

    def test_unknown_preexisting_gpu_holder_is_not_allowlisted(self):
        harness = PilotHarness()
        rogue = runtime.GpuUser(42, 7, "rogue", "/usr/local/bin/other-gpu-client")
        with TemporaryDirectory() as tmp:
            args = self.args()
            args.state_root = Path(tmp) / "state"
            with patch.object(runtime, "LocalProxmoxFullDrainSourceProducer", FakeProducer), \
                 patch.object(runtime, "LocalProxmoxFullDrainValidator", lambda *a, **k: object()), \
                 patch.object(runtime, "FullInferenceDrainController", FakeController), \
                 patch.object(runtime, "PersistentFullDrainSupervisor", FakeSupervisorFactory(harness)):
                with self.assertRaisesRegex(runtime.SupervisorError, "outside the accepted"):
                    runtime._run_pilot(args, runtime.FullDrainPaths(args.state_root),
                                       runner=lambda *a: (0, ""),
                                       gpu_users=lambda: frozenset({rogue}),
                                       wall_clock=lambda: 100)
            self.assertFalse(harness.active)

    def test_same_binary_outside_lxc110_is_not_allowlisted(self):
        harness = PilotHarness()
        rogue = runtime.GpuUser(
            43, 8, "0::/system.slice/rogue.service",
            "/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server")
        with TemporaryDirectory() as tmp:
            args = self.args()
            args.state_root = Path(tmp) / "state"
            with patch.object(runtime, "LocalProxmoxFullDrainSourceProducer", FakeProducer), \
                 patch.object(runtime, "LocalProxmoxFullDrainValidator", lambda *a, **k: object()), \
                 patch.object(runtime, "FullInferenceDrainController", FakeController), \
                 patch.object(runtime, "PersistentFullDrainSupervisor", FakeSupervisorFactory(harness)):
                with self.assertRaisesRegex(runtime.SupervisorError, "outside the accepted"):
                    runtime._run_pilot(args, runtime.FullDrainPaths(args.state_root),
                                       runner=lambda *a: (0, ""),
                                       gpu_users=lambda: frozenset({rogue}),
                                       wall_clock=lambda: 100)

    def test_same_binary_in_lxc110_but_different_unit_is_not_allowlisted(self):
        harness = PilotHarness()
        rogue = runtime.GpuUser(
            44, 9, "0::/lxc/110/ns/system.slice/other.service",
            "/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server")
        with TemporaryDirectory() as tmp:
            args = self.args()
            args.state_root = Path(tmp) / "state"
            with patch.object(runtime, "LocalProxmoxFullDrainSourceProducer", FakeProducer), \
                 patch.object(runtime, "LocalProxmoxFullDrainValidator", lambda *a, **k: object()), \
                 patch.object(runtime, "FullInferenceDrainController", FakeController), \
                 patch.object(runtime, "PersistentFullDrainSupervisor", FakeSupervisorFactory(harness)):
                with self.assertRaisesRegex(runtime.SupervisorError, "outside the accepted"):
                    runtime._run_pilot(args, runtime.FullDrainPaths(args.state_root),
                                       runner=lambda *a: (0, ""),
                                       gpu_users=lambda: frozenset({rogue}),
                                       wall_clock=lambda: 100)

    def test_one_shot_rescue_uses_exact_durable_identity_and_never_workload(self):
        with TemporaryDirectory() as tmp:
            args = self.args()
            args.state_root = Path(tmp) / "state"
            args.lease_id = "lease-1"
            args.generation = 2
            args.phase = "rescue"
            args.state_root.mkdir()
            args.state_root.joinpath("full-inference-drain.json").write_text(
                json.dumps({"owner_id": "owner-1"}) + "\n", encoding="utf-8")
            calls = []
            with patch.object(runtime, "LocalProxmoxFullDrainValidator", lambda *a, **k: object()), \
                 patch.object(runtime, "FullInferenceDrainController", FakeController), \
                 patch.object(runtime, "recovery_only", lambda *a, **k: calls.append(k)):
                self.assertEqual(runtime._run_rescue(
                    args, runtime.FullDrainPaths(args.state_root), runner=lambda *a: (0, "")), 0)
            self.assertEqual(calls[0]["lease_id"], "lease-1")
            self.assertEqual(calls[0]["generation"], 2)
            self.assertIn("cleanup_runner", calls[0])

    def test_one_shot_rescue_rejects_owner_identity_drift(self):
        with TemporaryDirectory() as tmp:
            args = self.args()
            args.state_root = Path(tmp) / "state"
            args.lease_id = "lease-1"
            args.generation = 2
            args.state_root.mkdir()
            args.state_root.joinpath("full-inference-drain.json").write_text(
                json.dumps({"owner_id": "different-owner"}) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(runtime.SupervisorError, "does not match"):
                runtime._run_rescue(args, runtime.FullDrainPaths(args.state_root),
                                     runner=lambda *a: (0, ""))

    def test_sa3_profile_uses_2700_second_preflight_and_fixed_listener(self):
        events=[]
        class Producer:
            def __init__(self,*a,**k): pass
            def collect(self,*,cycle,session_start_epoch,lab_seconds):
                events.append(("collect",lab_seconds))
                return SimpleNamespace(lab_end_epoch=2800)
        class Controller:
            def __init__(self,*a,**k): pass
            def begin(self,value,*,lab_seconds):
                events.append(("begin",lab_seconds)); return SimpleNamespace(lease_id="lease-1",generation=2)
            def heartbeat(self,now): events.append("heartbeat")
            def restore(self,plan,*,now_epoch,owner_present): events.append("restore")
        def execute(**kwargs):
            plan=kwargs["controller"].begin(SimpleNamespace(),lab_seconds=2700)
            kwargs["heartbeat"](); value=kwargs["workload_runner"](
                heartbeat=kwargs["heartbeat"],deadline_epoch=2800)
            kwargs["cleanup"](); kwargs["controller"].restore(
                plan,now_epoch=100,owner_present=True)
            return {"effects":"sa3-expanded-quality-complete","receipt":value}
        def listener(**kwargs):
            events.append(("listener",kwargs["lease_id"],kwargs["generation"],kwargs["deadline_epoch"]))
            return {"exit_status":0,"profile":"sa3-expanded-source-quality-v1","request_count":20}
        with TemporaryDirectory() as tmp:
            args=self.args();args.state_root=Path(tmp)/"state";args.retain_root=tmp
            args.workload_profile="sa3-expanded-source-quality-v1"
            with patch.object(runtime,"LocalProxmoxFullDrainSourceProducer",Producer), \
                 patch.object(runtime,"LocalProxmoxFullDrainValidator",lambda *a,**k:object()), \
                 patch.object(runtime,"FullInferenceDrainController",Controller), \
                 patch.object(runtime,"lab_is_absent",lambda *a,**k:True), \
                 patch("sa3_expanded_quality_transaction.execute",execute), \
                 patch("sa3_listener_adapter.run",listener):
                self.assertEqual(runtime._run_sa3(args,runtime.FullDrainPaths(args.state_root),
                    runner=lambda *a:(0,""),gpu_users=lambda:frozenset(),wall_clock=lambda:100),0)
        self.assertIn(("collect",2700),events)
        self.assertIn(("begin",2700),events)
        self.assertIn(("listener","lease-1",2,2800),events)
        self.assertIn("restore",events)

    def test_candidate_g_profile_uses_fixed_envelope_transaction_and_listener(self):
        events=[]
        class Producer:
            def __init__(self,*a,**k): pass
            def collect(self,*,cycle,session_start_epoch,lab_seconds):
                events.append(("collect",lab_seconds))
                return SimpleNamespace(lab_end_epoch=2800)
        class Controller:
            def __init__(self,*a,**k): pass
            def begin(self,value,*,lab_seconds):
                events.append(("begin",lab_seconds))
                return SimpleNamespace(lease_id="lease-g",generation=3)
            def heartbeat(self,now): events.append("heartbeat")
            def restore(self,plan,*,now_epoch,owner_present): events.append("restore")
        def execute(**kwargs):
            plan=kwargs["controller"].begin(SimpleNamespace(),lab_seconds=2700)
            value=kwargs["workload_runner"](
                heartbeat=kwargs["heartbeat"],deadline_epoch=2800)
            kwargs["cleanup"](); kwargs["controller"].restore(
                plan,now_epoch=100,owner_present=True)
            return {"effects":"sa3-evidence-envelope-quality-complete",
                    "production_restored":True,"receipt":value}
        def listener(**kwargs):
            events.append(("listener",kwargs["lease_id"],kwargs["generation"],
                           kwargs["deadline_epoch"]))
            return {"exit_status":0,"profile":"sa3-evidence-envelope-quality-v1",
                    "request_count":20,"model_request_count":14,"case_count":20,
                    "prediction_sha256":"a"*64,"error_count":0}
        with TemporaryDirectory() as tmp:
            args=self.args();args.state_root=Path(tmp)/"state";args.retain_root=tmp
            args.workload_profile="sa3-evidence-envelope-quality-v1"
            with patch.object(runtime,"LocalProxmoxFullDrainSourceProducer",Producer), \
                 patch.object(runtime,"LocalProxmoxFullDrainValidator",lambda *a,**k:object()), \
                 patch.object(runtime,"FullInferenceDrainController",Controller), \
                 patch.object(runtime,"lab_is_absent",lambda *a,**k:True), \
                 patch("sa3_evidence_envelope_transaction.execute",execute), \
                 patch("sa3_evidence_envelope_listener_adapter.run",listener):
                self.assertEqual(runtime._run_sa3(args,runtime.FullDrainPaths(args.state_root),
                    runner=lambda *a:(0,""),gpu_users=lambda:frozenset(),wall_clock=lambda:100),0)
        self.assertIn(("collect",2700),events)
        self.assertIn(("listener","lease-g",3,2800),events)
        self.assertIn("restore",events)

    def test_m3_profile_uses_bounded_2700_second_preflight_and_fixed_transaction(self):
        events=[]
        class Producer:
            def __init__(self,*a,**k): pass
            def collect(self,*,cycle,session_start_epoch,lab_seconds):
                events.append(("collect",lab_seconds))
                return SimpleNamespace(lab_end_epoch=3700)
        class Controller:
            def __init__(self,*a,**k): pass
            def heartbeat(self,now): events.append("heartbeat")
        def execute(**kwargs):
            events.append(("execute",kwargs["owner_id"],kwargs["cycle"],
                           str(kwargs["retain_root"])))
            kwargs["heartbeat"]()
            return {"effects":"m3-joint-semantic-public-complete",
                    "production_restored":True,"receipt":{"exit_status":0,
                    "profile":"m3-joint-semantic-35b-public-v1",
                    "request_count":24,"result_sha256":"a"*64,
                    "exact":23,"public_pass":True}}
        with TemporaryDirectory() as tmp:
            args=self.args();args.state_root=Path(tmp)/"state";args.retain_root=tmp
            args.workload_profile="m3-joint-semantic-35b-public-v1"
            with patch.object(runtime,"LocalProxmoxFullDrainSourceProducer",Producer), \
                 patch.object(runtime,"LocalProxmoxFullDrainValidator",lambda *a,**k:object()), \
                 patch.object(runtime,"FullInferenceDrainController",Controller), \
                 patch("m3_joint_semantic_35b_transaction.execute",execute):
                self.assertEqual(runtime._run_m3(args,runtime.FullDrainPaths(args.state_root),
                    runner=lambda *a:(0,""),gpu_users=lambda:frozenset(),wall_clock=lambda:100),0)
        self.assertIn(("collect",2700),events)
        self.assertTrue(any(event[0]=="execute" for event in events if isinstance(event,tuple)))
        self.assertIn("heartbeat",events)

    def test_rescue_accepts_only_the_restored_production_gpu_holder(self):
        with TemporaryDirectory() as tmp:
            args=self.args(); args.state_root=Path(tmp)/"state"
            args.lease_id="lease-1"; args.generation=2; args.phase="rescue"
            args.state_root.mkdir(); args.state_root.joinpath("full-inference-drain.json").write_text(
                json.dumps({"owner_id":"owner-1"})+"\n",encoding="utf-8")
            accepted=runtime.GpuUser(44,9,"0::/lxc/110/ns/system.slice/aster-llama.service",
                "/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server")
            captured=[]
            def probes(command,timeout):
                if "pgrep" in command: return 1,""
                if "is-active" in command: return 3,"inactive"
                return 0,""
            with patch.object(runtime,"LocalProxmoxFullDrainValidator",lambda *a,**k:object()), \
                 patch.object(runtime,"FullInferenceDrainController",FakeController), \
                 patch.object(runtime,"recovery_only",lambda *a,**k:captured.append(k)):
                self.assertEqual(runtime._run_rescue(args,runtime.FullDrainPaths(args.state_root),
                    runner=probes,gpu_users=lambda:frozenset({accepted})),0)
            self.assertTrue(captured[0]["lab_absent"]())


if __name__ == "__main__":
    unittest.main()
