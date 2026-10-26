from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import stat
import types
import unittest
from unittest.mock import Mock,patch
import importlib.util

SPEC=importlib.util.spec_from_file_location('home_status_capture',Path(__file__).parent/'tools/capture_home_status.py')
capture=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(capture)

class CaptureTests(unittest.TestCase):
    def run_source(self,**changes):
        before=dict(st_dev=1,st_ino=2,st_size=100,st_mtime_ns=3,st_ctime_ns=4,st_mode=stat.S_IFREG|0o600,st_nlink=1,st_atime_ns=5)
        after=dict(before,st_atime_ns=6,**changes)
        row=dict(id='light.room',name='Room',kind='light',availability='available',state='on',token='secret',url='http://private')
        raw=json.dumps(dict(schema_version=4,snapshot_id='ha-home-dashboard-v4',observed_at='2026-10-26T05:00:00+00:00',entities=[row],raw_attributes='secret')).encode()
        fake=Mock();fake.is_symlink.return_value=False;fake.parent.is_symlink.return_value=False
        fake.stat.side_effect=[types.SimpleNamespace(**before),types.SimpleNamespace(**after)]
        fake.read_bytes.return_value=raw
        output=StringIO();ok=True
        with patch('pathlib.Path',return_value=fake),redirect_stdout(output):
            try:exec(compile(capture.SOURCE,'home-display-source','exec'),{})
            except SystemExit:ok=False
        return ok,output.getvalue()

    def test_own_read_atime_change_not_mistaken_for_source_mutation(self):
        ok,text=self.run_source();self.assertTrue(ok);self.assertEqual(len(json.loads(text)['entities']),1)

    def test_unknown_raw_fields_removed_before_transport(self):
        ok,text=self.run_source();self.assertTrue(ok)
        for banned in ('secret','token','url','raw_attributes','http'):self.assertNotIn(banned,text)

    def test_source_replacement_or_metadata_change_refused(self):
        for changes in (dict(st_ino=99),dict(st_mtime_ns=99),dict(st_mode=stat.S_IFREG|0o644),dict(st_nlink=2)):
            ok,text=self.run_source(**changes);self.assertFalse(ok);self.assertEqual(text,'')

if __name__=='__main__':unittest.main()
