import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET


MODULE_PATH = Path(__file__).with_name("allow_family_tcl_discovery.py")
SPEC = importlib.util.spec_from_file_location("allow_family_tcl_discovery", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AllowFamilyTclDiscoveryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.config = root / "config.xml"
        self.checkpoint = root / "checkpoint.xml"
        self.proof = root / "proof.json"
        self.before = b"""<opnsense><filter><rules>
<rule uuid="bfaf8ab8-9e66-43fe-8be0-f25a6ca13d47">
<enabled>1</enabled><sequence>950</sequence><action>block</action>
<interface>opt2</interface><direction>in</direction><ipprotocol>inet</ipprotocol>
<protocol>any</protocol><source_net>192.168.30.162</source_net><source_not>0</source_not>
<destination_net>any</destination_net><destination_not>0</destination_not>
<description>AsterTV M7 block Family TCL Internet egress</description>
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
        self.assertEqual([rule.findtext("sequence") for rule in rules], ["925", "926", "950"])
        self.assertEqual(rules[0].findtext("destination_port"), "5353")
        self.assertEqual(rules[1].findtext("destination_port"), "1900")
        self.assertEqual(rules[2].findtext("action"), "block")
        MODULE.rollback()
        self.assertEqual(self.config.read_bytes(), self.before)

    def test_block_drift_fails_closed(self):
        tree = ET.parse(self.config)
        tree.getroot().find("filter/rules/rule/source_net").text = "192.168.30.1"
        tree.write(self.config, encoding="utf-8")
        MODULE.EXPECTED = hashlib.sha256(self.config.read_bytes()).hexdigest()
        with self.assertRaisesRegex(RuntimeError, "block-rule-drift"):
            MODULE.apply()


if __name__ == "__main__":
    unittest.main()
