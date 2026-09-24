import hashlib
import io
import tarfile
import tempfile
import unittest
from pathlib import Path
from export_service import ALLOWED, build


class ExportTests(unittest.TestCase):
    def test_exact_scope_and_tamper_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hashes = {}
            for name in ALLOWED:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'synthetic service definition')
                hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
            (root/'db.sqlite3').write_bytes(b'SECRET DOCUMENT DATA')
            (root/'llama-api-key').write_bytes(b'SECRET TOKEN')
            output = io.BytesIO()
            build(root, hashes, output)
            with tarfile.open(fileobj=io.BytesIO(output.getvalue())) as archive:
                names = set(archive.getnames())
                self.assertEqual(names, {'paperless-service/' + n for n in ALLOWED | {'MANIFEST.json'}})
                for member in archive:
                    contents = archive.extractfile(member).read()
                    self.assertNotIn(b'SECRET DOCUMENT DATA', contents)
                    self.assertNotIn(b'SECRET TOKEN', contents)
            (root/'pipeline.py').write_bytes(b'SECRET DOCUMENT DATA')
            with self.assertRaisesRegex(ValueError, 'release_file_changed'):
                build(root, hashes, io.BytesIO())

    def test_expanded_manifest_refused(self):
        with self.assertRaises(ValueError):
            build('/unused', {'db.sqlite3': 'anything'}, io.BytesIO())


if __name__ == '__main__':
    unittest.main()
