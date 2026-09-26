import sqlite3
import tempfile
import unittest
from pathlib import Path

from evidence_store import EvidenceStore

D='sha256:'+'1'*64


def experiment():
    return dict(experiment_id='fixture-experiment',owner='fixture-proposer',baseline_digest=D,
                candidate_digest=D,evaluator_digest=D,dataset_digest=D,status='preregistered',
                metric='offline-payload-construction-ms')


def evaluation():
    return dict(experiment_id='fixture-experiment',candidate_digest=D,evaluator_digest=D,dataset_digest=D,
                independent_units=10,passed_units=1,verdict='fail')


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.root=tempfile.TemporaryDirectory()
        self.addCleanup(self.root.cleanup)
        self.path=Path(self.root.name)/'ledger.db'
        self.store=EvidenceStore(self.path)
        self.addCleanup(lambda:self.store.close())

    def test_idempotent_append_and_conflicting_replay(self):
        first=self.store.append('e1','experiment',experiment())
        self.assertEqual(first,self.store.append('e1','experiment',experiment()))
        self.assertEqual(1,len(self.store.records()))
        with self.assertRaises(ValueError):
            self.store.append('e1','experiment',experiment()|{'owner':'other'})

    def test_frozen_specification_and_evaluator(self):
        self.store.append('e1','experiment',experiment())
        with self.assertRaises(ValueError):
            self.store.append('e2','experiment',experiment())
        with self.assertRaises(ValueError):
            self.store.append('eval','evaluation',evaluation()|{'evaluator_digest':'sha256:'+'2'*64})
        self.assertEqual(1,len(self.store.records()))

    def test_raw_content_and_promotion_not_persistable(self):
        with self.assertRaises(ValueError):
            self.store.append('e1','experiment',experiment()|{'prompt':'private content'})
        with self.assertRaises(ValueError):
            self.store.append('e1','experiment',experiment()|{'promotion_authority':'automatic'})
        self.assertEqual([],self.store.records())

    def test_evaluation_requires_spec_and_valid_denominator(self):
        with self.assertRaises(ValueError):
            self.store.append('eval','evaluation',evaluation())
        self.store.append('e1','experiment',experiment())
        with self.assertRaises(ValueError):
            self.store.append('eval','evaluation',evaluation()|{'passed_units':11})

    def test_review_binds_exact_evaluation_and_cannot_execute(self):
        self.store.append('e1','experiment',experiment())
        h=self.store.append('eval','evaluation',evaluation())
        r=dict(experiment_id='fixture-experiment',evaluation_digest=h,reviewer_ref='fixture-reviewer',
               decision='retain-baseline',reason='guardrail-failed')
        with self.assertRaises(ValueError):
            self.store.append('review','review',r|{'execution_authority':'deploy'})
        self.store.append('review','review',r)
        with self.assertRaises(ValueError):
            self.store.append('another-review','review',r)
        with self.assertRaisesRegex(ValueError,'already reviewed'):
            self.store.append('late-eval','evaluation',evaluation())
        self.assertEqual(3,len(self.store.records()))

    def test_update_delete_refused(self):
        self.store.append('e1','experiment',experiment())
        for sql in ('DELETE FROM events','UPDATE events SET kind="review"'):
            with self.assertRaises(sqlite3.IntegrityError):
                with self.store.connection:
                    self.store.connection.execute(sql)

    def test_hash_chain_detects_tampering(self):
        self.store.append('e1','experiment',experiment())
        with self.store.connection:
            self.store.connection.execute('DROP TRIGGER evidence_no_update')
            self.store.connection.execute("UPDATE events SET event_digest=?",('sha256:'+'a'*64,))
        with self.assertRaisesRegex(ValueError,'chain'):
            self.store.verify()

    def test_backup_restore_and_external_head_detect_truncation(self):
        head=self.store.append('e1','experiment',experiment())
        destination=Path(self.root.name)/'backup.db'
        self.assertEqual(head,self.store.backup(destination))
        restored=EvidenceStore(destination)
        self.addCleanup(restored.close)
        self.assertEqual(head,restored.verify(expected_head=head))
        with self.assertRaises(FileExistsError):
            self.store.backup(destination)
        with restored.connection:
            restored.connection.execute('DROP TRIGGER evidence_no_delete')
            restored.connection.execute('DELETE FROM events')
        with self.assertRaisesRegex(ValueError,'external checkpoint'):
            restored.verify(expected_head=head)

    def test_restart_and_interrupted_transaction(self):
        head=self.store.append('e1','experiment',experiment())
        self.store.connection.execute('BEGIN IMMEDIATE')
        self.store.connection.execute("INSERT INTO events(event_id,kind,record_json,previous_digest,event_digest) VALUES('partial','outcome','{}','bad','bad')")
        self.store.close()  # SQLite rolls back the uncommitted write.
        self.store=EvidenceStore(self.path)
        self.assertEqual(head,self.store.verify())
        self.assertEqual(1,len(self.store.records()))

    def test_separate_connections_racing_same_event_commit_once(self):
        import concurrent.futures
        import threading
        barrier=threading.Barrier(4)
        def append(_):
            store=EvidenceStore(self.path)
            try:
                barrier.wait(timeout=5)
                return store.append('e1','experiment',experiment())
            finally:
                store.close()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            heads=list(pool.map(append,range(4)))
        self.assertEqual(1,len(set(heads)))
        self.assertEqual(1,len(self.store.records()))
