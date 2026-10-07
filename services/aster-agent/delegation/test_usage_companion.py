import tempfile
import sqlite3
import unittest
from pathlib import Path
from companion import CompanionJobs, NotFound, Unavailable
from session import Session
from store import DispatchStore
from usage import parse_usage
from test_contract import answer, end, event


def usage(total=15):
    part = dict(inputTokens=10, cachedInputTokens=2, outputTokens=5,
                reasoningOutputTokens=3, totalTokens=total)
    return dict(last=dict(part), total=dict(part))


class UsageCompanionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)/'jobs.sqlite'
        self.store = DispatchStore(self.path)
        self.s = Session(self.store, 'j', 't', owner='verified-owner')
        self.s.prepare('fixture')
        self.api = CompanionJobs(self.store, enabled=True)

    def tearDown(self):
        self.store.close(); self.tmp.cleanup()

    def test_disabled_by_default(self):
        with self.assertRaises(Unavailable):
            CompanionJobs(self.store).get('verified-owner', 'j')

    def test_other_owner_and_missing_job_are_indistinguishable(self):
        for owner, job in [('other', 'j'), ('verified-owner', 'missing'), ('', 'j')]:
            with self.assertRaisesRegex(NotFound, '^Job not found$'):
                self.api.get(owner, job)

    def test_legacy_unowned_job_cannot_be_claimed_by_ui(self):
        self.store.claim('legacy', 't')
        with self.assertRaises(NotFound):
            self.api.get('verified-owner', 'legacy')
        self.assertFalse(self.store.claim('legacy', 't', 'verified-owner'))

    def test_missing_usage_is_unknown_not_zero(self):
        view = self.api.get('verified-owner', 'j')
        self.assertEqual(view['usage']['status'], 'unknown')
        self.assertIsNone(view['usage']['cost'])
        self.assertIsNone(view['usage']['quota_remaining'])

    def test_usage_before_ack_and_after_completion(self):
        self.s.receive(event('thread/tokenUsage/updated', tokenUsage=usage()))
        self.assertIsNone(self.store.usage('j'))
        self.s.acknowledge('u')
        self.s.receive(answer()); self.s.receive(end())
        self.s.receive(event('thread/tokenUsage/updated', tokenUsage=usage(20)))
        self.assertEqual(self.store.usage('j')['total']['totalTokens'], 20)

    def test_duplicate_usage_is_snapshot_not_sum(self):
        self.s.acknowledge('u')
        m = event('thread/tokenUsage/updated', tokenUsage=usage())
        self.s.receive(m); self.s.receive(m)
        self.assertEqual(self.store.usage('j')['total']['totalTokens'], 15)

    def test_wrong_turn_and_malformed_usage_ignored(self):
        self.s.acknowledge('u')
        m = event('thread/tokenUsage/updated', tokenUsage=usage()); m['params']['turnId'] = 'other'
        self.s.receive(m)
        for value in (-1, True, '15', 10**16):
            bad = usage(); bad['last']['totalTokens'] = value
            self.s.receive(event('thread/tokenUsage/updated', tokenUsage=bad))
        self.assertIsNone(self.store.usage('j'))

    def test_usage_discards_unrecognized_sensitive_fields(self):
        data = usage(); data['raw_prompt'] = 'secret'
        data['last']['reasoning_text'] = 'secret'
        self.assertNotIn('secret', str(parse_usage(data)))

    def test_cancel_is_owner_scoped_and_not_reported_stopped(self):
        self.s.acknowledge('u')
        with self.assertRaises(NotFound):
            self.api.request_cancel('other', 'j', self.s)
        request = self.api.request_cancel('verified-owner', 'j', self.s)
        self.assertEqual(request['params'], {'threadId': 't', 'turnId': 'u'})
        view = self.api.get('verified-owner', 'j', self.s)
        self.assertEqual(view['state'], 'cancel_requested')
        self.assertFalse(view['can_request_cancel'])
        self.s.receive(end('interrupted'))
        self.assertEqual(self.api.get('verified-owner','j',self.s)['state'], 'interrupted')

    def test_disconnect_status_and_usage_survive_restart(self):
        self.s.acknowledge('u')
        self.s.receive(event('thread/tokenUsage/updated', tokenUsage=usage()))
        self.s.disconnect(); self.store.close()
        self.store = DispatchStore(self.path); self.api = CompanionJobs(self.store, enabled=True)
        view = self.api.get('verified-owner', 'j')
        self.assertEqual(view['state'], 'unknown')
        self.assertEqual(view['usage']['status'], 'reported')
        self.assertFalse(view['automatic_retry'])

    def test_final_answer_is_faithful_and_internal_ids_not_exposed(self):
        self.s.acknowledge('u'); self.s.receive(answer('<script>literal</script>')); self.s.receive(end())
        view = self.api.get('verified-owner', 'j', self.s)
        self.assertEqual(view['reply'], '<script>literal</script>')
        for key in ('thread_id', 'turn_id', 'owner', 'failure_class'):
            self.assertNotIn(key, view)

    def test_completed_without_in_memory_answer_requires_recovery(self):
        self.s.acknowledge('u'); self.s.receive(answer()); self.s.receive(end())
        view = self.api.get('verified-owner', 'j')
        self.assertEqual(view['state'], 'completed')
        self.assertIsNone(view['reply'])
        self.assertIn('recovered', view['message'])

    def test_stale_running_row_without_live_session_is_unknown(self):
        self.s.acknowledge('u')
        view = self.api.get('verified-owner', 'j')
        self.assertEqual(view['state'], 'unknown')
        self.assertFalse(view['can_request_cancel'])

    def test_legacy_schema_migration_preserves_job_without_granting_owner(self):
        path = Path(self.tmp.name)/'legacy.sqlite'
        db = sqlite3.connect(path)
        db.execute('CREATE TABLE jobs(job_id TEXT PRIMARY KEY,state TEXT NOT NULL,thread_id TEXT,turn_id TEXT)')
        db.execute("INSERT INTO jobs VALUES ('old','completed','thread','turn')")
        db.commit(); db.close()
        legacy = DispatchStore(path)
        try:
            self.assertEqual(legacy.inspect('old'), ('completed','thread','turn'))
            self.assertIsNone(legacy.inspect_owned('old','verified-owner'))
            self.assertFalse(legacy.claim('old','thread','verified-owner'))
        finally:
            legacy.close()
