import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import build_network_settings as builder
import network_settings_install as install
from build_network_preview import build as network_build

RAW=b'<window><controls><control type="button" id="206"><onclick>RunAddon(script.logviewer)</onclick><enable>System.HasAddon(script.logviewer)</enable><label>Diagnostics</label></control><control id="200"><onclick>ActivateWindow(InterfaceSettings)</onclick></control></controls></window>'

class NetworkSettingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();self.storage=self.root/'storage';self.storage.mkdir()
        self.before=hashlib.sha256(RAW).hexdigest()
        for module in (builder,install):
            change=patch.object(module,'BEFORE',self.before);change.start();self.addCleanup(change.stop)
        target=self.storage/install.TARGET;target.parent.mkdir(parents=True);target.write_bytes(RAW)
        network=self.storage/'.aster-staging'/install.NETWORK;network.parent.mkdir()
        self.assertEqual(network_build(network),install.NETWORK_PIN)
        source=self.root/'source.xml';source.write_bytes(RAW)
        self.stage=self.root/'stage';self.pin=builder.build(self.stage,source)

    def run_mode(self,mode,idle=True):
        return install.run(mode,self.stage,self.storage,self.pin,idle=lambda:idle)

    def test_only_action_and_enable_change(self):
        original=ET.fromstring(RAW);changed=ET.fromstring(builder.patch_page(RAW))
        b=changed.find(".//control[@id='206']")
        self.assertIn(install.NETWORK_PIN,b.findtext('onclick'));self.assertTrue(b.findtext('onclick').endswith(',diagnostics)'))
        self.assertEqual(b.findtext('enable'),'!Player.HasMedia')
        b.find('onclick').text='RunAddon(script.logviewer)';b.find('enable').text='System.HasAddon(script.logviewer)'
        self.assertEqual(ET.tostring(original),ET.tostring(changed))
        with self.assertRaises(ValueError):builder.patch_page(RAW+b' ')

    def test_checkpoint_isolated_restore_rollback_reinstall(self):
        self.assertTrue(self.run_mode('install')['checkpoint_verified'])
        self.assertTrue(self.run_mode('verify')['active'])
        cp=self.storage/install.CHECKPOINT
        self.assertEqual((cp/'original.xml').read_bytes(),RAW)
        isolated=self.root/'isolated.xml';isolated.write_bytes((cp/'original.xml').read_bytes())
        self.assertEqual(hashlib.sha256(isolated.read_bytes()).hexdigest(),self.before)
        self.assertTrue(self.run_mode('rollback')['original_restored'])
        self.assertFalse(self.run_mode('verify')['active'])
        self.run_mode('install');self.assertTrue(self.run_mode('verify')['active'])
        self.assertEqual(list(install.accepted_overrides(self.stage,self.storage,self.pin)),[install.TARGET])

    def test_active_playback_unknown_drift_and_invalid_pin_are_fenced(self):
        with self.assertRaises(ValueError):self.run_mode('install',False)
        self.assertFalse((self.storage/install.CHECKPOINT).exists())
        with self.assertRaises(ValueError):install.inspect(self.stage,self.storage,'0'*64)
        self.run_mode('install');(self.storage/install.TARGET).write_bytes(b'unknown')
        with self.assertRaises(ValueError):self.run_mode('rollback')
        self.assertEqual((self.storage/install.TARGET).read_bytes(),b'unknown')

    def test_checkpoint_or_dependency_drift_is_fenced(self):
        self.run_mode('install');cp=self.storage/install.CHECKPOINT
        (cp/'original.xml').write_bytes(b'not the backup')
        with self.assertRaises(ValueError):self.run_mode('rollback')
        dependency=self.storage/'.aster-staging'/install.NETWORK/'default.py'
        dependency.write_bytes(dependency.read_bytes()+b'\n')
        with self.assertRaises(ValueError):self.run_mode('verify')

    def test_payload_links_and_helper_drift_are_fenced(self):
        path=self.stage/'payload'/install.TARGET;raw=path.read_bytes();path.unlink()
        other=self.root/'other.xml';other.write_bytes(raw);path.symlink_to(other)
        with self.assertRaises(ValueError):self.run_mode('install')
        path.unlink();path.write_bytes(raw)
        helper=self.stage/'network_settings_install.py';helper.write_bytes(helper.read_bytes()+b'\n')
        with self.assertRaises(ValueError):self.run_mode('install')
