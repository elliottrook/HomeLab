"""Offline queue proposals, not a Kodi transport or playback implementation.

Keep this outside the read-only pilot bundle. An eventual write adapter must
re-read the live queue and require approval before replacing playback. Queue
duplicates are intentional: never deduplicate a user's existing playlist.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import random

from music_policy import shuffle_candidates


def identities(values, *, allow_empty=True):
    if not isinstance(values, (list, tuple)) or (not allow_empty and not values):
        raise ValueError('Song identities required')
    if any(type(value) is not int or value < 1 for value in values):
        raise ValueError('Invalid song identity')
    if len(values) > 100000:
        raise ValueError('Queue exceeds planning limit')
    return tuple(values)


@dataclass(frozen=True)
class QueueSnapshot:
    song_ids: tuple
    current_index: int | None

    def __post_init__(self):
        object.__setattr__(self, 'song_ids', identities(self.song_ids))
        if self.current_index is not None and (
                type(self.current_index) is not int or
                not 0 <= self.current_index < len(self.song_ids)):
            raise ValueError('Invalid current position')

    @property
    def fingerprint(self):
        return hashlib.sha256(json.dumps(
            [self.song_ids, self.current_index], separators=(',', ':')
        ).encode()).hexdigest()


@dataclass(frozen=True)
class QueueProposal:
    action: str
    song_ids: tuple
    current_index: int | None
    expected_queue: str
    replaces_queue: bool

    def matches(self, snapshot):
        """Optimistic stale-preview guard only; not a transaction or write grant."""
        return isinstance(snapshot, QueueSnapshot) and snapshot.fingerprint == self.expected_queue


def propose(snapshot, selected_ids, *, action):
    """Preserve current playback for append/play-next; replace is explicit.

    selected_ids must already be in the desired order. Alphabetical catalogue
    order is NOT album track order. No library paths or credentials accepted.
    No function in this module starts, stops, clears or changes a Kodi queue.
    """
    if not isinstance(snapshot, QueueSnapshot):
        raise ValueError('Verified queue snapshot required')
    selected = identities(selected_ids, allow_empty=False)
    if action == 'append':
        result = snapshot.song_ids + selected
        current = snapshot.current_index
    elif action == 'next':
        if snapshot.current_index is None:
            raise ValueError('Play next requires an identified current item')
        split = snapshot.current_index + 1
        result = snapshot.song_ids[:split] + selected + snapshot.song_ids[split:]
        current = snapshot.current_index
    elif action == 'replace':
        result, current = selected, None  # Does not request automatic playback.
    else:
        raise ValueError('Unknown queue action')
    return QueueProposal(action, identities(result), current, snapshot.fingerprint,
                         action == 'replace')


def nonholiday_shuffle(songs, albums, *, expected_total, seed):
    """Deterministic preview over the complete eligible library, not one UI page."""
    if type(seed) is not int:
        raise ValueError('Explicit integer preview seed required')
    summary = shuffle_candidates(songs, albums, expected_total=expected_total)
    selected = sorted(summary['eligible_ids'])
    random.Random(seed).shuffle(selected)
    return tuple(selected)
