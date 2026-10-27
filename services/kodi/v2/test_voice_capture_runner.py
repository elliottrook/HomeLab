import subprocess
import sys
import time
import unittest

from voice_capture import PulseSource
from voice_capture_runner import record
from voice_search import VoiceUnavailable


SOURCE = PulseSource(4, 'alsa_input.usb-Aster_G20-00.mono-fallback',
                     'module-alsa-card.c', 's16le 1ch 48000Hz', 'IDLE')


class VoiceCaptureRunnerTests(unittest.TestCase):
    def launcher(self, code):
        self.children = []
        def spawn(argv, **options):
            self.assertEqual(argv[0], '/usr/bin/parec')
            self.assertIn('--device='+SOURCE.name, argv)
            self.assertIs(options['shell'], False)
            child = subprocess.Popen((sys.executable, '-c', code), **options)
            self.children.append(child)
            return child
        return spawn

    def assert_reaped(self):
        self.assertTrue(self.children)
        self.assertTrue(all(child.poll() is not None for child in self.children))

    def test_release_returns_only_pcm_and_reaps_recorder(self):
        started = time.monotonic()
        pcm = record(SOURCE, cancelled=lambda: False,
            released=lambda: time.monotonic()-started > .3,
            _spawn=self.launcher('import os,time; os.write(1,b"\\0\\0"*8000); time.sleep(10)'))
        self.assertEqual(pcm, b'\0\0'*8000)
        self.assert_reaped()

    def test_deadline_stops_recording_and_reaps_recorder(self):
        started = time.monotonic()
        pcm = record(SOURCE, cancelled=lambda: False, released=lambda: False,
            maximum_seconds=.3,
            _spawn=self.launcher('import os,time; os.write(1,b"\\0\\0"*8000); time.sleep(10)'))
        self.assertEqual(len(pcm), 16000)
        self.assertLess(time.monotonic()-started, 2)
        self.assert_reaped()

    def test_cancel_discards_already_recorded_audio_and_reaps_recorder(self):
        started = time.monotonic()
        with self.assertRaisesRegex(VoiceUnavailable, 'recorder-cancelled'):
            record(SOURCE, cancelled=lambda: time.monotonic()-started > .3,
                released=lambda: False,
                _spawn=self.launcher('import os,time; os.write(1,b"\\0\\0"*8000); time.sleep(10)'))
        self.assert_reaped()

    def test_oversized_output_is_refused_and_reaped(self):
        with self.assertRaisesRegex(VoiceUnavailable, 'recorder-size'):
            record(SOURCE, cancelled=lambda: False, released=lambda: False,
                _spawn=self.launcher('import os,time; os.write(1,b"x"*320001); time.sleep(10)'))
        self.assert_reaped()

    def test_early_recorder_exit_is_not_sent_to_speech(self):
        with self.assertRaisesRegex(VoiceUnavailable, 'recorder-ended'):
            record(SOURCE, cancelled=lambda: False, released=lambda: False,
                _spawn=self.launcher('raise SystemExit(7)'))
        self.assert_reaped()

    def test_odd_pcm_is_rejected(self):
        started = time.monotonic()
        with self.assertRaisesRegex(VoiceUnavailable, 'recorder-audio'):
            record(SOURCE, cancelled=lambda: False,
                released=lambda: time.monotonic()-started > .3,
                _spawn=self.launcher('import os,time; os.write(1,b"x"*8001); time.sleep(10)'))
        self.assert_reaped()

    def test_monitor_and_pre_cancel_do_not_launch(self):
        def never(*args, **kwargs):
            self.fail('recorder must not launch')
        with self.assertRaisesRegex(VoiceUnavailable, 'source-unavailable'):
            record(PulseSource(0, 'auto_null.monitor', 'driver',
                               's16le 2ch 48000Hz', 'IDLE'),
                   cancelled=lambda: False, released=lambda: False, _spawn=never)
        with self.assertRaisesRegex(VoiceUnavailable, 'recorder-cancelled'):
            record(SOURCE, cancelled=lambda: True, released=lambda: False, _spawn=never)

    def test_unresponsive_recorder_is_killed_and_late_cancel_wins(self):
        started = time.monotonic()
        with self.assertRaisesRegex(VoiceUnavailable, 'recorder-cancelled'):
            record(SOURCE, cancelled=lambda: time.monotonic()-started > .5,
                released=lambda: time.monotonic()-started > .3,
                _spawn=self.launcher(
                    'import os,time,signal; signal.signal(signal.SIGTERM,signal.SIG_IGN); '
                    'os.write(1,b"\\0\\0"*8000); time.sleep(10)'))
        self.assert_reaped()


if __name__ == '__main__':
    unittest.main()
