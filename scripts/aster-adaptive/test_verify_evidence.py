import copy
import json
import tempfile
import unittest
from pathlib import Path
from evidence_store import EvidenceStore, canonical
from test_evidence_store import experiment
from verify_evidence import MAX_BYTES, verify_export


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name)
        store=EvidenceStore(root/'fixture.db')
        try:
            self.head=store.append('spec','experiment',experiment())
            self.proof=dict(schema_version='lineage-proof.v1',data_class='synthetic',
                            final_head=self.head,events=store.records())
        finally:
            store.close()
        self.path=root/'export.json'

    def verify(self,proof=None,head=None):
        self.path.write_text(json.dumps(self.proof if proof is None else proof))
        return verify_export(self.path,self.head if head is None else head)

    def test_reconstructs_without_mutating_export_or_granting_review(self):
        result=self.verify()
        original=self.path.read_bytes()
        self.assertEqual(1,result['event_count'])
        self.assertEqual('not-granted',result['review_approval'])
        verify_export(self.path,self.head)
        self.assertEqual(original,self.path.read_bytes())

    def test_external_head_and_chain_tampering_denied(self):
        with self.assertRaises(ValueError):
            self.verify(head='sha256:'+'f'*64)
        proof=copy.deepcopy(self.proof)
        proof['events'][0]['record']['owner']='changed'
        proof['events'][0]['record_json']=canonical(proof['events'][0]['record'])
        with self.assertRaises(ValueError):
            self.verify(proof)

    def test_duplicate_reordered_and_mismatched_records_denied(self):
        variants=[]
        proof=copy.deepcopy(self.proof); proof['events']*=2; variants.append(proof)
        proof=copy.deepcopy(self.proof); proof['events'][0]['sequence']=2; variants.append(proof)
        proof=copy.deepcopy(self.proof); proof['events'][0]['record_json']='{}'; variants.append(proof)
        for proof in variants:
            with self.assertRaises(ValueError):
                self.verify(proof)

    def test_ambiguous_json_and_oversized_exports_denied(self):
        self.path.write_text('{"events":[],"events":[]}')
        with self.assertRaisesRegex(ValueError,'duplicate JSON'):
            verify_export(self.path,self.head)
        self.path.write_bytes(b' '*(MAX_BYTES+1))
        with self.assertRaisesRegex(ValueError,'size limit'):
            verify_export(self.path,self.head)
