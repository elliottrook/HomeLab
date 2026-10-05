"""Run-003 remains local and approval-gated; no network calls occur here."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import s0_live_candidate as live


class AttemptThreeTests(unittest.TestCase):
    def test_distinct_consumed_identity_and_preserved_evidence(self):
        self.assertIn('attempt-3',live.JOURNAL.name)
        self.assertIn('attempt-3',live.APPROVAL.name)
        self.assertIn('attempt-3',live.MANIFEST.name)
        value=json.loads(live.APPROVAL.read_text())
        self.assertEqual(value['scope']['attempt'],'run-003')
        self.assertEqual(value['release'],{'technical_review':'passed','exclusive_operator_window':'confirmed',
            'one_shot_execution':'consumed-run-003-namespace-failure','human_approval':'approved-for-run-003'})
        self.assertTrue((live.ROOT/live.EXPERIMENT/'run-003/manifest.json').exists())
        with self.assertRaises(PermissionError):live.validate_approval()

    def test_both_prior_readonly_attempts_verify(self):
        live.verify_prior_readonly_abort()
        live.verify_prior_run002()

    def test_run002_evidence_tamper_fails_closed(self):
        source=live.ROOT/live.EXPERIMENT/'run-002'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();target=root/live.EXPERIMENT/'run-002'
            target.parent.mkdir(parents=True);shutil.copytree(source,target)
            record=target/'006.json';record.write_bytes(record.read_bytes()+b' ')
            with patch.object(live,'ROOT',root),self.assertRaises(ValueError):live.verify_prior_run002()

    def test_run003_evidence_and_recovery_are_preserved(self):
        root=live.ROOT/live.EXPERIMENT/'run-003';evidence=json.loads((root/'manifest.json').read_text())
        self.assertEqual(evidence['systemd_failure'],'226/NAMESPACE')
        self.assertTrue(evidence['manual_recovery_completed'])
        self.assertTrue(evidence['service_baseline_restored'])
        self.assertFalse(evidence['further_shared_host_retries_allowed'])


if __name__=='__main__':unittest.main()
