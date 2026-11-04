import hashlib, json, subprocess, sys, tempfile, unittest
from pathlib import Path
import sa3_candidate_g_response_normalization_inactive_install as install

class ResponseNormalizationInstallTests(unittest.TestCase):
    def test_exact_scope_and_platform_source_pins(self):
        self.assertEqual(2,len(install.HOST_FILES)); self.assertEqual(2,len(install.GUEST_FILES))
        root=Path(__file__).parent
        for name,(_,expected,_) in install.HOST_FILES.items():
            self.assertEqual(expected,hashlib.sha256((root/name).read_bytes()).hexdigest())
        wrapper=hashlib.sha256((root/"aster_llama_sa3_evidence_envelope_wrapper.py").read_bytes()).hexdigest()
        self.assertEqual(install.GUEST_FILES["aster_llama_sa3_evidence_envelope_wrapper.py"][1],wrapper)
        runner=subprocess.check_output(("git","show",
            "56d4d2272cad0cdbd0e5b3fbbc71f35690a4fbbb:services/aster-agent/evals/sa3_evidence_envelope_runner_v1.py"),
            cwd=root.parents[1])
        self.assertEqual(install.GUEST_FILES["sa3_evidence_envelope_runner_v1.py"][1],
                         hashlib.sha256(runner).hexdigest())
    def test_cli_is_inert_without_apply(self):
        with tempfile.TemporaryDirectory() as temporary:
            result=subprocess.run((sys.executable,"-B",install.__file__,"--stage",temporary),capture_output=True,text=True,check=False)
        self.assertEqual(2,result.returncode); self.assertEqual("source-only",json.loads(result.stdout)["state"])
    def test_checkpoint_is_unique(self):
        self.assertIn("response-normalization-r1-20261104",str(install.CHECKPOINT))

    def test_remote_update_protocol_is_fail_closed(self):
        self.assertIn('BASELINE_DRIFT:', install.REMOTE)
        self.assertIn('ROLLBACK_UNCERTAIN:', install.REMOTE)
        self.assertIn('CHECKPOINT_DRIFT:', install.REMOTE)
        self.assertNotIn('p.unlink()', install.REMOTE)

if __name__=="__main__": unittest.main()
