from dataclasses import replace
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sa4_atomic_rollback_owner_v1 as rollback
import sa4_authenticated_authority_v1 as rsa
import sa4_independent_postcheck_receipt_v1 as observer
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry
from test_sa4_independent_postcheck_receipt_v1 import KEY, proof_for
from test_sa4_single_file_repair_contract_v1 import plan


class SA4AtomicRollbackOwnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(); root=Path(self.temporary.name)
        self.before=b"drifted\n"; self.after=b"healthy\n"
        self.path=root/"canary"; self.path.write_bytes(self.after); os.chmod(self.path,0o644)
        parent=root/"checkpoints"; parent.mkdir(mode=0o700)
        self.checkpoint_path=parent/"sa4-synthetic-single-file-v1.original"
        self.checkpoint_path.write_bytes(self.before); os.chmod(self.checkpoint_path,0o600)
        base=registry.SCHEMA_FIXTURES[0]
        self.target=replace(base,host_id="rollback-test-host",path=str(self.path),
            checkpoint_parent=str(parent),temporary_path=str(root/".canary.tmp"))
        value=plan(); value["target"]={"host_id":self.target.host_id,"path":self.target.path,
            "type":"regular-file","follow_symlinks":False,"owner":"root","group":"root","mode":"0644"}
        value["precondition"]["expected_sha256"]=hashlib.sha256(self.before).hexdigest()
        value["change"]["artifact_sha256"]=hashlib.sha256(self.after).hexdigest()
        self.plan_raw=contract.canonical(value); registration=registry.registration_sha256(self.target)
        self.checkpoint_raw=contract.canonical({"schema":"aster-sa4-inactive-checkpoint-owner.v1",
            "plan_sha256":rollback.sha256(self.plan_raw),"target_id":self.target.target_id,
            "checkpoint_path":str(self.checkpoint_path),"checkpoint_sha256":hashlib.sha256(self.before).hexdigest(),
            "checkpoint_created":True})
        self.terminal_raw=contract.canonical({"schema":"aster-sa4-operation-terminal.v1",
            "operation_id":"sa4-test-operation","state":"effect-attempted-awaiting-observer",
            "effect_count":1,"retry_count":0})
        check_set=[{"check_id":i,"registered_program_sha256":p}
                   for i,p in zip(self.target.postcheck_ids,self.target.postcheck_program_sha256)]
        snapshot={"device":7,"inode":8,"uid":0,"gid":0,"mode":"0644","link_count":1,
            "size":len(self.after),"regular_file":True,"symlink":False,
            "bytes_sha256":hashlib.sha256(self.after).hexdigest(),"metadata_sha256":"a"*64}
        receipt={"schema":"aster-sa4-independent-postcheck-receipt.v1",
            "operation_id":"sa4-test-operation","plan_sha256":rollback.sha256(self.plan_raw),
            "admission_sha256":"1"*64,"claim_sha256":"2"*64,
            "effect_terminal_sha256":rollback.sha256(self.terminal_raw),
            "target_id":self.target.target_id,"target_registration_sha256":registration,
            "observed_epoch":120,"observer_id":"sa4-observer",
            "check_set_sha256":rollback.sha256(contract.canonical(check_set)),
            "checks":[{"check_id":row["check_id"],"registered_program_sha256":row["registered_program_sha256"],
                       "state":"fail" if n==0 else "pass","measurement_sha256":str(n+3)*64}
                      for n,row in enumerate(check_set)],"target_snapshot":snapshot,
            "temporary_absent":True,"lock_owner":"sa4-test-operation","maximum_effects":0,
            "authority":"independent-observer","automatic_retry":False}
        self.receipt_raw=contract.canonical(receipt); self.proof_raw=proof_for(self.receipt_raw)
        self.trusted={rsa.key_sha256(KEY):{"observer_id":"sa4-observer","key":KEY}}

    def tearDown(self): self.temporary.cleanup()

    def context(self):
        return patch.multiple(rollback,LOCAL_HOST_ID=self.target.host_id,
                              EXPECTED_UID=os.geteuid(),EXPECTED_GID=os.getegid())

    def restore(self):
        with patch.object(registry,"PRODUCTION_TARGETS",(self.target,)),self.context(), \
             patch.object(observer,"TRUSTED_OBSERVERS",self.trusted):
            return rollback.restore(self.plan_raw,self.checkpoint_raw,self.terminal_raw,
                self.receipt_raw,self.proof_raw,rollback_attempt_id="sa4-test-rollback",
                not_before_epoch=100,deadline_epoch=150,rollback_epoch=130)

    def test_signed_failed_postcheck_restores_once_and_retains_checkpoint(self):
        result=self.restore()
        self.assertEqual(self.before,self.path.read_bytes())
        self.assertEqual(self.before,self.checkpoint_path.read_bytes())
        self.assertEqual(1,result["rollback_effect_count"]); self.assertEqual(0,result["retry_count"])
        self.assertTrue(result["temporary_absent"]); self.assertTrue(result["checkpoint_retained"])

    def test_committed_source_is_inactive(self):
        self.assertEqual("unconfigured",rollback.LOCAL_HOST_ID)
        with patch.object(registry,"PRODUCTION_TARGETS",(self.target,)), \
             patch.object(observer,"TRUSTED_OBSERVERS",self.trusted),self.assertRaises(ValueError):
            rollback.restore(self.plan_raw,self.checkpoint_raw,self.terminal_raw,
                self.receipt_raw,self.proof_raw,rollback_attempt_id="sa4-test-rollback",
                not_before_epoch=100,deadline_epoch=150,rollback_epoch=130)

    def test_passing_receipt_or_changed_checkpoint_cannot_rollback(self):
        changed=self.receipt_raw.replace(b'"state":"fail"',b'"state":"pass"',1)
        with patch.object(registry,"PRODUCTION_TARGETS",(self.target,)),self.context(), \
             patch.object(observer,"TRUSTED_OBSERVERS",self.trusted),self.assertRaises(ValueError):
            rollback.restore(self.plan_raw,self.checkpoint_raw,self.terminal_raw,
                changed,proof_for(changed),rollback_attempt_id="sa4-test-rollback",
                not_before_epoch=100,deadline_epoch=150,rollback_epoch=130)
        self.checkpoint_path.write_bytes(b"changed")
        with self.assertRaises(ValueError): self.restore()
        self.assertEqual(self.after,self.path.read_bytes())


if __name__=="__main__": unittest.main()
