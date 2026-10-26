import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import build_digest_read_news as builder
import digest_read_news_install as installer
from build_digest_reader import build as reader_bundle


def fixture():
    buttons=[]
    for identity,left,width,label,previous,nxt in ((310,550,210,'Daily Digest',139,311),
            (311,772,220,'Breaking News',310,301),(301,1004,150,'Refresh',311,139)):
        buttons.append('<control type="button" id="%s"><left>%s</left><width>%s</width>'
            '<label>%s</label><onleft>%s</onleft><onright>%s</onright><onup>%s</onup>'
            '<ondown>500</ondown><onclick>Original</onclick></control>' %
            (identity,left,width,label,previous,nxt,identity))
    return ('<window><controls><control type="group"><control type="image"><left>542</left>'
        '<width>620</width></control>'+''.join(buttons)+
        '<control type="image"><left>1003</left><width>152</width>'
        '<visible>Control.HasFocus(301)</visible></control>'
        '<control type="list" id="500"><onclick>Original story action</onclick></control>'
        '</control></controls></window>').encode()


class ReadingNewsTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name).resolve()
        self.storage=self.root/'storage'
        self.stage=self.storage/'.aster-staging/aster-digest-read-news1'
        self.original=fixture()
        before=hashlib.sha256(self.original).hexdigest()
        for module in (builder,installer):
            mock=patch.object(module,'BEFORE',before);mock.start();self.addCleanup(mock.stop)
        source=self.root/'original.xml';source.write_bytes(self.original)
        self.pin=builder.build(self.stage,source)
        self.target=self.storage/installer.TARGET
        self.target.parent.mkdir(parents=True);self.target.write_bytes(self.original)
        self.assertEqual(reader_bundle(self.storage/'.aster-staging'/installer.READER),installer.READER_PIN)

    def run_mode(self,mode,idle=lambda:True):
        return installer.run(mode,self.stage,self.storage,self.pin,idle=idle)

    def test_exact_install_verify_rollback_reinstall(self):
        self.assertTrue(self.run_mode('install')['installed'])
        self.assertTrue(self.run_mode('verify')['active'])
        self.assertEqual(set(installer.accepted_overrides(self.stage,self.storage,self.pin)),{installer.TARGET})
        self.assertTrue(self.run_mode('rollback')['original_restored'])
        self.assertEqual(self.target.read_bytes(),self.original)
        self.assertEqual(installer.accepted_overrides(self.stage,self.storage,self.pin),{})
        self.assertFalse(self.run_mode('verify')['active'])
        self.assertTrue(self.run_mode('install')['installed'])

    def test_semantically_only_the_rail_changes(self):
        raw=builder.patch_page(self.original)
        root=ET.fromstring(raw);group=root.find('./controls/control')
        self.assertIn('news)',group.find("control[@id='312']/onclick").text)
        self.assertEqual(group.find("control[@id='500']/onclick").text,'Original story action')
        group.remove(group.find("control[@id='312']"))
        group.remove(next(n for n in group.findall('control') if n.findtext('visible')=='Control.HasFocus(312)'))
        group.find("control[@id='311']/onright").text='301'
        group.find("control[@id='301']/left").text='1004'
        group.find("control[@id='301']/onleft").text='311'
        group.find("control[@type='image']/width").text='620'
        next(n for n in group.findall('control') if n.findtext('visible')=='Control.HasFocus(301)').find('left').text='1003'
        self.assertEqual(ET.tostring(root),ET.tostring(ET.fromstring(self.original)))

    def test_busy_or_unknown_predecessor_creates_no_checkpoint(self):
        with self.assertRaisesRegex(ValueError,'idle'):self.run_mode('install',lambda:False)
        self.assertFalse((self.storage/installer.CHECKPOINT).exists())
        self.target.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'predecessor'):self.run_mode('install')
        self.assertFalse((self.storage/installer.CHECKPOINT).exists())

    def test_stage_payload_reader_or_helper_drift_is_refused(self):
        paths=(self.stage/'payload'/installer.TARGET,self.stage/'digest_read_news_install.py',
               self.storage/'.aster-staging'/installer.READER/'default.py')
        for path in paths:
            original=path.read_bytes();path.write_bytes(original+b'\n')
            with self.assertRaisesRegex(ValueError,'drift'):self.run_mode('install')
            path.write_bytes(original)

    def test_external_pin_and_linked_target_refused(self):
        with self.assertRaisesRegex(ValueError,'pin'):
            installer.inspect(self.stage,self.storage,'0'*64)
        other=self.root/'other.xml';other.write_bytes(self.original)
        self.target.unlink();self.target.symlink_to(other)
        with self.assertRaisesRegex(ValueError,'linked'):self.run_mode('install')
        self.assertEqual(other.read_bytes(),self.original)

    def test_backup_or_installed_drift_never_overwritten(self):
        self.run_mode('install')
        backup=self.storage/installer.CHECKPOINT/'original.xml'
        backup.write_bytes(b'bad')
        current=self.target.read_bytes()
        with self.assertRaisesRegex(ValueError,'recovery-drift'):self.run_mode('rollback')
        self.assertEqual(self.target.read_bytes(),current)
        backup.write_bytes(self.original);self.target.write_bytes(b'unknown successor')
        with self.assertRaisesRegex(ValueError,'rollback-drift'):self.run_mode('rollback')
        self.assertEqual(self.target.read_bytes(),b'unknown successor')

    def test_prepared_state_requires_explicit_recovery(self):
        self.run_mode('install')
        state=self.storage/installer.CHECKPOINT/'state.json'
        state.write_text('{"state":"prepared"}')
        with self.assertRaisesRegex(ValueError,'recovery-required'):
            installer.accepted_overrides(self.stage,self.storage,self.pin)
        self.assertTrue(self.run_mode('rollback')['rolled_back'])
        self.assertEqual(self.target.read_bytes(),self.original)

    def test_unknown_state_refused_and_immutable_build(self):
        self.run_mode('install')
        (self.storage/installer.CHECKPOINT/'state.json').write_text('{"state":"unknown"}')
        with self.assertRaisesRegex(ValueError,'unknown-state'):self.run_mode('verify')
        with self.assertRaisesRegex(ValueError,'immutable'):builder.build(self.stage,self.root/'original.xml')
        with self.assertRaisesRegex(ValueError,'exact'):builder.patch_page(self.original+b'\n')


if __name__=='__main__':unittest.main()
