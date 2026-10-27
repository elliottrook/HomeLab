from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1]))

from epub_narration.catalog import fingerprint, read_epub_sources


class CatalogueTests(unittest.TestCase):
    def make_catalogue(self, root: Path, relative: str = "Synthetic/Book") -> Path:
        database = root / "metadata.db"
        with closing(sqlite3.connect(database)) as connection, connection:
            connection.executescript(
                "CREATE TABLE books (id INTEGER PRIMARY KEY, path TEXT NOT NULL);"
                "CREATE TABLE data (id INTEGER PRIMARY KEY, book INTEGER, format TEXT, name TEXT);"
            )
            connection.execute("INSERT INTO books VALUES (1, ?)", (relative,))
            connection.execute("INSERT INTO data VALUES (1, 1, 'EPUB', 'fixture')")
        return database

    def test_discovers_and_hashes_epub_without_modifying_catalogue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            book = root / "Synthetic" / "Book"
            book.mkdir(parents=True)
            (book / "fixture.epub").write_bytes(b"synthetic epub")
            database = self.make_catalogue(root)
            before = database.read_bytes()

            sources = read_epub_sources(database, root)
            result = fingerprint(sources[0])

            self.assertEqual(1, len(sources))
            self.assertEqual(1, result.calibre_id)
            self.assertEqual(len(b"synthetic epub"), result.size)
            self.assertEqual(before, database.read_bytes())

    def test_read_only_database_fails_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(FileNotFoundError):
                read_epub_sources(root / "missing.db", root)
            self.assertFalse((root / "missing.db").exists())

    def test_rejects_source_path_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = parent / "library"
            root.mkdir()
            outside = parent / "outside"
            outside.mkdir()
            (outside / "fixture.epub").write_bytes(b"private synthetic bytes")
            database = self.make_catalogue(root, "../outside")
            with self.assertRaisesRegex(ValueError, "calibre-epub-path"):
                read_epub_sources(database, root)


if __name__ == "__main__":
    unittest.main()

