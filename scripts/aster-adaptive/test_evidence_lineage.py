"""Reject lineage substitutions before retaining measured fixture outcomes."""
import json
import tempfile
import unittest
from pathlib import Path

from evidence_store import Dataset, EvidenceStore, digest
from fixtures import make_run
from test_evidence_store import D, experiment


class LineageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = EvidenceStore(Path(self.temp.name)/'ledger.db')
        self.addCleanup(self.store.close)
        self.dataset = Dataset(dataset_id='fixture-data', cases=(dict(
            case_id='one-read', family_id='time', input_digest=D, expected_digest=D),))
        self.data = self.dataset.model_dump(mode='json')
        self.store.append('dataset', 'dataset', self.data)
        self.spec = experiment() | {'dataset_digest':digest(self.data)}
        self.store.append('spec', 'experiment', self.spec)
        run = make_run(D).model_dump(mode='json')
        run['experiment_id'] = self.spec['experiment_id']
        self.run = dict(dataset_digest=digest(self.data), case_id='one-read',
                        candidate_role='candidate', run=run)

    def test_dataset_identity_and_case_uniqueness(self):
        with self.assertRaises(ValueError):
            self.store.append('other-dataset', 'dataset', self.data)
        with self.assertRaises(ValueError):
            Dataset.model_validate_json(json.dumps(self.data | {'cases':self.data['cases']*2}))

    def test_unknown_case_and_changed_dataset_denied(self):
        for change in ({'case_id':'missing'}, {'dataset_digest':'sha256:'+'2'*64}):
            with self.assertRaises(ValueError):
                self.store.append('run', 'run', self.run | change)

    def test_harness_and_experiment_substitution_denied(self):
        for change in ({'harness_digest':'sha256:'+'2'*64}, {'experiment_id':'other'}):
            with self.assertRaises(ValueError):
                self.store.append('run', 'run', self.run | {'run':self.run['run'] | change})

    def test_replayed_run_identity_denied(self):
        self.store.append('run', 'run', self.run)
        with self.assertRaises(ValueError):
            self.store.append('new-event', 'run', self.run)

    def test_outcome_binding_duplicate_and_restore(self):
        h = self.store.append('run', 'run', self.run)
        outcome = dict(run_id=self.run['run']['run_id'],status='completed',
                       verification='fixture-conformance',tool_calls=1,elapsed_ms=0.1,output_bytes=100)
        linked = dict(experiment_id=self.spec['experiment_id'],run_event_digest=h,outcome=outcome)
        for change in ({'experiment_id':'other'}, {'run_event_digest':D},
                       {'outcome':outcome | {'run_id':'different'}}):
            with self.assertRaises(ValueError):
                self.store.append('out', 'linked-outcome', linked | change)
        head = self.store.append('out', 'linked-outcome', linked)
        with self.assertRaises(ValueError):
            self.store.append('duplicate', 'linked-outcome', linked)
        backup = Path(self.temp.name)/'backup.db'
        self.assertEqual(head,self.store.backup(backup))
        restored = EvidenceStore(backup)
        self.addCleanup(restored.close)
        self.assertEqual(head,restored.verify(expected_head=head))
