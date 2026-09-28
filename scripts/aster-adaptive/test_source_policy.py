import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import source_policy
from offline_baseline import FixtureAdapter, load_slice
from compare_tool_loop import aster_chat


class SourcePinTests(unittest.TestCase):
    def test_expected_and_observed_provenance_agree(self):
        adapter=FixtureAdapter()
        self.assertEqual(adapter.source_digest,adapter.source_provenance['expected_digest'])
        self.assertEqual(adapter.source_digest,adapter.source_provenance['observed_digest'])
        self.assertTrue(adapter.source_provenance['definition_digest'].startswith('sha256:'))

    def test_changed_source_denied_before_parse_or_compile(self):
        source=Mock()
        source.read_bytes.return_value=b'TOOLS = dangerous_call()\n'
        with patch.object(source_policy,'SOURCE',source), patch('ast.parse',side_effect=AssertionError('must not parse')):
            with self.assertRaisesRegex(ValueError,'reviewed definition'):
                load_slice()
            with self.assertRaisesRegex(ValueError,'reviewed definition'):
                aster_chat()

    def test_even_nonexecuting_source_drift_requires_revision(self):
        source=Mock()
        source.read_bytes.return_value=source_policy.SOURCE.read_bytes()+b'\n# changed source\n'
        with patch.object(source_policy,'SOURCE',source):
            with self.assertRaises(ValueError):
                FixtureAdapter()

    def test_compile_uses_same_single_read_that_was_verified(self):
        source=Mock()
        source.read_bytes.side_effect=[source_policy.SOURCE.read_bytes(),AssertionError('second read')]
        with patch.object(source_policy,'SOURCE',source):
            namespace,_,_=load_slice()
        self.assertIn('build_payload',namespace)
        self.assertEqual(1,source.read_bytes.call_count)

    def test_missing_or_invalid_definition_denied(self):
        original=json.loads(source_policy.DEFINITION.read_text())
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'definition.json'
            with patch.object(source_policy,'DEFINITION',path):
                with self.assertRaises(FileNotFoundError):
                    FixtureAdapter()
                for change in ({'expected_digest':'bad'},{'source':'/tmp/other.py'},
                               {'schema_version':'future.v2'},{'allow_drift':True}):
                    path.write_text(json.dumps(original | change))
                    with self.assertRaises(ValueError):
                        FixtureAdapter()

    def test_wrong_expected_pin_has_no_auto_update(self):
        original=json.loads(source_policy.DEFINITION.read_text())
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'definition.json'
            path.write_text(json.dumps(original | {'expected_digest':'sha256:'+'0'*64}))
            before=path.read_bytes()
            with patch.object(source_policy,'DEFINITION',path):
                with self.assertRaises(ValueError):
                    FixtureAdapter()
            self.assertEqual(before,path.read_bytes())
