"""Exact live hardware admission for the HP G20 voice-search pilot."""
from voice_capture import parse_sources
from voice_search import (HardwarePolicy, VoiceUnavailable, capability,
                          parse_capture_pcms, parse_inputs)


INPUT_NAME = 'HAOBO Technology USB Composite Device Keyboard'
# Consumer.00cf is remapped by the HP hwdb to Linux KEY_SEARCH.
VOICE_CODE = 217
CAPTURE_PCM = 'hw:1,0'
PULSE_SOURCE = ('alsa_input.usb-HAOBO_Technology_USB_Composite_Device_'
                '8545124150354735-00.mono-fallback')


def resolve(raw_inputs, raw_pcms, raw_sources):
    inputs = parse_inputs(raw_inputs)
    matches = [row for row in inputs if row.name == INPUT_NAME]
    if len(matches) != 1 or len(matches[0].handlers) != 1:
        raise VoiceUnavailable('voice-event-device-unavailable')
    policy = HardwarePolicy(INPUT_NAME, matches[0].handlers[0], VOICE_CODE,
                            CAPTURE_PCM)
    captures = parse_capture_pcms(raw_pcms)
    result = capability(inputs, captures, policy)
    sources = parse_sources(raw_sources)
    if result.state != 'ready' or sum(row.name == PULSE_SOURCE for row in sources) != 1:
        raise VoiceUnavailable('voice-hardware-unavailable')
    return result, sources
