"""Conservative policy for clearing an orphaned Aster Music recovery flag."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlaybackState:
    active_players: int
    audio_items: int
    video_items: int

    def is_idle_and_empty(self):
        return (
            self.active_players == 0
            and self.audio_items == 0
            and self.video_items == 0
        )


def may_clear_trial_recovery(flag, state, stable_samples, required_samples=3):
    return (
        flag == "required"
        and isinstance(state, PlaybackState)
        and state.is_idle_and_empty()
        and stable_samples >= required_samples
    )

