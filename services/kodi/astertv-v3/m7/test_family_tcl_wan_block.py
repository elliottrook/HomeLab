import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET


MODULE_PATH = Path(__file__).with_name("apply_family_tcl_wan_block.py")
SPEC = importlib.util.spec_from_file_location("apply_family_tcl_wan_block", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FamilyTclWanBlockTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.config = root / "config.xml"
        self.checkpoint = root / "checkpoint.xml"
        self.proof = root / "proof.json"
        self.before = b"""<opnsense><filter><rules>
<rule uuid="dd2386fe-4bc3-4656-95dd-f784cb4f825a">
<enabled>1</enabled><sequence>1000</sequence><action>pass</action>
<interface>opt2</interface><direction>in</direction><ipprotocol>inet</ipprotocol>
<protocol>any</protocol><source_net>opt2</source_net><source_not>0</source_not>
<destination_net>any</destination_net><destination_not>0</destination_not>
<description>Allow IoT internet</description>
</rule></rules></filter></opnsense>"""
        self.config.write_bytes(self.before)
        MODULE.CONFIG = self.config
        MODULE.CHECKPOINT = self.checkpoint
        MODULE.PROOF = self.proof
        MODULE.EXPECTED = hashlib.sha256(self.before).hexdigest()

    def tearDown(self):
        self.temp.cleanup()

    def test_apply_and_exact_rollback(self):
        MODULE.apply()
        rules = list(ET.parse(self.config).getroot().iter("rule"))
        self.assertEqual([rule.findtext("sequence") for rule in rules], ["950", "1000"])
        added = rules[0]
        self.assertEqual(added.findtext("source_net"), "192.168.30.162")
        self.assertEqual(added.findtext("action"), "block")
        self.assertEqual(added.findtext("destination_net"), "any")
        MODULE.rollback()
        self.assertEqual(self.config.read_bytes(), self.before)

    def test_predecessor_drift_fails_closed(self):
        self.config.write_bytes(self.before + b"\n")
        with self.assertRaisesRegex(RuntimeError, "predecessor"):
            MODULE.apply()


if __name__ == "__main__":
    unittest.main()
