import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("guest_provision", ROOT / "provision_guest.py")
guest = importlib.util.module_from_spec(spec); spec.loader.exec_module(guest)


class GuestPolicyTests(unittest.TestCase):
    def test_policy_allows_only_bounded_media_playback(self):
        current = {"AuthenticationProviderId": "fixture", "PasswordResetProviderId": "fixture"}
        policy = guest.build_policy(current, ["movie-id", "show-id"], device_enabled=False)
        self.assertTrue(policy["EnableMediaPlayback"])
        self.assertTrue(policy["EnableVideoPlaybackTranscoding"])
        self.assertTrue(policy["EnableAudioPlaybackTranscoding"])
        self.assertTrue(policy["EnablePlaybackRemuxing"])
        self.assertFalse(policy["IsAdministrator"])
        for denied in ("EnableContentDownloading", "EnableContentDeletion",
                       "EnableCollectionManagement", "EnableLiveTvAccess",
                       "EnableRemoteControlOfOtherUsers", "EnableSharedDeviceControl",
                       "EnableUserPreferenceAccess", "EnableMediaConversion"):
            self.assertFalse(policy[denied], denied)
        self.assertFalse(policy["EnableAllFolders"])
        self.assertEqual(policy["EnabledFolders"], ["movie-id", "show-id"])
        self.assertFalse(policy["EnableAllDevices"])
        self.assertEqual(policy["EnabledDevices"], [guest.DEVICE_ID])

    def test_exact_four_video_libraries_and_no_music(self):
        self.assertEqual(guest.LIBRARIES, {
            "Movies": "movies", "Shows": "tvshows",
            "Archive Movies": "movies", "Archive TV": "tvshows",
        })


if __name__ == "__main__":
    unittest.main()
