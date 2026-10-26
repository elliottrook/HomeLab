import json
import unittest

from voice_capture import parse_sources
from voice_search import Capability, HardwarePolicy, VoiceUnavailable
from voice_search_runtime import VoiceRuntime


TOKEN = 'v' * 48
POLICY = HardwarePolicy('Aster Remote', 'event7', 0x246, 'hw:1,0')
READY = Capability('ready', 'Explicit press-to-listen hardware is present', POLICY)
ABSENT = Capability('unavailable', 'Configured remote microphone is absent', POLICY)
SOURCES = parse_sources('4\talsa_input.usb-Aster_G20-00.mono-fallback\t'
                        'module-alsa-card.c\ts16le 1ch 48000Hz\tIDLE\n')
NAME = SOURCES[0].name
PCM = b'\x00\x00' * 16000


class VoiceSearchRuntimeTests(unittest.TestCase):
    def test_full_pure_flow_returns_normalized_existing_search_query(self):
        runtime, argv = VoiceRuntime().start(READY, SOURCES, NAME, 10)
        self.assertEqual(argv[0], '/usr/bin/parec')
        runtime, audio = runtime.accept_pcm(PCM, 11)
        wire = runtime.speech_request(audio, TOKEN)
        self.assertEqual(wire.path, '/v1/stt')
        runtime = runtime.complete(200, 'application/json',
                                   json.dumps({'text': '  The   Morning Show '}).encode())
        self.assertEqual((runtime.session.state, runtime.session.query),
                         ('results', 'The Morning Show'))
        self.assertNotIn(TOKEN, repr(runtime))

    def test_absent_capability_wrong_source_and_bad_audio_fail_closed(self):
        for capability, source in ((ABSENT, NAME), (READY, 'missing')):
            with self.assertRaises(VoiceUnavailable):
                VoiceRuntime().start(capability, SOURCES, source, 1)
        runtime, _ = VoiceRuntime().start(READY, SOURCES, NAME, 1)
        for pcm in (b'', b'\x00', b'\x00\x00' * 200000):
            with self.assertRaises((VoiceUnavailable, ValueError)):
                runtime.accept_pcm(pcm, 2)

    def test_cancel_discards_capture_state_and_blocks_late_results(self):
        runtime, _ = VoiceRuntime().start(READY, SOURCES, NAME, 1)
        runtime = runtime.stop()
        self.assertEqual(runtime.session.state, 'cancelled')
        with self.assertRaises(VoiceUnavailable):
            runtime.complete(200, 'application/json', b'{"text":"late"}')

    def test_wire_calls_require_transcribing_state(self):
        runtime = VoiceRuntime()
        with self.assertRaises(VoiceUnavailable):
            runtime.speech_request(PCM, TOKEN)
        with self.assertRaises(VoiceUnavailable):
            runtime.complete(200, 'application/json', b'{"text":"late"}')


if __name__ == '__main__':
    unittest.main()
