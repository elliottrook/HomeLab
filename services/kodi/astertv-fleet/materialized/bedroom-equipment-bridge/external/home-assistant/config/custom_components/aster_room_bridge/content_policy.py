"""Content-free AsterTV playback state and room-volume policy contracts."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re


SCHEMA = "astertv-room-playback.v1"
CONTENT_CLASSES = frozenset({
    "Movie", "Television", "Music", "YouTube", "Podcast", "News",
    "Book/Audiobook", "Unknown",
})
PLAYBACK_STATES = frozenset({"playing", "paused", "idle"})
ROOM = re.compile(r"[a-z][a-z0-9-]{1,31}")
SESSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{7,127}")
PAGE = re.compile(r"[a-z][a-z0-9-]{1,63}")
PAYLOAD_KEYS = {
    "schema", "room_id", "session_id", "sequence", "observed_epoch",
    "expires_epoch", "available", "playback_state", "content_class",
    "page_id", "screensaver_active",
}


class ContentPolicyError(ValueError):
    pass


@dataclass(frozen=True)
class PlaybackObservation:
    room_id: str
    session_id: str
    sequence: int
    observed_epoch: int
    expires_epoch: int
    available: bool
    playback_state: str
    content_class: str
    page_id: str
    screensaver_active: bool

    @classmethod
    def parse(cls, value: object, *, now_epoch: int) -> "PlaybackObservation":
        if not isinstance(value, dict) or set(value) != PAYLOAD_KEYS:
            raise ContentPolicyError("playback-schema")
        if (value.get("schema") != SCHEMA
                or not isinstance(value.get("room_id"), str)
                or not ROOM.fullmatch(value["room_id"])
                or not isinstance(value.get("session_id"), str)
                or not SESSION.fullmatch(value["session_id"])
                or type(value.get("sequence")) is not int or value["sequence"] < 1
                or type(value.get("observed_epoch")) is not int
                or type(value.get("expires_epoch")) is not int
                or not value["observed_epoch"] <= now_epoch <= value["expires_epoch"]
                or value["expires_epoch"] - value["observed_epoch"] > 30
                or type(value.get("available")) is not bool
                or value.get("playback_state") not in PLAYBACK_STATES
                or value.get("content_class") not in CONTENT_CLASSES
                or not isinstance(value.get("page_id"), str)
                or not PAGE.fullmatch(value["page_id"])
                or type(value.get("screensaver_active")) is not bool):
            raise ContentPolicyError("playback-identity")
        return cls(
            room_id=value["room_id"], session_id=value["session_id"],
            sequence=value["sequence"], observed_epoch=value["observed_epoch"],
            expires_epoch=value["expires_epoch"], available=value["available"],
            playback_state=value["playback_state"],
            content_class=value["content_class"], page_id=value["page_id"],
            screensaver_active=value["screensaver_active"],
        )


class CurrentState:
    """Retain only the latest content-free observation for each room."""

    def __init__(self):
        self._rooms: dict[str, PlaybackObservation] = {}

    def accept(self, observation: PlaybackObservation) -> None:
        previous = self._rooms.get(observation.room_id)
        if previous is not None:
            if observation.session_id == previous.session_id:
                if observation.sequence <= previous.sequence:
                    raise ContentPolicyError("playback-replay")
            elif (observation.sequence != 1
                  or observation.observed_epoch < previous.observed_epoch):
                raise ContentPolicyError("playback-session-sequence")
        self._rooms[observation.room_id] = observation

    def get(self, room_id: str) -> PlaybackObservation | None:
        return self._rooms.get(room_id)


@dataclass(frozen=True)
class VolumeProfile:
    targets: dict[str, float]
    nighttime_ceiling: float
    maximum_step: float = 0.02

    def __post_init__(self):
        if (not self.targets or "Unknown" in self.targets
                or any(name not in CONTENT_CLASSES for name in self.targets)
                or any(type(level) not in {int, float} or not math.isfinite(level)
                       or not 0 <= level <= 1 for level in self.targets.values())
                or type(self.nighttime_ceiling) not in {int, float}
                or not math.isfinite(self.nighttime_ceiling)
                or not 0 <= self.nighttime_ceiling <= 1
                or type(self.maximum_step) not in {int, float}
                or not math.isfinite(self.maximum_step)
                or not 0 < self.maximum_step <= 0.05):
            raise ContentPolicyError("volume-profile")


@dataclass(frozen=True)
class VolumeDecision:
    reason: str
    target: float | None
    ramp: tuple[float, ...]


class VolumeSessionController:
    """Fail-closed state machine for one room's playback-session volume."""

    def __init__(self, profile: VolumeProfile):
        self.profile = profile
        self.previous: PlaybackObservation | None = None
        self.last_level: float | None = None
        self.manual_override = False

    def observe(self, current: PlaybackObservation, *, current_level: float,
                nighttime: bool) -> VolumeDecision:
        if (type(current_level) not in {int, float}
                or not math.isfinite(current_level)
                or not 0 <= current_level <= 1):
            raise ContentPolicyError("current-volume")
        previous = self.previous
        new_session = (previous is not None
                       and previous.session_id != current.session_id)
        if new_session:
            self.manual_override = False
        elif (previous is not None and self.last_level is not None
              and previous.playback_state in {"playing", "paused"}
              and abs(current_level - self.last_level) > 0.0011):
            self.manual_override = True

        # A controller restart while media is already playing must never alter
        # the room. It primes from observation and waits for the next real
        # playback start or class transition.
        if previous is None:
            self.previous = current
            self.last_level = current_level
            return VolumeDecision("startup-prime", None, ())

        decision = decide_volume(
            previous=previous, current=current, current_level=current_level,
            profile=self.profile, nighttime=nighttime,
            manual_override=self.manual_override,
        )
        self.previous = current
        self.last_level = current_level
        return decision

    def applied(self, level: float) -> None:
        if type(level) not in {int, float} or not 0 <= level <= 1:
            raise ContentPolicyError("applied-volume")
        self.last_level = float(level)

    def suppress(self, current: PlaybackObservation,
                 current_level: float | None = None) -> VolumeDecision:
        """Consume an observation when required control context is absent."""
        if (self.previous is not None
                and self.previous.session_id != current.session_id):
            self.manual_override = False
        self.previous = current
        if (type(current_level) in {int, float}
                and math.isfinite(current_level) and 0 <= current_level <= 1):
            self.last_level = float(current_level)
        return VolumeDecision("context-unavailable", None, ())


def _ramp(current: float, target: float, maximum_step: float) -> tuple[float, ...]:
    if abs(target - current) < 1e-9:
        return ()
    direction = 1 if target > current else -1
    values = []
    level = current
    while abs(target - level) > maximum_step:
        level = round(level + direction * maximum_step, 6)
        values.append(level)
    if not values or abs(values[-1] - target) > 1e-9:
        values.append(round(target, 6))
    return tuple(values)


def decide_volume(*, previous: PlaybackObservation | None,
                  current: PlaybackObservation, current_level: float,
                  profile: VolumeProfile, nighttime: bool,
                  manual_override: bool) -> VolumeDecision:
    if (type(current_level) not in {int, float} or not math.isfinite(current_level)
            or not 0 <= current_level <= 1):
        raise ContentPolicyError("current-volume")
    if not current.available:
        return VolumeDecision("unavailable", None, ())
    if current.playback_state != "playing":
        return VolumeDecision("not-playing", None, ())
    if current.content_class == "Unknown" or current.content_class not in profile.targets:
        return VolumeDecision("unknown-class", None, ())
    if manual_override:
        return VolumeDecision("manual-override", None, ())
    start = previous is None or previous.playback_state != "playing"
    changed = previous is not None and previous.content_class != current.content_class
    if not start and not changed:
        return VolumeDecision("no-transition", None, ())
    target = profile.targets[current.content_class]
    if nighttime:
        target = min(target, profile.nighttime_ceiling)
    return VolumeDecision("content-transition", target,
                          _ramp(current_level, target, profile.maximum_step))
