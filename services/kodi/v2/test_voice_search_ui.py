import unittest

from voice_search import Capability, HardwarePolicy, Session, VoiceUnavailable
from voice_search_ui import present


POLICY = HardwarePolicy('Aster Remote', 'event7', 217, 'hw:1,0')
READY = Capability('ready', 'Explicit press-to-listen hardware is present', POLICY)
ABSENT = Capability('unavailable', 'Configured remote microphone is absent', POLICY)


class VoiceSearchUITests(unittest.TestCase):
    def test_absent_hardware_is_truthful_and_keyboard_remains(self):
        view = present(ABSENT, Session())
        self.assertEqual((view.action, view.action_enabled), ('unavailable', False))
        self.assertTrue(view.keyboard_visible)
        self.assertIn('absent', view.status)

    def test_ready_idle_is_explicit_not_ambient(self):
        view = present(READY, Session())
        self.assertEqual((view.action, view.action_label), ('start', 'Start listening'))
        self.assertTrue(view.action_enabled)
        self.assertIn('Press once', view.status)

    def test_listening_and_transcribing_always_offer_cancel(self):
        for session, title in ((Session('listening', 1), 'Listening…'),
                               (Session('transcribing', 1, 4096, 1000), 'Working…')):
            view = present(READY, session)
            self.assertEqual((view.title, view.action), (title, 'cancel'))
            self.assertTrue(view.cancel_visible)
            self.assertFalse(view.keyboard_visible)
            self.assertTrue(view.busy)

    def test_terminal_states_restore_keyboard_and_disclose_outcome(self):
        result = present(READY, Session('results', query='the morning show'))
        self.assertIn('the morning show', result.status)
        cancelled = present(READY, Session('cancelled', reason='Cancelled'))
        self.assertIn('no audio was retained', cancelled.status)
        error = present(READY, Session('error', reason='Listening timed out'))
        self.assertEqual(error.status, 'Listening timed out')
        self.assertTrue(all(view.keyboard_visible for view in (result, cancelled, error)))

    def test_invalid_input_fails_closed(self):
        with self.assertRaises(VoiceUnavailable):
            present('ready', Session())
        with self.assertRaises(VoiceUnavailable):
            present(READY, Session('unknown'))


if __name__ == '__main__':
    unittest.main()
