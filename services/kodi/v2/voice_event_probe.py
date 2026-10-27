#!/usr/bin/env python3
"""Observe one bounded G20 microphone-button press without opening audio."""

import argparse
import json
import os
from pathlib import Path
import re
import selectors
import struct
import time


EVENT = re.compile(r'event([0-9]{1,3})')
PACKET = struct.Struct('llHHI')
EXPECTED_HOST = 'AsterTV'
EXPECTED_NAME = 'HAOBO Technology USB Composite Device Keyboard'
EV_KEY = 1
VOICE_CODE = 0x246


def observe(handler: str, seconds: float = 20.0):
    match = EVENT.fullmatch(handler)
    if (os.uname().nodename != EXPECTED_HOST or match is None
            or not 1 <= seconds <= 30 or PACKET.size != 24):
        raise ValueError('voice-event-policy')
    name = Path('/sys/class/input') / handler / 'device/name'
    if name.read_text().strip() != EXPECTED_NAME:
        raise ValueError('voice-event-device')
    path = Path('/dev/input') / handler
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
    selector = selectors.DefaultSelector()
    events = []
    started = time.monotonic()
    try:
        selector.register(descriptor, selectors.EVENT_READ)
        while time.monotonic() - started < seconds:
            for _, _ in selector.select(timeout=.1):
                raw = os.read(descriptor, PACKET.size * 16)
                if len(raw) % PACKET.size:
                    raise ValueError('voice-event-framing')
                for offset in range(0, len(raw), PACKET.size):
                    _, _, event_type, code, value = PACKET.unpack(
                        raw[offset:offset + PACKET.size])
                    if event_type == EV_KEY and value in (0, 1, 2):
                        events.append({'code': code, 'value': value})
                pressed = [row for row in events
                           if row['value'] == 1 and row['code'] == VOICE_CODE]
                if pressed and any(row['value'] == 0 and row['code'] == pressed[-1]['code']
                                   for row in events):
                    return {'handler': handler, 'device': EXPECTED_NAME,
                            'events': events[-12:], 'pressed_code': pressed[-1]['code']}
    finally:
        selector.close()
        os.close(descriptor)
    raise ValueError('voice-event-timeout')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('handler')
    parser.add_argument('--seconds', type=float, default=20)
    arguments = parser.parse_args()
    print(json.dumps(observe(arguments.handler, arguments.seconds), sort_keys=True))
