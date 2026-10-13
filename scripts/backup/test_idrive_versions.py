import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

spec=importlib.util.spec_from_file_location('versions',Path(__file__).with_name('idrive-version-maintenance.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class VersionProtection(unittest.TestCase):
    name='homelab-proxmox-guests/vzdump-lxc-100-2026_09_01-02_30_00.tar.zst'
    def entries(self):
        return [dict(Key='key',VersionId='old',kind='Version',IsLatest='false',Size='12'),
                dict(Key='key',VersionId='marker',kind='DeleteMarker',IsLatest='true')]
    def test_deleted_archive_only(self):
        self.assertEqual(len(m.candidates(self.entries(),{'key':self.name},set())),1)
    def test_local_retained_archive_blocks(self):
        with self.assertRaises(AssertionError):
            m.candidates(self.entries(),{'key':self.name},{self.name.split('/')[-1]})
    def test_current_version_is_never_selected(self):
        v=self.entries()[:1];v[0]['IsLatest']='true'
        self.assertEqual(m.candidates(v,{'key':self.name},set()),[])
    def test_non_archive_blocks(self):
        with self.assertRaises(AssertionError):
            m.candidates(self.entries(),{'key':'homelab-proxmox-guests/important.txt'},set())
    def test_rules_never_expire_current_archives_by_age(self):
        names=['homelab-proxmox-guests','gowest','configuration','home-assistant','mac','jellyfin','paperless-service','service-reconstruction']
        root=ET.fromstring(m.lifecycle({n:'encoded-'+n for n in names}))
        self.assertEqual(len(root),9)
        self.assertFalse(any(m.tag(e) in ('Days','Date') for e in root.iter()))
        days=[int(e.text) for e in root.iter() if m.tag(e)=='NoncurrentDays']
        self.assertEqual(days,[1,30,14,14,14,14,14,14])

if __name__=='__main__':unittest.main()
