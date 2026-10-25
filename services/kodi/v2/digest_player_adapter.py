"""Owned Digest command adapter with readback and an uncertainty fence.

No Kodi imports: the injected port establishes callback/session continuity and
immutable media identity. It supplies sample(), seek(seconds), stop(), idle().
Command acknowledgements alone are never proof of playback state. An uncertain
write is fenced, not retried; the caller must surface recovery to the operator.
"""
from digest_playback_state import Observation, PlaybackState


class Adapter:
    def __init__(self, timeline, session, media, port):
        self.state = PlaybackState(timeline, session, media)
        self.port = port
        self.fenced = False
        self.pending = None
        self.closed = False

    def _sample(self):
        observation = self.port.sample()
        if not isinstance(observation, Observation): raise ValueError('typed-observation-required')
        return observation

    def poll(self):
        if self.fenced or self.closed: return self.state.view
        try:
            observation = self._sample()
            view = self.state.observe(observation)
            if view.phase == 'lost':
                self.fenced = True
                self.pending = None
            elif self.pending is not None and observation.sequence > self.pending.sequence:
                if abs(observation.elapsed - self.pending.start) <= 2:
                    self.pending = None
                else:
                    # Native adapter may wait a bounded seek-settlement interval
                    # before calling poll; never send the same seek twice.
                    self.fenced = True
            return view
        except (OSError, RuntimeError, ValueError, KeyError, TypeError):
            self.fenced = True
            raise

    def seek(self, chapter):
        if self.fenced or self.closed or self.pending is not None:
            raise ValueError('adapter-not-ready')
        self.poll()
        was_paused = self.state.view.paused
        propose = lambda:self.state.opening() if chapter is None else self.state.seek(chapter)
        intent = propose()
        try:
            immediate = self._sample()
            # A new sample can advance its sequence, but must preserve ownership.
            self.state.observe(immediate)
            intent = propose()
            if not self.state.current(intent, immediate): raise ValueError('ownership-not-current')
            self.pending = intent  # Set before calling the port: failures are uncertain.
            self.port.seek(intent.start)
            # Kodi can resume audio as a side effect of seeking a paused MP3.
            # Restore the user's paused state with guarded readback.
            if was_paused: self.port.set_paused(True)
        except (OSError, RuntimeError, ValueError, KeyError, TypeError):
            self.fenced = True
            raise
        return intent

    def paused(self, value):
        if type(value) is not bool or self.fenced or self.closed or self.pending is not None:
            raise ValueError('adapter-not-ready')
        self.poll()
        try:
            immediate = self._sample()
            self.state.observe(immediate)
            intent = self.state.control('pause' if value else 'resume')
            if not self.state.current(intent, immediate): raise ValueError('ownership-not-current')
            self.port.set_paused(value)
            view = self.poll()
            if self.fenced or view.paused != value: raise ValueError('pause-readback-mismatch')
            return view
        except (OSError, RuntimeError, ValueError, KeyError, TypeError):
            self.fenced = True
            raise

    def close(self):
        if self.closed: return False
        self.closed = True
        if self.fenced: return False
        try:
            first = self._sample()
            self.state.observe(first)
            immediate = self._sample()
            # close() itself checks ownership and freshness, and consumes its
            # one stop proposal. Never reuse a prior seek/stop observation.
            intent = self.state.close(immediate)
            if intent is None: return False
            self.port.stop()
            # idle() must independently query all native players, not a local flag.
            if self.port.idle() is not True:
                self.fenced = True
                return False
            self.pending = None
            return True
        except (OSError, RuntimeError, ValueError, KeyError, TypeError):
            self.fenced = True
            raise
