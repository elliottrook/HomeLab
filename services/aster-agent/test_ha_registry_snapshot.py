import unittest

from ha_registry_snapshot import AliasConfig, build_snapshot


CONFIG = AliasConfig(
    entity_aliases={"light.kitchen_ceiling": "kitchen lights", "switch.office_lamp": "office lamp"},
    room_aliases={"kitchen": "kitchen", "office": "office"},
    timer_aliases={"timer.pasta": "pasta"},
    media_aliases={"media_player.jellyfin": "jellyfin"},
)


class HomeAssistantRegistrySnapshotTests(unittest.TestCase):
    def test_exports_only_reviewed_aliases_with_live_backing_objects(self):
        snapshot = build_snapshot(
            snapshot_id="ha-fixture-1", config=CONFIG,
            entity_ids={"light.kitchen_ceiling", "switch.office_lamp", "timer.pasta",
                        "media_player.jellyfin", "lock.private_door"},
            area_ids={"kitchen", "office", "private_bedroom"},
            states={"light.kitchen_ceiling": "on", "switch.office_lamp": "unavailable",
                    "timer.pasta": "active", "media_player.jellyfin": "idle",
                    "lock.private_door": "locked"},
        )
        self.assertEqual(snapshot["entities"], ["kitchen lights"])
        self.assertEqual(snapshot["rooms"], ["kitchen", "office"])
        self.assertEqual(snapshot["timers"], ["pasta"])
        self.assertEqual(snapshot["media_providers"], ["jellyfin"])
        self.assertNotIn("private", repr(snapshot))

    def test_missing_and_unavailable_objects_fail_closed_from_output(self):
        snapshot = build_snapshot(snapshot_id="ha-fixture-2", config=CONFIG,
                                  entity_ids={"light.kitchen_ceiling"}, area_ids=set(),
                                  states={"light.kitchen_ceiling": "unknown"})
        self.assertEqual(snapshot["entities"], [])
        self.assertEqual(snapshot["rooms"], [])
        self.assertEqual(snapshot["timers"], [])
        self.assertEqual(snapshot["media_providers"], [])

    def test_unregistered_state_is_rejected(self):
        with self.assertRaises(ValueError):
            build_snapshot(snapshot_id="ha-fixture-3", config=CONFIG, entity_ids=set(), area_ids=set(),
                           states={"light.kitchen_ceiling": "on"})

    def test_alias_and_domain_validation_rejects_broad_or_duplicate_exports(self):
        with self.assertRaises(ValueError):
            AliasConfig({"lock.front_door": "front door"}, {}, {}, {}).validate()
        with self.assertRaises(ValueError):
            AliasConfig({"light.kitchen": "kitchen"}, {"kitchen": "kitchen"}, {}, {}).validate()


if __name__ == "__main__":
    unittest.main()
