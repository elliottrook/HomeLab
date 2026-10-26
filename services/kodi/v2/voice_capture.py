"""Pure PulseAudio discovery and command contract for explicit voice capture.

The returned argv is intended for a bounded subprocess adapter.  This module
does not execute it, open audio, select a default source or invoke a shell.
"""
from dataclasses import dataclass
import re

from voice_search import VoiceUnavailable


SOURCE = re.compile(r'^[A-Za-z0-9_.:-]{1,255}$')
FORMAT = re.compile(r'^s16le\s+(1|2)ch\s+(16000|24000|44100|48000)Hz$')


@dataclass(frozen=True)
class PulseSource:
    index: int
    name: str
    driver: str
    sample_spec: str
    state: str


def parse_sources(raw):
    if not isinstance(raw, str) or len(raw) > 262144:
        raise VoiceUnavailable('voice-source-inventory-invalid')
    rows = []
    for line in raw.splitlines():
        fields = line.split('\t')
        if len(fields) != 5:
            raise VoiceUnavailable('voice-source-inventory-invalid')
        try:
            index = int(fields[0])
        except ValueError:
            raise VoiceUnavailable('voice-source-inventory-invalid') from None
        name, driver, sample_spec, state = fields[1:]
        if (not 0 <= index <= 4096 or not SOURCE.fullmatch(name)
                or not 1 <= len(driver) <= 255 or not FORMAT.fullmatch(sample_spec)
                or state not in ('RUNNING', 'IDLE', 'SUSPENDED')):
            raise VoiceUnavailable('voice-source-inventory-invalid')
        rows.append(PulseSource(index, name, driver, sample_spec, state))
    if len(rows) > 64 or len({row.name for row in rows}) != len(rows):
        raise VoiceUnavailable('voice-source-inventory-invalid')
    return tuple(rows)


def capture_source(rows, exact_name):
    if not isinstance(rows, tuple) or not isinstance(exact_name, str):
        raise VoiceUnavailable('voice-source-policy-invalid')
    matches = [row for row in rows if row.name == exact_name]
    if len(matches) != 1 or exact_name.endswith('.monitor'):
        raise VoiceUnavailable('voice-source-unavailable')
    return matches[0]


def parec_argv(source):
    if not isinstance(source, PulseSource) or not SOURCE.fullmatch(source.name):
        raise VoiceUnavailable('voice-source-invalid')
    return ('/usr/bin/parec', '--record', '--raw', '--device='+source.name,
            '--rate=16000', '--format=s16le', '--channels=1',
            '--client-name=Aster Voice Search',
            '--stream-name=Explicit voice search')
