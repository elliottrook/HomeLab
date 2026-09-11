import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "aster_snapshot_builder", ROOT / "scripts/build-aster-knowledge-snapshot.py"
)
BUILDER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(BUILDER)


class SnapshotMirrorTests(unittest.TestCase):
    def fixture(self, root: Path) -> None:
        entry = root / "entries/source/source-001.md"
        entry.parent.mkdir(parents=True)
        entry.write_text(
            '---\nauthority: "derived-memory"\nsource_locator: "lines 2-3"\n---\nclaim\n'
        )
        (root / "indexes").mkdir()
        (root / "indexes/provenance.json").write_text(json.dumps({"entries": {
            "source-001": {"source_path": "docs/upstream/source/content.txt",
                           "source_locator": "lines 2-3", "source_sha256": "a" * 64}
        }}))
        (root / "state").mkdir()
        (root / "state/generation.json").write_text(json.dumps({
            "entries": 1, "content_sha256": "b" * 64,
            "accepted_input_sha256": "c" * 64,
        }))

    def test_mirror_maps_only_as_derived_memory_with_human_route(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            members, records, state = BUILDER.mirror_members(root)
            self.assertEqual("mirror/entries/source/source-001.md", members[0][0])
            self.assertEqual("derived-memory", records[0]["authority"])
            self.assertEqual("docs/upstream/source/content.txt", records[0]["human_source"])
            self.assertEqual("b" * 64, state["commit"])

    def test_mirror_count_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            generation = root / "state/generation.json"
            payload = json.loads(generation.read_text())
            payload["entries"] = 2
            generation.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "entry count"):
                BUILDER.mirror_members(root)


if __name__ == "__main__":
    unittest.main()
