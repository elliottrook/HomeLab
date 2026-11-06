import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "repair_model_cache_custody", HERE / "repair_model_cache_custody.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ModelCustodyRepairTests(unittest.TestCase):
    def test_repair_is_checkpointed_and_inert(self):
        source = (HERE / "repair_model_cache_custody.py").read_text()
        ast.parse(source)
        for token in ("LEASE_NOT_READY", "FAILED_ATTEMPT_NOT_RETAINED",
                      "GUEST_CHECKPOINT", "STATIC_VALIDATION",
                      '"booking_created": False', '"workload_started": False'):
            self.assertIn(token, source)
        self.assertNotIn("reserve --", source)
        self.assertNotIn("systemctl start", source)

    def test_benchmark_bounds_model_links_to_local_cache(self):
        source = (HERE / "ebook_word_alignment_benchmark.py").read_text()
        self.assertIn("resolved.relative_to(cache)", source)
        self.assertIn("PINNED_MODEL_CUSTODY", source)
        self.assertIn("require_model_hash(MODEL / name", source)

    def test_build_repins_registry_and_manifest_as_one_set(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / "stage"
            stage.mkdir()
            registry = root / "registry.py"
            adapter = root / "adapter.py"
            manifest = root / "manifest.json"
            old_adapter = b"old adapter"
            old_adapter_sha = hashlib.sha256(old_adapter).hexdigest()
            old_registry = ("adapter_pin = '" + old_adapter_sha + "'\n").encode()
            old_registry_sha = hashlib.sha256(old_registry).hexdigest()
            adapter.write_bytes(old_adapter)
            registry.write_bytes(old_registry)
            manifest.write_text(json.dumps({"pins": {
                "adapter.py": old_adapter_sha,
                "registry.py": old_registry_sha,
            }}))
            guest = b"new guest"
            guest_sha = hashlib.sha256(guest).hexdigest()
            new_adapter = ("guest_pin = '" + guest_sha + "'\n").encode()
            new_adapter_sha = hashlib.sha256(new_adapter).hexdigest()
            (stage / "ebook_word_alignment_benchmark.py").write_bytes(guest)
            (stage / "epub_word_alignment_adapter.py").write_bytes(new_adapter)
            expected = {
                registry: old_registry_sha,
                adapter: old_adapter_sha,
                manifest: hashlib.sha256(manifest.read_bytes()).hexdigest(),
            }
            with mock.patch.multiple(
                    MODULE, REGISTRY=registry, ADAPTER=adapter, MANIFEST=manifest,
                    EXPECTED=expected, OLD_GUEST_SHA="f" * 64,
                    NEW_GUEST_SHA=guest_sha, NEW_ADAPTER_SHA=new_adapter_sha):
                output = MODULE.build(stage, expected_uid=os.getuid())
            self.assertIn(new_adapter_sha.encode(), output[registry])
            pins = json.loads(output[manifest])["pins"]
            self.assertEqual(pins["adapter.py"], new_adapter_sha)
            self.assertEqual(pins["registry.py"], hashlib.sha256(output[registry]).hexdigest())


if __name__ == "__main__":
    unittest.main()
