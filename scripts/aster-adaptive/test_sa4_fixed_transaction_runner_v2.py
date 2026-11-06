import hashlib,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import sa4_fixed_transaction_runner_v2 as runner
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry
from test_sa4_single_file_repair_contract_v1 import plan

GRANT_ID="sa4-runner-test-grant"

STATEMENT=b'{"authority":"observer-proof-only-no-effect","observer_id":"aster-observer","observer_key_sha256":"a8b5e876898ddcd7882a51c74d8b8388bb26160c96f87ab23dbeeecab9c0892b","receipt_sha256":"1111111111111111111111111111111111111111111111111111111111111111","schema":"aster-sa4-independent-receipt-proof.v1","signature_algorithm":"rsa-pkcs1v1_5-sha256"}\n'

class Tests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup); root=Path(temp.name)
        self.input=root/"input"; self.evidence=root/"evidence"; self.ledger=root/"ledger"; self.exchange=root/"exchange"
        self.input.mkdir(mode=0o700)
        candidate=b'{"adapter":"sa4-canary","schema":"aster-sa4-canary-adapter.v1","state":"healthy"}\n'
        target=registry.PRODUCTION_TARGETS[0]; value=plan()
        value.update(plan_id="sa4-runner-test-plan",target_id=target.target_id)
        value["target"]={"host_id":target.host_id,"path":target.path,"type":"regular-file","follow_symlinks":False,"owner":"root","group":"root","mode":"0644"}
        value["precondition"]["expected_sha256"]="2"*64
        value["change"]["artifact_sha256"]=hashlib.sha256(candidate).hexdigest()
        plan_raw=contract.canonical(value); plan_sha=hashlib.sha256(plan_raw).hexdigest()
        approval=contract.canonical({"plan_sha256":plan_sha})
        grant=contract.canonical({"grant_id":GRANT_ID,"expires_epoch":2000})
        files={"plan":plan_raw,"approval":approval,"approval_proof":b"proof\n","grant":grant,"grant_proof":b"proof\n","candidate":candidate}
        for name,raw in files.items():
            path=self.input/name; path.write_bytes(raw); path.chmod(0o600)
        self.patches=[patch.object(runner,"INPUT_DIR",self.input),patch.object(runner,"EVIDENCE_DIR",self.evidence),patch.object(runner,"LEDGER_ROOT",self.ledger),patch.object(runner,"EXPECTED_UID",os.geteuid()),patch.object(runner.exchange,"EXCHANGE_DIR",self.exchange)]
        for item in self.patches: item.start(); self.addCleanup(item.stop)
    def test_fixed_success_writes_one_terminal_result(self):
        def run(*args,**kwargs):
            reconciliation=b'{"state":"accepted"}\n'
            for name in runner.SUCCESS_EVIDENCE-{"reconciliation"}:
                kwargs["evidence_writer"](name,b'{}\n')
            kwargs["evidence_writer"]("reconciliation",reconciliation)
            kwargs["observer_signer"](STATEMENT)
            return {"schema":"aster-sa4-one-shot-transaction-result.v1","operation_id":runner.OPERATION_ID,"branch":"postcheck-complete","observer_signatures":1,"automatic_retry":False,"terminal_result_sha256":hashlib.sha256(reconciliation).hexdigest()}
        with patch.object(runner.authority,"verify",return_value={"grant_id":GRANT_ID}),patch.object(runner.controller,"run",side_effect=run),patch.object(runner.exchange,"request_signature",return_value="a"*512),patch.object(runner,"_close_exchange",return_value=[{"sequence":1,"request_sha256":"2"*64,"response_sha256":"3"*64}]):
            value=runner.execute(1000)
        self.assertEqual(GRANT_ID,value["grant_id"]); self.assertTrue(value["runtime_exchange_removed"]); self.assertTrue((self.evidence/"terminal-result.json").exists())
        self.assertEqual(runner.SUCCESS_EVIDENCE,
                         frozenset(path.stem for path in self.evidence.iterdir()
                                   if path.name!="terminal-result.json"))
    def test_bad_input_mode_fails_before_ledger(self):
        (self.input/"candidate").chmod(0o644)
        with self.assertRaises(ValueError): runner.execute(1000)
        self.assertFalse(self.ledger.exists())
    def test_no_arguments(self):
        with self.assertRaises(ValueError): runner.main(["unexpected"])

    def test_signature_count_drift_retains_exchange_and_stops(self):
        with patch.object(runner.authority,"verify",return_value={"grant_id":GRANT_ID}),patch.object(runner.controller,"run",return_value={"observer_signatures":1}):
            with self.assertRaises(ValueError): runner.execute(1000)
        self.assertTrue(self.exchange.exists()); self.assertFalse((self.evidence/"terminal-result.json").exists())

if __name__=="__main__": unittest.main()
