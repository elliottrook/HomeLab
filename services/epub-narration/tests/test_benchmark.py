from pathlib import Path
from contextlib import closing
import json
import sqlite3
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).parents[1]))

from epub_narration.benchmark import create_private_plan


CONTAINER = """<container xmlns='urn:oasis:names:tc:opendocument:xmlns:container'>
<rootfiles><rootfile full-path='OEBPS/content.opf'/></rootfiles></container>"""
PACKAGE = """<package xmlns='http://www.idpf.org/2007/opf'><manifest>
<item id='chapter' href='chapter.xhtml' media-type='application/xhtml+xml'/>
</manifest><spine><itemref idref='chapter'/></spine></package>"""


def fixture_epub(path: Path, words: int) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mimetype", "application/epub+zip")
        archive.writestr("META-INF/container.xml", CONTAINER)
        archive.writestr("OEBPS/content.opf", PACKAGE)
        text = " ".join(f"fixture{index}" for index in range(words))
        archive.writestr("OEBPS/chapter.xhtml", f"<html><body><p>{text}</p></body></html>")


class BenchmarkPlanTests(unittest.TestCase):
    def test_selects_deterministic_quantiles_and_keeps_private_plan_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "library"
            root.mkdir()
            database = root / "metadata.db"
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.executescript(
                    "CREATE TABLE books (id INTEGER PRIMARY KEY, path TEXT NOT NULL);"
                    "CREATE TABLE data (id INTEGER PRIMARY KEY, book INTEGER, format TEXT, name TEXT);"
                )
                for book_id in range(1, 26):
                    relative = f"synthetic/{book_id}"
                    directory = root / relative
                    directory.mkdir(parents=True)
                    fixture_epub(directory / "fixture.epub", 100 + book_id * 10)
                    connection.execute("INSERT INTO books VALUES (?,?)", (book_id, relative))
                    connection.execute(
                        "INSERT INTO data VALUES (?,?,?,?)", (book_id, book_id, "EPUB", "fixture")
                    )
            output = Path(tmp) / "private" / "plan.json"
            summary = create_private_plan(database, root, output, sample_count=20, sample_words=100)
            plan = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(20, summary["sample_count"])
            self.assertEqual(20, len(plan["samples"]))
            self.assertEqual(list(range(1, 21)), [item["slot"] for item in plan["samples"]])
            self.assertEqual(0o600, output.stat().st_mode & 0o777)
            self.assertEqual(0o700, output.parent.stat().st_mode & 0o777)

    def test_refuses_too_few_eligible_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database = root / "metadata.db"
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.executescript(
                    "CREATE TABLE books (id INTEGER PRIMARY KEY, path TEXT NOT NULL);"
                    "CREATE TABLE data (id INTEGER PRIMARY KEY, book INTEGER, format TEXT, name TEXT);"
                )
            with self.assertRaisesRegex(ValueError, "benchmark-sample-count"):
                create_private_plan(database, root, root / "private" / "plan.json")


if __name__ == "__main__":
    unittest.main()
