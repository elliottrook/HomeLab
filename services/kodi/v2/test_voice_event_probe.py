#!/usr/bin/env python3

import struct
import unittest

import voice_event_probe


class EventProbeTests(unittest.TestCase):
    def test_linux_input_packet_contract_is_exact(self):
        self.assertEqual(voice_event_probe.PACKET.size, 24)
        raw = voice_event_probe.PACKET.pack(1, 2, 1, 248, 1)
        self.assertEqual(voice_event_probe.PACKET.unpack(raw)[2:], (1, 248, 1))
        self.assertEqual(voice_event_probe.VOICE_CODE, 582)

    def test_handler_and_device_are_fixed(self):
        self.assertTrue(voice_event_probe.EVENT.fullmatch('event17'))
        self.assertFalse(voice_event_probe.EVENT.fullmatch('../event17'))
        self.assertEqual(voice_event_probe.EXPECTED_HOST, 'AsterTV')
        self.assertIn('HAOBO', voice_event_probe.EXPECTED_NAME)


if __name__ == '__main__':
    unittest.main()
