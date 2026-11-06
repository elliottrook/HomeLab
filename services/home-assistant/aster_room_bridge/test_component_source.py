import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).parent / "custom_components" / "aster_room_bridge"
SOURCE = (ROOT / "__init__.py").read_text()


class ComponentSourceTests(unittest.TestCase):
    def test_component_parses_and_is_outbound_only(self):
        ast.parse(SOURCE)
        self.assertIn('self.url + "/poll"', SOURCE)
        self.assertIn('self.url + "/ack"', SOURCE)
        self.assertNotIn("HomeAssistantView", SOURCE)
        self.assertNotIn("async_register", SOURCE)

    def test_key_is_file_bound_and_never_logged(self):
        self.assertIn("details.st_mode & 0o077", SOURCE)
        self.assertIn('"Authorization": "Bearer " + self.key', SOURCE)
        self.assertNotIn("_LOGGER", SOURCE)
        self.assertNotIn("print(", SOURCE)

    def test_gateway_cannot_supply_service_or_entity(self):
        self.assertIn("self.contract.service_call(action)", SOURCE)
        self.assertIn("call.domain, call.service, call.data", SOURCE)
        self.assertNotIn('command.get("entity', SOURCE)
        self.assertNotIn('command.get("service', SOURCE)

    def test_content_state_is_outbound_polled_and_volatile_only(self):
        self.assertIn('self.url + "/content"', SOURCE)
        self.assertIn("PlaybackObservation.parse", SOURCE)
        self.assertIn('"content_states", {}', SOURCE)
        self.assertIn(')[self.room_id] = state', SOURCE)
        self.assertNotIn("async_fire", SOURCE)
        self.assertNotIn("recorder", SOURCE.casefold())

    def test_content_failure_cannot_take_down_accepted_equipment_controls(self):
        self.assertIn("response.status in {404, 405}", SOURCE)
        self.assertIn("self.content_supported = False", SOURCE)
        content = SOURCE.index("await self._content()")
        equipment = SOURCE.index('self.url + "/poll"', content)
        isolation = SOURCE[content:equipment]
        self.assertIn("except Exception", isolation)

    def test_multi_room_config_is_backward_compatible_and_unique(self):
        self.assertIn('vol.Required("rooms")', SOURCE)
        self.assertIn('domain_config.get("rooms", [domain_config])', SOURCE)
        self.assertIn('len(room_ids) != len(set(room_ids))', SOURCE)
        self.assertIn('"aster-room-bridge-" + bridge.room_id', SOURCE)
        self.assertIn('"bridges": {bridge.room_id: bridge for bridge in bridges}', SOURCE)
        self.assertIn('if len(bridges) == 1', SOURCE)


if __name__ == "__main__":
    unittest.main()
