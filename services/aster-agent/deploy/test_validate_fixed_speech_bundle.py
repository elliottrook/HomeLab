import json
import tempfile
import unittest
from pathlib import Path
from validate_fixed_speech_bundle import MANIFEST, validate

class FixedSpeechBundleTests(unittest.TestCase):
    def mutate(self, change):
        value=json.loads(MANIFEST.read_text()); change(value)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"m.json"; path.write_text(json.dumps(value))
            with self.assertRaises(ValueError): validate(path)
    def test_manifest_passes(self): validate()
    def test_source_drift_rejected(self): self.mutate(lambda v:v["entries"][0].update(sha256="0"*64))
    def test_target_and_effect_broadening_rejected(self):
        self.mutate(lambda v:v["entries"][0].update(target="/tmp/other"))
        self.mutate(lambda v:v["entries"][0].update(predecessor="present"))
        self.mutate(lambda v:v["excluded"].remove("model-call"))
    def test_dependency_or_unit_drift_rejected(self):
        self.mutate(lambda v:v["dependencies"][0].update(sha256="0"*64))
        self.mutate(lambda v:v["units"]["must_remain_disabled_inactive"].pop())

if __name__=="__main__": unittest.main()
