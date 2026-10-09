"""Offline supervised-readiness contract. No authentication or HTTP transport.

A future integration must provide owner and worker from verified identities and
atomically bind admission to the gateway's durable job creation transaction.
This volatile object deliberately loses readiness on restart. It never stores
credentials, prompts or provider output and cannot grant execution authority.
"""
from dataclasses import dataclass
import secrets
import threading
import time


@dataclass(frozen=True)
class Readiness:
    lease_id: str
    owner: str
    worker: str
    model: str
    scope_sha256: str
    expires_at: float
    ready: bool
    admitted_job: str | None


class WindowUnavailable(Exception):
    pass


class AdmissionWindow:
    def __init__(self, *, clock=time.monotonic, maximum_seconds=240,
                 heartbeat_seconds=20, token_margin_seconds=10):
        if not 0 < heartbeat_seconds < maximum_seconds <= 300:
            raise ValueError('Invalid bounded window')
        if not 0 < token_margin_seconds < maximum_seconds:
            raise ValueError('Invalid credential margin')
        self.clock = clock
        self.maximum_seconds = maximum_seconds
        self.heartbeat_seconds = heartbeat_seconds
        self.token_margin_seconds = token_margin_seconds
        self._current = None
        self._lock = threading.Lock()

    def open(self, *, owner, worker, model, scope_sha256, token_deadline):
        """Called only after the transport verifies the worker and fixed plan.

        token_deadline uses the same monotonic clock and is supplied by the
        verified worker session, not an app request body.
        """
        if not all(isinstance(v, str) and v and len(v) <= 256
                   for v in (owner, worker, model)):
            raise ValueError('Verified identity and model required')
        if (not isinstance(scope_sha256, str) or len(scope_sha256) != 64 or
                any(ch not in '0123456789abcdef' for ch in scope_sha256)):
            raise ValueError('Verified plan digest required')
        if isinstance(token_deadline, bool) or not isinstance(token_deadline, (int, float)):
            raise ValueError('Credential deadline required')
        with self._lock:
            now = self.clock()
            expiry = min(now + self.maximum_seconds,
                         token_deadline - self.token_margin_seconds)
            if expiry - now < self.heartbeat_seconds:
                raise WindowUnavailable('Credential lifetime is insufficient')
            if self._current is not None:
                raise WindowUnavailable('Previous session requires explicit closure and reconciliation')
            value = {'lease_id': secrets.token_hex(16), 'owner': owner,
                     'worker': worker, 'model': model, 'scope_sha256': scope_sha256,
                     'expires_at': expiry, 'last_seen': now, 'admitted_job': None}
            self._current = value
            return self._snapshot(value, now)

    def _ready(self, value, now):
        return (value is not None and value['admitted_job'] is None and
                now < value['expires_at'] and
                0 <= now - value['last_seen'] < self.heartbeat_seconds)

    def _snapshot(self, value, now):
        return Readiness(value['lease_id'], value['owner'], value['worker'],
                         value['model'], value['scope_sha256'],
                         value['expires_at'], self._ready(value, now),
                         value['admitted_job'])

    def status(self, owner):
        with self._lock:
            value = self._current
            if not value or value['owner'] != owner:
                return None
            return self._snapshot(value, self.clock())

    def heartbeat(self, lease_id, worker):
        """Freshness only; never extends the lease or credential deadline."""
        with self._lock:
            value = self._current
            now = self.clock()
            if not value or value['lease_id'] != lease_id or value['worker'] != worker:
                raise WindowUnavailable('Worker session mismatch')
            if not self._ready(value, now):
                raise WindowUnavailable('Session no longer ready')
            value['last_seen'] = now
            return self._snapshot(value, now)

    def admit(self, *, lease_id, owner, worker, model, scope_sha256, job_id):
        """Prototype single-claim rule; durable integration must be transactional."""
        with self._lock:
            value = self._current
            now = self.clock()
            if (not value or not self._ready(value, now) or
                    (value['lease_id'], value['owner'], value['worker'],
                     value['model'], value['scope_sha256']) !=
                    (lease_id, owner, worker, model, scope_sha256) or
                    not isinstance(job_id, str) or not job_id):
                raise WindowUnavailable('Reviewed request is not admissible')
            value['admitted_job'] = job_id
            return self._snapshot(value, now)

    def close(self, lease_id):
        with self._lock:
            if self._current and self._current['lease_id'] == lease_id:
                self._current = None
                return True
            return False
