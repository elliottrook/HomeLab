import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "custom_components" /
                       "aster_room_bridge"))
from contract import RoomContract, observation


class RoomContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = RoomContract(
            "media_player.family_room_tv", "media_player.tx_rz30",
            frozenset({
                "equipment.power_on", "equipment.power_off",
                "equipment.volume_up", "equipment.volume_down",
                "equipment.mute_on", "equipment.mute_off",
            }),
        )

    def test_actions_map_only_to_fixed_entities_and_media_player_services(self):
        expected = {
            "equipment.power_on": ("turn_on", "media_player.family_room_tv"),
            "equipment.power_off": ("turn_off", "media_player.family_room_tv"),
            "equipment.volume_up": ("volume_up", "media_player.tx_rz30"),
            "equipment.volume_down": ("volume_down", "media_player.tx_rz30"),
            "equipment.mute_on": ("volume_mute", "media_player.tx_rz30"),
            "equipment.mute_off": ("volume_mute", "media_player.tx_rz30"),
        }
        for action, (service, entity) in expected.items():
            call = self.contract.service_call(action)
            self.assertEqual((call.domain, call.service), ("media_player", service))
            self.assertEqual(call.data["entity_id"], entity)
        self.assertTrue(self.contract.service_call("equipment.mute_on").data["is_volume_muted"])
        self.assertFalse(self.contract.service_call("equipment.mute_off").data["is_volume_muted"])

    def test_unknown_or_ungranted_actions_fail_closed(self):
        limited = RoomContract("media_player.family_room_tv", "media_player.tx_rz30",
                               frozenset({"equipment.power_on"}))
        with self.assertRaises(ValueError): limited.service_call("equipment.volume_up")
        with self.assertRaises(ValueError): limited.service_call("home.call_service")
        with self.assertRaises(ValueError):
            RoomContract("switch.bad", "media_player.tx_rz30",
                         frozenset({"equipment.power_on"}))

    def test_observation_is_bounded_and_type_checked(self):
        self.assertEqual(observation("on", {"volume_level": 0.59,
                                            "is_volume_muted": False}),
                         {"power": "on", "volume_level": 0.59, "muted": False})
        self.assertEqual(observation("playing", {"volume_level": 4,
                                                 "is_volume_muted": "no"}),
                         {"power": "unavailable", "volume_level": None,
                          "muted": None})


if __name__ == "__main__":
    unittest.main()
