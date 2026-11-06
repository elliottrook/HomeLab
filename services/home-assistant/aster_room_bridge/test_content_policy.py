from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent / "custom_components" / "aster_room_bridge"
sys.path.insert(0, str(HERE))
from content_policy import (ContentPolicyError, CurrentState, PlaybackObservation,
                            VolumeProfile, decide_volume)


def payload(**updates):
    value = {
        "schema": "astertv-room-playback.v1",
        "room_id": "family",
        "session_id": "session-0001",
        "sequence": 1,
        "observed_epoch": 100,
        "expires_epoch": 125,
        "available": True,
        "playback_state": "playing",
        "content_class": "Movie",
        "page_id": "movie-details",
        "screensaver_active": False,
    }
    value.update(updates)
    return value


class ContentPolicyTests(unittest.TestCase):
    def setUp(self):
        self.profile = VolumeProfile(
            targets={"Movie": 0.60, "Television": 0.55, "Music": 0.45,
                     "YouTube": 0.44, "Podcast": 0.35, "News": 0.35,
                     "Book/Audiobook": 0.30},
            nighttime_ceiling=0.40,
            maximum_step=0.02,
        )

    def observation(self, **updates):
        return PlaybackObservation.parse(payload(**updates), now_epoch=110)

    def test_schema_rejects_titles_history_and_stale_state(self):
        value = payload(title="private")
        with self.assertRaisesRegex(ContentPolicyError, "playback-schema"):
            PlaybackObservation.parse(value, now_epoch=110)
        with self.assertRaisesRegex(ContentPolicyError, "playback-identity"):
            PlaybackObservation.parse(payload(expires_epoch=109), now_epoch=110)

    def test_all_coarse_classes_are_accepted_but_unknown_never_changes_volume(self):
        for name in ("Movie", "Television", "Music", "YouTube", "Podcast",
                     "News", "Book/Audiobook", "Unknown"):
            observation = self.observation(content_class=name)
            self.assertEqual(observation.content_class, name)
        decision = decide_volume(previous=None, current=self.observation(content_class="Unknown"),
                                 current_level=0.5, profile=self.profile,
                                 nighttime=False, manual_override=False)
        self.assertEqual((decision.reason, decision.ramp), ("unknown-class", ()))

    def test_current_state_rejects_replay_and_keeps_only_latest(self):
        state = CurrentState()
        one = self.observation()
        state.accept(one)
        two = self.observation(sequence=2)
        state.accept(two)
        self.assertIs(state.get("family"), two)
        with self.assertRaisesRegex(ContentPolicyError, "playback-replay"):
            state.accept(one)
        replayed_session = self.observation(session_id="session-0002", sequence=2)
        with self.assertRaisesRegex(ContentPolicyError, "playback-session-sequence"):
            state.accept(replayed_session)
        restarted = self.observation(session_id="session-0002", sequence=1)
        state.accept(restarted)
        self.assertIs(state.get("family"), restarted)

    def test_volume_runs_only_on_start_or_class_transition(self):
        current = self.observation()
        started = decide_volume(previous=None, current=current, current_level=0.5,
                                profile=self.profile, nighttime=False,
                                manual_override=False)
        self.assertEqual(started.target, 0.60)
        self.assertTrue(started.ramp)
        self.assertTrue(all(abs(b - a) <= 0.020001
                            for a, b in zip((0.5,) + started.ramp, started.ramp)))
        same = self.observation(sequence=2)
        unchanged = decide_volume(previous=current, current=same, current_level=0.6,
                                  profile=self.profile, nighttime=False,
                                  manual_override=False)
        self.assertEqual(unchanged.reason, "no-transition")
        music = self.observation(sequence=3, content_class="Music", page_id="music")
        changed = decide_volume(previous=same, current=music, current_level=0.6,
                                profile=self.profile, nighttime=False,
                                manual_override=False)
        self.assertEqual((changed.reason, changed.target), ("content-transition", 0.45))

    def test_night_cap_manual_override_and_outage_fail_closed(self):
        current = self.observation()
        capped = decide_volume(previous=None, current=current, current_level=0.3,
                               profile=self.profile, nighttime=True,
                               manual_override=False)
        self.assertEqual(capped.target, 0.40)
        manual = decide_volume(previous=None, current=current, current_level=0.3,
                               profile=self.profile, nighttime=False,
                               manual_override=True)
        self.assertEqual((manual.reason, manual.ramp), ("manual-override", ()))
        unavailable = self.observation(available=False)
        denied = decide_volume(previous=None, current=unavailable, current_level=0.3,
                               profile=self.profile, nighttime=False,
                               manual_override=False)
        self.assertEqual((denied.reason, denied.ramp), ("unavailable", ()))

    def test_contract_cannot_change_kodi_volume_or_audio_route(self):
        fields = set(payload())
        self.assertNotIn("kodi_volume", fields)
        self.assertNotIn("audio_route", fields)
        self.assertNotIn("passthrough", fields)


if __name__ == "__main__":
    unittest.main()
