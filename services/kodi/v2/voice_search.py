"""Pure privacy and hardware contract for explicit Aster voice search.

This module never opens an input device, records audio or contacts speech.
Hardware becomes usable only after an exact device/event/capture policy has
been observed and recorded for the target box.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import re

from global_search import SearchUnavailable, normalize_query


class VoiceUnavailable(ValueError):
    pass


@dataclass(frozen=True)
class InputDevice:
    name: str
    handlers: tuple


@dataclass(frozen=True)
class CaptureDevice:
    card: int
    device: int
    label: str

    @property
    def pcm(self):
        return f'hw:{self.card},{self.device}'


@dataclass(frozen=True)
class HardwarePolicy:
    input_name: str
    event_handler: str
    event_code: int
    capture_pcm: str


@dataclass(frozen=True)
class Capability:
    state: str
    reason: str
    policy: HardwarePolicy | None = None


@dataclass(frozen=True)
class Session:
    state: str = 'idle'
    started_at: float | None = None
    audio_bytes: int = 0
    duration_ms: int = 0
    query: str = ''
    reason: str = ''


INPUT_NAME = re.compile(r'^N: Name="([^"\r\n]{1,160})"$')
HANDLERS = re.compile(r'^H: Handlers=(.+)$')
EVENT = re.compile(r'^event\d{1,3}$')
PCM = re.compile(r'^(\d{2})-(\d{2}):\s+(.{1,160}?)\s+:.*\bcapture\b')
PCM_ID = re.compile(r'^hw:(\d{1,2}),(\d{1,2})$')
STATES = frozenset(('idle', 'listening', 'transcribing', 'results',
                    'cancelled', 'error'))


def parse_inputs(raw):
    if not isinstance(raw, str) or len(raw) > 262144:
        raise VoiceUnavailable('input-inventory-invalid')
    devices = []
    for block in raw.split('\n\n'):
        name = None
        handlers = None
        for line in block.splitlines():
            match = INPUT_NAME.fullmatch(line)
            if match:
                name = match.group(1)
            match = HANDLERS.fullmatch(line)
            if match:
                handlers = tuple(sorted(token for token in match.group(1).split()
                                        if EVENT.fullmatch(token)))
        if name and handlers:
            devices.append(InputDevice(name, handlers))
    if len(devices) > 128 or len({(row.name, row.handlers) for row in devices}) != len(devices):
        raise VoiceUnavailable('input-inventory-invalid')
    return tuple(devices)


def parse_capture_pcms(raw):
    if not isinstance(raw, str) or len(raw) > 262144:
        raise VoiceUnavailable('capture-inventory-invalid')
    rows = []
    for line in raw.splitlines():
        match = PCM.match(line)
        if not match:
            continue
        card, device = int(match.group(1)), int(match.group(2))
        rows.append(CaptureDevice(card, device, ' '.join(match.group(3).split())))
    if len(rows) > 64 or len({row.pcm for row in rows}) != len(rows):
        raise VoiceUnavailable('capture-inventory-invalid')
    return tuple(rows)


def validate_policy(policy):
    if (not isinstance(policy, HardwarePolicy)
            or not 0 < len(policy.input_name) <= 160
            or not EVENT.fullmatch(policy.event_handler)
            or type(policy.event_code) is not int
            or not 1 <= policy.event_code <= 0x2ff
            or not PCM_ID.fullmatch(policy.capture_pcm)):
        raise VoiceUnavailable('voice-policy-invalid')
    return policy


def capability(inputs, captures, policy=None):
    if policy is None:
        return Capability('unconfigured', 'No exact remote microphone policy recorded')
    validate_policy(policy)
    matches = [row for row in inputs
               if row.name == policy.input_name and policy.event_handler in row.handlers]
    if len(matches) != 1:
        return Capability('unavailable', 'Configured remote event device is absent', policy)
    if sum(row.pcm == policy.capture_pcm for row in captures) != 1:
        return Capability('unavailable', 'Configured microphone capture device is absent', policy)
    return Capability('ready', 'Explicit press-to-listen hardware is present', policy)


def begin(session, hardware, now):
    if (session.state not in STATES or session.state not in ('idle', 'cancelled', 'error', 'results')
            or hardware.state != 'ready' or not isinstance(now, (int, float))):
        raise VoiceUnavailable('voice-start-denied')
    return Session('listening', float(now))


def captured(session, audio_bytes, duration_ms, now):
    if (session.state != 'listening' or session.started_at is None
            or type(audio_bytes) is not int or not 1024 <= audio_bytes <= 15 * 1024 * 1024
            or type(duration_ms) is not int or not 250 <= duration_ms <= 10_000
            or not isinstance(now, (int, float)) or not session.started_at <= now <= session.started_at + 12):
        raise VoiceUnavailable('voice-capture-invalid')
    return replace(session, state='transcribing', audio_bytes=audio_bytes,
                   duration_ms=duration_ms)


def transcript(session, text):
    if session.state != 'transcribing':
        raise VoiceUnavailable('voice-transcript-denied')
    try:
        query = normalize_query(text)
    except SearchUnavailable:
        raise VoiceUnavailable('voice-transcript-invalid') from None
    if not query:
        return replace(session, state='error', reason='No speech recognized')
    return replace(session, state='results', query=query)


def cancel(session):
    if session.state not in ('listening', 'transcribing'):
        raise VoiceUnavailable('voice-cancel-denied')
    return Session('cancelled', reason='Cancelled')


def expire(session, now):
    if (session.state != 'listening' or session.started_at is None
            or not isinstance(now, (int, float))):
        raise VoiceUnavailable('voice-expiry-denied')
    return (Session('error', reason='Listening timed out')
            if now >= session.started_at + 10 else session)
