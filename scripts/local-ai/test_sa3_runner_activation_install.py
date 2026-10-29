import hashlib,json,os,subprocess,tempfile,unittest
from pathlib import Path
import sa3_runner_activation_install as install
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();r=Path(self.t.name);self.target=r/"target";self.source=r/"source"/"scripts/local-ai";self.cp=r/"cp";self.res=r/"res";self.target.mkdir();self.source.mkdir(parents=True);self.res.mkdir();self.saved=install.FILES
  names=("full_inference_lab_runtime.py","lab_hours_reserved_runner.py","lab_hours_release_manifest.json");self.old={n:("old "+n).encode() for n in names};self.new={n:("new "+n).encode() for n in names};install.FILES={n:(hashlib.sha256(self.old[n]).hexdigest(),hashlib.sha256(self.new[n]).hexdigest(),0o755 if n.endswith(".py") else 0o644) for n in names}
  for n,d in self.old.items():(self.target/n).write_bytes(d);os.chmod(self.target/n,install.FILES[n][2])
  for n,d in self.new.items():(self.source/n).write_bytes(d);os.chmod(self.source/n,install.FILES[n][2])
 def tearDown(self):install.FILES=self.saved;self.t.cleanup()
 def run(self,*a,**k):return subprocess.CompletedProcess(a[0],0,"","")
 def test_success(self):self.assertEqual(install.install(self.source.parents[1],target=self.target,checkpoint=self.cp,reservations=self.res,uid=os.geteuid(),run=self.run)["sa3_runner"],"available")
 def test_active_booking_blocks(self):
  (self.res/"x.json").write_text(json.dumps({"workload":"sa3-expanded-source-quality-v1","state":"reserved"}))
  with self.assertRaisesRegex(install.ActivationError,"ACTIVE_SA3"):install.install(self.source.parents[1],target=self.target,checkpoint=self.cp,reservations=self.res,uid=os.geteuid(),run=self.run)
 def test_failure_rolls_back(self):
  def fail(*a,**k):return subprocess.CompletedProcess(a[0],1,"","bad")
  with self.assertRaises(install.ActivationError):install.install(self.source.parents[1],target=self.target,checkpoint=self.cp,reservations=self.res,uid=os.geteuid(),run=fail)
  for n,d in self.old.items():self.assertEqual((self.target/n).read_bytes(),d)
if __name__=="__main__":unittest.main()
