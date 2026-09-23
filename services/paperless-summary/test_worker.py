import tempfile
import unittest
from pathlib import Path

from broker_contract import source_hash, validate
from pipeline import Pipeline, SafeFailure
from worker import process, Broker


class FakeBroker:
    def __init__(self, documents):
        self.documents = documents
        self.published = []
        self.fail = False

    def snapshot(self):
        if self.fail:
            raise SafeFailure('incomplete')
        return self.documents

    def call(self, request):
        validate(request)
        doc = next(d for d in self.documents if d['id'] == request['id'])
        if source_hash(doc) != request['source_hash']:
            raise ValueError('stale_source')
        self.published.append(request)
        return {'published': True}


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.calls = []
        self.p = Pipeline(str(Path(self.temp.name)/'state.sqlite'),
                          lambda text: self.calls.append(text) or 'Synthetic summary.', 'test-model')
        self.doc = {'id': 1, 'title': 'SYNTHETIC PAPERLESS receipt', 'content': 'Synthetic receipt for a lamp.'}
        self.b = FakeBroker([self.doc])

    def tearDown(self):
        self.p.close()
        self.temp.cleanup()

    def test_publish_and_metadata_change(self):
        self.assertEqual(process(self.p, self.b)['published'], 1)
        self.assertEqual(process(self.p, self.b)['complete'], 0)
        self.doc['title'] += ' changed'
        self.assertEqual(process(self.p, self.b)['complete'], 1)
        self.assertEqual(len(self.calls), 2)

    def test_revoked_or_deleted_local_state_removed(self):
        process(self.p, self.b)
        self.b.documents = []
        process(self.p, self.b)
        self.assertEqual(self.p.db.execute('SELECT count(*) FROM summaries').fetchone()[0], 0)

    def test_incomplete_snapshot_preserves_state(self):
        process(self.p, self.b)
        self.b.fail = True
        with self.assertRaises(SafeFailure):
            process(self.p, self.b)
        self.assertEqual(self.p.db.execute('SELECT count(*) FROM summaries').fetchone()[0], 1)

    def test_real_documents_excluded_until_gate(self):
        self.doc['title'] = 'Household document'
        self.assertEqual(process(self.p, self.b)['published'], 0)
        self.assertEqual(self.calls, [])

    def test_empty_ocr_never_sent(self):
        self.doc['content'] = ''
        self.assertEqual(process(self.p, self.b)['failed'], 1)
        self.assertEqual(self.calls, [])

    def test_stale_during_inference_cannot_publish_summary(self):
        def inference(_):
            self.doc['content'] = 'Changed while summarizing.'
            return 'Stale summary.'
        self.p.infer = inference
        self.assertEqual(process(self.p, self.b)['published'], 0)
        self.assertFalse(any(r['summary'] == 'Stale summary.' for r in self.b.published))

    def test_work_limit(self):
        self.b.documents += [dict(self.doc, id=2)]
        result = process(self.p, self.b, max_documents=1)
        self.assertEqual(result['complete'], 1)
        self.assertEqual(result['deferred'], 1)

    def test_forbidden_broker_fields_and_actions(self):
        for request in [{'action': 'delete', 'id': 1}, {'action': 'read', 'id': True},
                        {'action': 'read', 'id': 1, 'path': '/etc/passwd'},
                        {'action': 'publish', 'id': 1, 'source_hash': '0'*64, 'summary': 'ok', 'field': 5}]:
            with self.assertRaises(ValueError):
                validate(request)

    def test_changed_snapshot_count_aborts(self):
        b = Broker('/unused')
        pages = iter([{'count': 2, 'documents': [self.doc], 'more': True},
                      {'count': 1, 'documents': [], 'more': False}])
        b.call = lambda _: next(pages)
        with self.assertRaises(SafeFailure):
            b.snapshot()


if __name__ == '__main__':
    unittest.main()
