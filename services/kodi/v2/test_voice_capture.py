import unittest

from voice_capture import capture_source, parec_argv, parse_sources
from voice_search import VoiceUnavailable


SOURCES = ('0\tauto_null.monitor\tmodule-null-sink.c\ts16le 2ch 44100Hz\tSUSPENDED\n'
           '4\talsa_input.usb-Aster_G20-00.mono-fallback\tmodule-alsa-card.c\t'
           's16le 1ch 48000Hz\tIDLE\n')


class VoiceCaptureTests(unittest.TestCase):
    def test_exact_non_monitor_source_builds_shell_free_command(self):
        rows = parse_sources(SOURCES)
        source = capture_source(rows, 'alsa_input.usb-Aster_G20-00.mono-fallback')
        argv = parec_argv(source)
        self.assertEqual(argv[0], '/usr/bin/parec')
        self.assertIn('--device='+source.name, argv)
        self.assertNotIn('sh', argv)
        self.assertFalse(any('\n' in value or ';' in value for value in argv))

    def test_default_and_monitor_capture_are_never_selected(self):
        rows = parse_sources(SOURCES)
        for name in ('', '@DEFAULT_SOURCE@', 'auto_null.monitor',
                     'alsa_input.usb-missing'):
            with self.assertRaises(VoiceUnavailable):
                capture_source(rows, name)

    def test_inventory_is_strict_and_bounded(self):
        for raw in ('bad', 'x\tname\tdriver\ts16le 1ch 16000Hz\tIDLE',
                    '1\tbad source\tdriver\ts16le 1ch 16000Hz\tIDLE',
                    '1\tname\tdriver\tfloat32le 1ch 16000Hz\tIDLE'):
            with self.assertRaises(VoiceUnavailable):
                parse_sources(raw)
        with self.assertRaises(VoiceUnavailable):
            parse_sources(SOURCES+SOURCES.splitlines()[1]+'\n')


if __name__ == '__main__':
    unittest.main()
