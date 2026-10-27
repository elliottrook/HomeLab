import unittest

from voice_search import (HardwarePolicy, Session, VoiceUnavailable, begin,
                          cancel, capability, captured, expire, parse_capture_pcms,
                          normalize_spoken_query, parse_inputs, transcript)


INPUTS = '''I: Bus=0003 Vendor=1234 Product=5678 Version=0001
N: Name="Aster Test Remote"
P: Phys=usb-test/input0
H: Handlers=sysrq kbd event7
B: EV=120013

N: Name="Mouse"
H: Handlers=mouse0 event8
B: EV=17
'''
PCMS = '''00-00: Aster USB Audio : Aster USB Audio : playback 1 : capture 1
00-01: HDMI : HDMI : playback 1
'''
POLICY = HardwarePolicy('Aster Test Remote', 'event7', 217, 'hw:0,0')


class VoiceSearchTests(unittest.TestCase):
    def test_inventory_is_bounded_and_does_not_infer_hardware(self):
        inputs = parse_inputs(INPUTS)
        captures = parse_capture_pcms(PCMS)
        self.assertEqual(inputs[0].handlers, ('event7',))
        self.assertEqual(captures[0].pcm, 'hw:0,0')
        self.assertEqual(capability(inputs, captures).state, 'unconfigured')

    def test_exact_policy_requires_both_trigger_and_capture(self):
        inputs = parse_inputs(INPUTS)
        captures = parse_capture_pcms(PCMS)
        self.assertEqual(capability(inputs, captures, POLICY).state, 'ready')
        self.assertEqual(capability(inputs, (), POLICY).state, 'unavailable')
        changed = HardwarePolicy(POLICY.input_name, 'event6', POLICY.event_code,
                                 POLICY.capture_pcm)
        self.assertEqual(capability(inputs, captures, changed).state, 'unavailable')

    def test_explicit_session_reaches_normalized_results(self):
        ready = capability(parse_inputs(INPUTS), parse_capture_pcms(PCMS), POLICY)
        listening = begin(Session(), ready, 100)
        working = captured(listening, 4096, 1250, 103)
        result = transcript(working, '  Science   Fiction  ')
        self.assertEqual((result.state, result.query), ('results', 'Science Fiction'))

    def test_spoken_command_prefix_is_bounded(self):
        self.assertEqual(normalize_spoken_query('Search for Dune'), 'Dune')
        self.assertEqual(normalize_spoken_query('Search Party'), 'Search Party')
        self.assertEqual(normalize_spoken_query('search for Search Party'),
                         'Search Party')
        self.assertEqual(normalize_spoken_query('Search for Dune.'), 'Dune')

    def test_cancel_and_timeout_discard_session_state(self):
        ready = capability(parse_inputs(INPUTS), parse_capture_pcms(PCMS), POLICY)
        listening = begin(Session(), ready, 100)
        self.assertEqual(expire(listening, 109).state, 'listening')
        timed_out = expire(listening, 110)
        self.assertEqual((timed_out.state, timed_out.audio_bytes), ('error', 0))
        self.assertEqual(cancel(listening).state, 'cancelled')

    def test_capture_transcript_and_transition_bounds_fail_closed(self):
        ready = capability(parse_inputs(INPUTS), parse_capture_pcms(PCMS), POLICY)
        listening = begin(Session(), ready, 100)
        for size, duration, now in ((0, 1000, 101), (4096, 11_000, 101),
                                    (4096, 1000, 113)):
            with self.assertRaises(VoiceUnavailable):
                captured(listening, size, duration, now)
        with self.assertRaises(VoiceUnavailable):
            transcript(Session(), 'movies')
        with self.assertRaises(VoiceUnavailable):
            begin(Session(), capability((), (), POLICY), 1)

    def test_malformed_inventory_and_policy_are_refused(self):
        with self.assertRaises(VoiceUnavailable):
            parse_inputs('x' * 262145)
        with self.assertRaises(VoiceUnavailable):
            parse_capture_pcms('00-00: one : one : capture 1\n00-00: two : two : capture 1')
        bad = HardwarePolicy('Remote', '../event7', 1, 'default')
        with self.assertRaises(VoiceUnavailable):
            capability((), (), bad)


if __name__ == '__main__':
    unittest.main()
