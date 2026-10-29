import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import sa3_guest_validator_upgrade as upgrade


class GuestValidatorUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); root=Path(self.tmp.name)
        self.target=root/"target"; self.source=root/"source"/"scripts/local-ai"; self.checkpoint=root/"checkpoint"
        self.target.mkdir(); self.source.mkdir(parents=True)
        self.old={"lab_hours_inactive_target.py":b"old validator\n","lab_hours_release_manifest.json":b"old manifest\n"}
        self.new={"lab_hours_inactive_target.py":b"new validator\n","lab_hours_release_manifest.json":b"new manifest\n"}
        self.saved=upgrade.FILES
        upgrade.FILES={n:(hashlib.sha256(self.old[n]).hexdigest(),hashlib.sha256(self.new[n]).hexdigest(),0o644) for n in self.old}
        for n,d in self.old.items(): (self.target/n).write_bytes(d); os.chmod(self.target/n,0o644)
        for n,d in self.new.items(): (self.source/n).write_bytes(d); os.chmod(self.source/n,0o644)
    def tearDown(self): upgrade.FILES=self.saved; self.tmp.cleanup()
    def runner(self,command,**kwargs):
        if command[-1].endswith("lab_hours_inactive_target.py"):
            out={"state":"valid","guest":"110","runtime_files":4}
            return subprocess.CompletedProcess(command,0,json.dumps(out),"")
        return subprocess.CompletedProcess(command,0,"","")
    def test_success(self):
        value=upgrade.install(self.source.parents[1],target=self.target,checkpoint=self.checkpoint,uid=os.geteuid(),run=self.runner)
        self.assertEqual(value["guest_validation"],"pass")
        self.assertEqual((self.target/"lab_hours_inactive_target.py").read_bytes(),self.new["lab_hours_inactive_target.py"])
    def test_failed_validation_rolls_back(self):
        def fail(command,**kwargs): return subprocess.CompletedProcess(command,1,"bad","")
        with self.assertRaises(upgrade.UpgradeError):
            upgrade.install(self.source.parents[1],target=self.target,checkpoint=self.checkpoint,uid=os.geteuid(),run=fail)
        for n,d in self.old.items(): self.assertEqual((self.target/n).read_bytes(),d)
    def test_checkpoint_must_be_fresh(self):
        self.checkpoint.mkdir()
        with self.assertRaisesRegex(upgrade.UpgradeError,"CHECKPOINT_EXISTS"):
            upgrade.install(self.source.parents[1],target=self.target,checkpoint=self.checkpoint,uid=os.geteuid(),run=self.runner)


if __name__ == "__main__": unittest.main()
