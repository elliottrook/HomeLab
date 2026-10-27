import unittest

from test_voice_search_runtime import ABSENT, NAME, PCM, READY, SOURCES, TOKEN
from voice_search_attempt import attempt


class VoiceAttemptTests(unittest.TestCase):
    def run_attempt(self, **overrides):
        self.views = []
        self.calls = []
        def recorder(source, **signals):
            self.calls.append('capture')
            return PCM
        def token():
            self.calls.append('token')
            return TOKEN
        def transport(wire, **signals):
            self.calls.append('transport')
            self.assertEqual(wire.timeout, 20)
            self.assertEqual(wire.path, '/v1/stt')
            return 200, 'application/json', b'{"text":" The  Morning Show "}'
        moments = iter((10, 11))
        options = dict(cancelled=lambda: False, released=lambda: True,
                       token=token, transport=transport, changed=self.views.append,
                       recorder=recorder, clock=lambda: next(moments))
        options.update(overrides)
        return attempt(READY, SOURCES, NAME, **options)

    def test_capture_transcribe_and_normalized_query_without_retained_secret(self):
        result = self.run_attempt()
        self.assertEqual((result.state, result.query), ('results', 'The Morning Show'))
        self.assertEqual(self.calls, ['capture', 'token', 'transport'])
        self.assertEqual([view.title for view in self.views],
                         ['Listening…', 'Working…', 'Voice search'])
        self.assertNotIn(TOKEN, repr(result)+repr(self.views))
        self.assertTrue(self.views[-1].keyboard_visible)

    def test_pre_cancel_never_opens_capture_or_gets_credential(self):
        result = self.run_attempt(cancelled=lambda: True)
        self.assertEqual(result.state, 'cancelled')
        self.assertEqual(self.calls, [])

    def test_cancel_after_recording_never_transmits(self):
        flag = [False]
        def recorder(*args, **kwargs):
            flag[0] = True
            return PCM
        result = self.run_attempt(recorder=recorder, cancelled=lambda: flag[0])
        self.assertEqual(result.state, 'cancelled')
        self.assertEqual(self.calls, [])

    def test_cancel_during_transport_discards_late_transcript(self):
        flag = [False]
        def transport(*args, **kwargs):
            flag[0] = True
            return 200, 'application/json', b'{"text":"must not search"}'
        result = self.run_attempt(transport=transport, cancelled=lambda: flag[0])
        self.assertEqual((result.state, result.query), ('cancelled', ''))

    def test_transport_failure_never_retries_or_exposes_exception(self):
        count = [0]
        def transport(*args, **kwargs):
            count[0] += 1
            raise OSError('secret '+TOKEN)
        result = self.run_attempt(transport=transport)
        self.assertEqual(count[0], 1)
        self.assertEqual(result.state, 'error')
        self.assertNotIn(TOKEN, repr(result)+repr(self.views))
        self.assertTrue(self.views[-1].keyboard_visible)

    def test_empty_transcript_has_clear_retry_feedback(self):
        result = self.run_attempt(
            transport=lambda *args, **kwargs:
            (200, 'application/json', b'{"text":""}'))
        self.assertEqual(result.state, 'error')
        self.assertEqual(result.reason, 'I could not hear a search · try again')
        self.assertEqual(self.views[-1].status, result.reason)

    def test_absent_hardware_does_not_capture(self):
        calls = []
        result = attempt(ABSENT, SOURCES, NAME, cancelled=lambda: False,
                         released=lambda: False, token=lambda: calls.append('token'),
                         transport=lambda *a, **k: calls.append('transport'),
                         changed=lambda view: None,
                         recorder=lambda *a, **k: calls.append('capture'))
        self.assertEqual(result.state, 'error')
        self.assertEqual(calls, [])


if __name__ == '__main__':
    unittest.main()
