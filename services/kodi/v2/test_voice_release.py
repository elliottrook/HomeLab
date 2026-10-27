import os
import unittest
from unittest.mock import patch

from voice_release import PACKET, ReleaseSignal
from voice_search import VoiceUnavailable


class ReleaseSignalTests(unittest.TestCase):
    def signal(self):
        return ReleaseSignal('event17', 0x246, _open=lambda *args: 41)

    def test_only_exact_voice_release_completes(self):
        signal = self.signal()
        packets = (PACKET.pack(0, 0, 1, 353, 0)
                   + PACKET.pack(0, 0, 1, 0x246, 1)
                   + PACKET.pack(0, 0, 1, 0x246, 0))
        with patch('voice_release.os.read', return_value=packets):
            self.assertTrue(signal.released())
        with patch('voice_release.os.close') as close:
            signal.close(); signal.close()
        close.assert_called_once_with(41)

    def test_no_data_is_not_release_and_policy_is_fixed(self):
        signal = self.signal()
        with patch('voice_release.os.read', side_effect=BlockingIOError):
            self.assertFalse(signal.released())
        with patch('voice_release.os.close'):
            signal.close()
        for handler, code in (('../event17', 0x246), ('event17', 353)):
            with self.assertRaises(VoiceUnavailable):
                ReleaseSignal(handler, code, _open=lambda *args: 1)

    def test_malformed_kernel_frame_fails_closed(self):
        signal = self.signal()
        with patch('voice_release.os.read', return_value=b'x'):
            with self.assertRaises(VoiceUnavailable):
                signal.released()
        with patch('voice_release.os.close'):
            signal.close()


if __name__ == '__main__':
    unittest.main()
