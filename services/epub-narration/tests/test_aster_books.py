from pathlib import Path
import hashlib
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1]))

from epub_narration.aster_books import BetaSession, ProgressStore, load_ready_book
from epub_narration.publication import VOICE, publish_generation, sha256_file


def publish(root: Path, source_hash: str, texts=("First sentence. Second sentence.", "Another chapter. Final line.")):
    stage = root / ("stage-" + source_hash[:8])
    files = []
    for index, text in enumerate(texts, 1):
        stem = f"{index:04d}"
        first_end = text.index(".") + 1
        spans = ((0, first_end), (first_end + 1, len(text)))
        records = []
        for cue_index, (start, end) in enumerate(spans):
            records.append({
                "source_start": start,
                "source_end": end,
                "start_sample": cue_index * 24_000,
                "end_sample": (cue_index + 1) * 24_000,
                "spoken_sha256": hashlib.sha256(text[start:end].encode()).hexdigest(),
            })
        values = {
            "chapters/" + stem + ".opus": b"OggS synthetic opus " + stem.encode(),
            "timing/" + stem + ".json": json.dumps({
                "schema": 1,
                "timing_level": "sentence-sample-index",
                "sample_rate": 24_000,
                "total_samples": 48_000,
                "cleaned_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "cues": records,
            }, sort_keys=True, separators=(",", ":")).encode(),
            "content/" + stem + ".json": json.dumps({
                "schema": 1,
                "chapter": index,
                "text": text,
                "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            }, sort_keys=True, separators=(",", ":")).encode(),
        }
        for relative, payload in values.items():
            path = stage / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            files.append({"path": relative, "bytes": len(payload), "sha256": sha256_file(path)})
    manifest = {
        "schema": 1,
        "state": "ready-candidate",
        "contracts": {"compiler": "synthetic-v1", "parser": "synthetic-v1",
                      "cleanup": "synthetic-v1", "encoder": "synthetic-v1"},
        "book_id": 7,
        "source_sha256": source_hash,
        "voice": VOICE,
        "timing_level": "sentence-sample-index",
        "sample_rate": 24_000,
        "codec": {"name": "opus", "bitrate": 48_000, "channels": 1},
        "files": files,
    }
    (stage / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")))
    return publish_generation(stage, root)


class AsterBooksConsumerTests(unittest.TestCase):
    def test_ready_only_load_exact_sentence_highlight_and_probe(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            publish(root, "a" * 64)
            probed = []
            book = load_ready_book(root, 7, lambda path, rate, samples: probed.append((path.suffix, rate, samples)))
            self.assertEqual(2, len(book.chapters))
            self.assertEqual([(".opus", 24_000, 48_000)] * 2, probed)
            session = BetaSession(book, ProgressStore(root / "private-progress"))
            self.assertEqual((0, 15), session.highlight())
            session.seek(24_000)
            self.assertEqual((16, len(book.chapters[0].text)), session.highlight())
            self.assertTrue(session.play_pause())
            self.assertFalse(session.play_pause())

    def test_seek_chapter_change_and_private_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            publish(root, "b" * 64)
            book = load_ready_book(root, 7)
            store = ProgressStore(root / "private-progress")
            session = BetaSession(book, store)
            session.seek(12_345)
            session.select_chapter(2)
            session.seek(23_456)
            session.close()
            resumed = BetaSession(book, store)
            self.assertEqual((2, 23_456), (resumed.chapter, resumed.sample))
            files = list((root / "private-progress").iterdir())
            self.assertEqual(1, len(files))
            self.assertEqual(0o600, files[0].stat().st_mode & 0o777)
            self.assertNotIn("First sentence", files[0].read_text())
            self.assertRegex(files[0].name, r"^[0-9a-f]{64}\.json$")
            self.assertNotEqual("7.json", files[0].name)

    def test_pointer_and_content_tampering_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pointer = publish(root, "c" * 64)
            generation = root / json.loads(pointer.read_text())["generation"]
            content = generation / "content/0001.json"
            content.write_text(content.read_text().replace("First", "Other"))
            with self.assertRaisesRegex(ValueError, "manifest-file-integrity"):
                load_ready_book(root, 7)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pointer = publish(root, "d" * 64)
            value = json.loads(pointer.read_text())
            value["generation"] = "generations/7/../../work/private"
            pointer.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, "beta-generation-path"):
                load_ready_book(root, 7)

    def test_atomic_pointer_rollback_selects_last_known_good(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = publish(root, "e" * 64)
            before = first.read_bytes()
            publish(root, "f" * 64)
            self.assertEqual("f" * 64, load_ready_book(root, 7).source_sha256)
            os.replace(first, root / "ready/current.json")
            (root / "ready/7.json").write_bytes(before)
            self.assertEqual("e" * 64, load_ready_book(root, 7).source_sha256)


if __name__ == "__main__":
    unittest.main()
