"""Pure Digest UI state and bounded intents; no player, network or storage I/O.

The future adapter must independently establish an immutable media fingerprint
and unique session token and recheck ownership immediately before any command.
These values are matching evidence, not authentication or permission grants.
"""
from dataclasses import dataclass
from digest_timeline import Timeline, seconds


def identity(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 128 or not value.isascii() or not all(c.isalnum() or c in '-_' for c in value):
        raise ValueError('invalid-opaque-identity')
    return value


@dataclass(frozen=True)
class Observation:
    session: str
    media: str
    edition: str
    sequence: int
    elapsed: float
    paused: bool = False
    ended: bool = False


@dataclass(frozen=True)
class View:
    phase: str
    chapter: object = None
    elapsed: float = 0
    paused: bool = False


@dataclass(frozen=True)
class Intent:
    kind: str
    session: str
    media: str
    edition: str
    sequence: int
    start: object = None


class PlaybackState:
    def __init__(self, timeline, session, media):
        if not isinstance(timeline, Timeline) or not timeline.duration_verified:
            raise ValueError('verified-timeline-required')
        self.timeline = timeline
        self.session, self.media = identity(session), identity(media)
        self.sequence = -1
        self.view = View('waiting')

    def _matches(self, observation):
        return (observation.session, observation.media, observation.edition) == (
            self.session, self.media, self.timeline.identity)

    def observe(self, observation):
        if not isinstance(observation, Observation): raise ValueError('typed-observation-required')
        if type(observation.sequence) is not int or observation.sequence < 0:
            raise ValueError('invalid-sequence')
        if observation.sequence <= self.sequence: return self.view
        if self.view.phase in ('lost', 'ended', 'closed'): return self.view
        if not self._matches(observation):
            self.sequence = observation.sequence
            self.view = View('lost')
            return self.view
        elapsed = seconds(observation.elapsed)
        if elapsed > self.timeline.duration + 2 or type(observation.paused) is not bool or type(observation.ended) is not bool:
            raise ValueError('invalid-player-observation')
        self.sequence = observation.sequence
        if observation.ended or elapsed >= self.timeline.duration:
            self.view = View('ended', elapsed=min(elapsed, self.timeline.duration))
        else:
            chapter = self.timeline.chapter_at(elapsed, observation.edition)
            self.view = View('opening' if chapter is None else 'story', chapter, elapsed, observation.paused)
        return self.view

    def seek(self, chapter):
        if self.view.phase not in ('opening', 'story'): raise ValueError('not-owned-active-playback')
        proposal = self.timeline.seek_proposal(chapter, self.timeline.identity)
        return Intent('seek', self.session, self.media, self.timeline.identity, self.sequence, proposal['start'])

    def current(self, intent, observation):
        """Final adapter-side check; an intent is not an executable command."""
        if not isinstance(intent, Intent) or not isinstance(observation, Observation): return False
        if self.view.phase not in ('opening', 'story') or not self._matches(observation): return False
        if observation.ended is not False or type(observation.sequence) is not int: return False
        return (intent.kind == 'seek' and intent.session == self.session and intent.media == self.media
            and intent.edition == self.timeline.identity and intent.sequence == self.sequence
            and observation.sequence == self.sequence and intent.start in tuple(row.start for row in self.timeline.chapters))

    def close(self, observation):
        """One stop proposal on exit, only with a fresh matching observation.

        Closing after foreign playback/repeated exit/completion returns no stop.
        The adapter must recheck the returned session/media immediately at use.
        """
        if self.view.phase == 'closed': return None
        self.observe(observation)
        intent = None
        if (self.view.phase in ('opening', 'story') and self._matches(observation)
                and observation.sequence == self.sequence):
            intent = Intent('stop', self.session, self.media, self.timeline.identity, self.sequence)
        self.view = View('closed')
        return intent
