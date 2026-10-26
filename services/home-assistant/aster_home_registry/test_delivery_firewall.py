import copy
import unittest
import xml.etree.ElementTree as ET
import delivery_firewall as fw

class RuleTests(unittest.TestCase):
    def root(self):
        root=ET.Element('config');ET.SubElement(root,'unrelated').text='preserve'
        rules=ET.SubElement(root,'rules');n=ET.SubElement(rules,'rule',uuid=fw.REFERENCE)
        for key,value in dict(interface='opt3',source_net='192.168.20.11',sequence='1787').items():ET.SubElement(n,key).text=value
        return root
    def test_exact_rule_and_no_other_config_changes(self):
        root=self.root();before=ET.tostring(root)
        self.assertTrue(fw.change(root,'apply'));n=root.find('.//rule[@uuid="'+fw.RULE_ID+'"]')
        for key,value in fw.VALUES.items():self.assertEqual(n.findtext(key),value)
        self.assertTrue(fw.change(root,'rollback'));self.assertEqual(ET.tostring(root),before)
    def test_idempotent_and_drift_refuses(self):
        root=self.root();fw.change(root,'apply');self.assertFalse(fw.change(root,'apply'))
        root.find('.//rule[@uuid="'+fw.RULE_ID+'"]/destination_port').text='any'
        with self.assertRaisesRegex(ValueError,'drift'):fw.change(root,'rollback')
    def test_no_sequence_collision(self):
        root=self.root();ET.SubElement(ET.SubElement(root,'rule'),'sequence').text='1850'
        with self.assertRaisesRegex(ValueError,'sequence-used'):fw.change(root,'apply')

if __name__=='__main__':unittest.main()
