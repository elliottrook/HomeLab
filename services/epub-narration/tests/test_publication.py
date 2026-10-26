from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1]))

from epub_narration.publication import VOICE, publish_generation, sha256_file


def make_staging(root: Path, book_id: int, source_hash: str, payload: bytes, valid: bool = True) -> Path:
    staging = root / f"stage-{source_hash[:4]}"
    chapter = staging / "chapters" / "0001.opus"
    chapter.parent.mkdir(parents=True)
    chapter.write_bytes(payload)
    manifest = {
        "schema": 1,
        "state": "ready-candidate",
        "contracts": {
            "compiler": "synthetic-compiler-v1",
            "parser": "synthetic-parser-v1",
            "cleanup": "canonical-cleanup-v1",
            "encoder": "synthetic-opus-v1",
        },
        "book_id": book_id,
        "source_sha256": source_hash,
        "voice": VOICE,
        "timing_level": "sentence-sample-index",
        "sample_rate": 24000,
        "codec": {"name": "opus", "bitrate": 48000, "channels": 1},
        "files": [{
            "path": "chapters/0001.opus",
            "bytes": len(payload),
            "sha256": sha256_file(chapter) if valid else "0" * 64,
        }],
    }
    (staging / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return staging


class PublicationTests(unittest.TestCase):
    def test_publishes_immutable_generation_and_ready_pointer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "output"
            staging = make_staging(root, 12, "a" * 64, b"synthetic opus bytes")
            pointer = publish_generation(staging, output)
            record = json.loads(pointer.read_text(encoding="utf-8"))
            self.assertEqual("generations/12/" + "a" * 64, record["generation"])
            self.assertFalse(staging.exists())
            self.assertTrue((output / record["generation"] / "manifest.json").is_file())

    def test_invalid_replacement_preserves_last_known_good_pointer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "output"
            first = make_staging(root, 12, "a" * 64, b"first synthetic")
            pointer = publish_generation(first, output)
            before = pointer.read_bytes()
            invalid = make_staging(root, 12, "b" * 64, b"broken synthetic", valid=False)
            with self.assertRaisesRegex(ValueError, "manifest-file-integrity"):
                publish_generation(invalid, output)
            self.assertEqual(before, pointer.read_bytes())
            self.assertTrue(invalid.exists())

    def test_refuses_to_overwrite_immutable_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "output"
            publish_generation(make_staging(root, 8, "c" * 64, b"first"), output)
            second = make_staging(root, 8, "c" * 64, b"second")
            with self.assertRaisesRegex(FileExistsError, "immutable-generation-exists"):
                publish_generation(second, output)


if __name__ == "__main__":
    unittest.main()

