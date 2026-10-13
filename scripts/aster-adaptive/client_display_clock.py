"""Offline client clock producer for Adaptive's v0 join; no transport or UI hook.

The caller must mark acceptance and actual final display/failure. Receiving a
backend response alone is not display. No prompt, answer, headers or exception
text is recorded. Deployment and a useful-result review are separate gates.

Implementation copied without functional changes from B60 coordination commit
779af42f, scripts/b60-inference/client_display_clock.py (original SHA-256
b1a3a627970248038927c9f440650864160f07b3da7833ec596db499c334c827).
"""
import math
import re
import time

ID = re.compile(r'[0-9a-f]{32}\Z')


class ClientDisplayClock:
    def __init__(self, clock=time.monotonic_ns):
        self.clock = clock
        self.started = clock()
        self.observation_id = None
        self.status = None
        self.ended = False

    def response_identity(self, observation_id, http_status):
        if self.ended or self.observation_id is not None:
            raise ValueError('response identity already sealed')
        if (not isinstance(observation_id, str) or not ID.fullmatch(observation_id)
                or type(http_status) is not int or not 100 <= http_status <= 599):
            raise ValueError('invalid response identity')
        self.observation_id = observation_id
        self.status = http_status

    def finish(self, *, terminal_displayed):
        if self.ended or type(terminal_displayed) is not bool:
            raise ValueError('invalid or repeated terminal event')
        elapsed = (self.clock() - self.started) / 1_000_000
        if not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError('invalid client monotonic duration')
        self.ended = True
        return {'schema_version': 'aster-client-clock.v0',
                'observation_id': self.observation_id, 'http_status': self.status,
                'accepted_to_displayed_ms': elapsed if terminal_displayed else None,
                'terminal_displayed': terminal_displayed}
