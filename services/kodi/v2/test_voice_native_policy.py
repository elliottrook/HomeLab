import unittest

from voice_native_policy import (CAPTURE_PCM, INPUT_NAME, PULSE_SOURCE,
                                 VOICE_CODE, resolve)
from voice_search import VoiceUnavailable


INPUTS = ('N: Name="' + INPUT_NAME + '"\nH: Handlers=sysrq kbd leds event17 \n\n')
PCMS = '01-00: USB Audio : USB Audio : capture 1\n'
SOURCES = '1\t' + PULSE_SOURCE + '\tmodule-alsa-source.c\ts16le 1ch 16000Hz\tSUSPENDED\n'


class NativePolicyTests(unittest.TestCase):
    def test_resolves_dynamic_handler_but_fixed_identity_code_and_audio(self):
        capability, sources = resolve(INPUTS, PCMS, SOURCES)
        self.assertEqual(capability.state, 'ready')
        self.assertEqual((capability.policy.event_handler,
                          capability.policy.event_code,
                          capability.policy.capture_pcm),
                         ('event17', VOICE_CODE, CAPTURE_PCM))
        self.assertEqual(sources[0].name, PULSE_SOURCE)

    def test_missing_duplicate_or_monitor_source_fails_closed(self):
        for inputs, sources in ((INPUTS.replace('event17', ''), SOURCES),
                                (INPUTS + INPUTS, SOURCES),
                                (INPUTS, SOURCES.replace(PULSE_SOURCE, PULSE_SOURCE + '.monitor'))):
            with self.assertRaises(VoiceUnavailable):
                resolve(inputs, PCMS, sources)


if __name__ == '__main__':
    unittest.main()
