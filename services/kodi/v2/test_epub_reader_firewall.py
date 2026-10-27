import copy,unittest,xml.etree.ElementTree as ET
from epub_reader_firewall import RULE_ID,VALUES,change

class FirewallTests(unittest.TestCase):
 def root(self):
  root=ET.fromstring('<OPNsense><filter><rules><rule uuid="d8c1a44e-e726-4442-99e2-2093f209799e"><enabled>1</enabled><sequence>3092</sequence><action>pass</action><interface>lan</interface><direction>in</direction><ipprotocol>inet</ipprotocol><protocol>TCP</protocol><source_net>192.168.1.140</source_net><source_not>0</source_not><destination_net>192.168.50.23</destination_net><destination_not>0</destination_not><destination_port>443</destination_port><description>reference</description></rule></rules></filter></OPNsense>')
  return root
 def test_exact_add_verify_rollback(self):
  root=self.root();before=ET.tostring(root);self.assertTrue(change(root,'apply'));self.assertFalse(change(root,'verify'))
  rule=next(x for x in root.iter('rule') if x.get('uuid')==RULE_ID)
  self.assertTrue(all(rule.findtext(k)==v for k,v in VALUES.items()))
  self.assertTrue(change(root,'rollback'));self.assertEqual(ET.tostring(root),before)
 def test_refuses_sequence_and_drift(self):
  root=self.root();root.find('.//sequence').text='3095'
  with self.assertRaises(ValueError):change(root,'apply')
  root=self.root();change(root,'apply');next(x for x in root.iter('rule') if x.get('uuid')==RULE_ID).find('destination_port').text='111'
  with self.assertRaises(ValueError):change(root,'verify')
if __name__=='__main__':unittest.main()
