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


if __name__ == "__main__":
    unittest.main()
