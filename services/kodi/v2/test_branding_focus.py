import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import build_branding_focus as builder


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode() + b'\n'


class BrandingFocusBuilderTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.previous = self.root / 'review9'
        self.output = self.root / 'review10'
        skin = builder.SKIN
        page = (b'<window><controls><control type="button" id="139">'
                b'<onclick>OldSearch</onclick></control></controls></window>')
        files = []
        for name in ('custom_1111_digest.xml', 'custom_1122_breaking.xml'):
            path = skin + '1080i/' + name
            target = self.previous / 'payload' / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(page)
            files.append(dict(path=path, sha256=digest(page)))
        integration_name = '.aster-checkpoints/aster-music-integration-20261024/active-manifest.json'
        integration = dict(files=[dict(path='1080i/' + Path(row['path']).name,
                                       sha256=row['sha256'], bytes=len(page))
                                  for row in files])
        integration_raw = encoded(integration)
        target = self.previous / 'payload' / integration_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(integration_raw)
        files.append(dict(path=integration_name, sha256=digest(integration_raw)))
        manifest = encoded(dict(files=files))
        (self.previous / 'manifest.json').write_bytes(manifest)
        self.predecessor = digest(manifest)

    def build(self):
        with patch.object(builder, 'PREVIOUS', self.predecessor):
            return builder.build(self.previous, self.output)

    def test_rewrites_only_header_search_and_reconciles_integration(self):
        pin = self.build()
        manifest = json.loads((self.output / 'manifest.json').read_text())
        self.assertEqual(pin, digest((self.output / 'manifest.json').read_bytes()))
        self.assertEqual(manifest['kind'], 'hp-review10')
        self.assertEqual(manifest['previous_manifest_sha256'], self.predecessor)
        members = {row['path']: row for row in manifest['files']}
        for name in ('custom_1111_digest.xml', 'custom_1122_breaking.xml'):
            path = builder.SKIN + '1080i/' + name
            raw = (self.output / 'payload' / path).read_bytes()
            root = ET.fromstring(raw)
            self.assertEqual(root.findtext('.//control[@id="139"]/onclick'),
                             'RunScript(special://skin/tools/header_search.py)')
            self.assertEqual(members[path]['before_sha256'],
                             digest((self.previous / 'payload' / path).read_bytes()))
        integration_name = '.aster-checkpoints/aster-music-integration-20261024/active-manifest.json'
        integration = json.loads((self.output / 'payload' / integration_name).read_text())
        for row in integration['files']:
            path = builder.SKIN + row['path']
            self.assertEqual(row['sha256'], members[path]['sha256'])
            self.assertEqual(row['bytes'], (self.output / 'payload' / path).stat().st_size)
        helper = builder.SKIN + 'tools/header_search.py'
        self.assertIsNone(members[helper]['before_sha256'])

    def test_refuses_unknown_predecessor_and_existing_output(self):
        with self.assertRaisesRegex(ValueError, 'predecessor'):
            builder.build(self.previous, self.output)
        self.build()
        with patch.object(builder, 'PREVIOUS', self.predecessor):
            with self.assertRaisesRegex(ValueError, 'immutable'):
                builder.build(self.previous, self.output)


if __name__ == '__main__':
    unittest.main()
