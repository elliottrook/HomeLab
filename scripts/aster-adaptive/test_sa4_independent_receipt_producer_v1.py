from dataclasses import replace
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sa4_independent_receipt_producer_v1 as producer
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry
from test_sa4_single_file_repair_contract_v1 import plan


class SA4IndependentReceiptProducerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(); root = Path(self.temporary.name)
        self.raw = (Path(__file__).with_name("fixtures") /
                    "sa4-canary-adapter-healthy-v1.json").read_bytes()
        self.path = root / "canary.json"; self.path.write_bytes(self.raw); os.chmod(self.path, 0o644)
        base = registry.PRODUCTION_TARGETS[0]
        self.target = replace(base, host_id="observer-test-host", path=str(self.path),
                              checkpoint_parent=str(root / "checkpoints"),
                              temporary_path=str(root / ".canary.tmp"))
        value = plan(); value["target_id"] = self.target.target_id
        value["target"] = {"host_id": self.target.host_id, "path": self.target.path,
                           "type": "regular-file", "follow_symlinks": False,
                           "owner": "root", "group": "root", "mode": "0644"}
        value["precondition"]["expected_sha256"] = "19b4e02d7f4edd9b38d9a0c3e9e3b49c4209473694fab39db0494c5fe523df1a"
        value["change"]["artifact_sha256"] = hashlib.sha256(self.raw).hexdigest()
        self.plan_raw = contract.canonical(value); plan_sha = producer.sha256(self.plan_raw)
        self.admission_raw = contract.canonical({"schema":"aster-sa4-effect-admission.v1",
            "plan_sha256":plan_sha,"effect_authorized":True,"maximum_effects":1,
            "automatic_retry":False})
        self.claim_raw = contract.canonical({"state":"claimed","use_count":1,
            "plan_sha256":plan_sha,"claimant":"sa4-test-operation",
            "claimed_epoch":100,"claim_deadline_epoch":150})
        self.terminal_raw = contract.canonical({
            "schema":"aster-sa4-operation-terminal.v1","operation_id":"sa4-test-operation",
            "plan_sha256":plan_sha,"admission_sha256":producer.sha256(self.admission_raw),
            "claim_sha256":producer.sha256(self.claim_raw),"target_id":self.target.target_id,
            "target_registration_sha256":registry.registration_sha256(self.target),
            "state":"effect-attempted-awaiting-observer","effect_count":1,"retry_count":0})

    def tearDown(self): self.temporary.cleanup()

    def observe(self):
        original_metadata = producer.metadata_check.check
        def metadata(value):
            adjusted = dict(value, uid=0, gid=0)
            return original_metadata(adjusted)
        with patch.object(registry,"PRODUCTION_TARGETS",(self.target,)), \
             patch.object(producer,"LOCAL_HOST_ID",self.target.host_id), \
             patch.object(producer,"EXPECTED_UID",os.geteuid()), \
             patch.object(producer,"EXPECTED_GID",os.getegid()), \
             patch.object(producer.metadata_check,"check",side_effect=metadata):
            return contract.decode_unique_json(producer.observe(
                self.plan_raw,self.admission_raw,self.claim_raw,self.terminal_raw,
                observed_epoch=120))

    def test_healthy_target_produces_three_content_free_passes(self):
        receipt = self.observe()
        self.assertEqual(["pass","pass","pass"], [r["state"] for r in receipt["checks"]])
        self.assertEqual(0,receipt["maximum_effects"])
        self.assertTrue(receipt["temporary_absent"])

    def test_changed_target_produces_fail_rows_without_effect(self):
        self.path.write_bytes(b'{"changed":true}\n')
        receipt = self.observe()
        self.assertIn("fail",[r["state"] for r in receipt["checks"]])
        self.assertEqual(0,receipt["maximum_effects"])

    def test_committed_source_is_inactive(self):
        self.assertEqual("unconfigured",producer.LOCAL_HOST_ID)
        with patch.object(registry,"PRODUCTION_TARGETS",(self.target,)):
            with self.assertRaises(ValueError): producer.observe(
                self.plan_raw,self.admission_raw,self.claim_raw,self.terminal_raw,
                observed_epoch=120)


if __name__ == "__main__": unittest.main()
