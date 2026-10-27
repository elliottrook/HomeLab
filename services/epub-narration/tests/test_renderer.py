from pathlib import Path
import importlib.util
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1]))

from epub_narration.publication import sha256_file
from epub_narration.renderer import CLEANUP_SHA256


class RendererContractTests(unittest.TestCase):
    def test_pinned_cleanup_hash_and_long_form_units(self):
        cleanup = Path(__file__).parents[1] / "vendor" / "digest_text.py"
        self.assertEqual(CLEANUP_SHA256, sha256_file(cleanup))
        spec = importlib.util.spec_from_file_location("test_cleanup", cleanup)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        spoken = module.speech_text("B.C. paid $1,200. Visit https://example.com now.")
        self.assertEqual("British Columbia paid one thousand two hundred dollars. Visit now.", spoken)
        units = module.narration_units(spoken)
        self.assertTrue(units)
        self.assertEqual(0.0, units[-1][1])

    def test_renderer_publishes_private_hash_bound_content(self):
        source = (Path(__file__).parents[1] / "epub_narration" / "renderer.py").read_text()
        self.assertIn('content_root = staging / "content"', source)
        self.assertIn('"text_sha256": hashlib.sha256(cleaned.encode("utf-8")).hexdigest()', source)
        self.assertIn('for path in (opus_path, timing_path, content_path)', source)


if __name__ == "__main__":
    unittest.main()
