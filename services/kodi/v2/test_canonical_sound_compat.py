"""All samples remain identical in normalized amplitude, time and channel."""
import io,tempfile,unittest,wave,sys,zipfile
from pathlib import Path
from canonical_sound_compat import promote,build

SOURCE=Path(__file__).parent.parent/'resource.uisounds.asterhome/resources'

class CompatibilityTests(unittest.TestCase):
    def test_every_sample_and_stereo_frame_preserved(self):
        for path in SOURCE.glob('*.wav'):
            with wave.open(str(path),'rb') as a,wave.open(io.BytesIO(promote(path.read_bytes())),'rb') as b:
                self.assertEqual((a.getnframes(),a.getframerate(),a.getnchannels()),(b.getnframes(),b.getframerate(),b.getnchannels()))
                self.assertEqual(b.getsampwidth(),4)
                raw=a.readframes(a.getnframes());converted=b.readframes(b.getnframes())
                self.assertEqual([int.from_bytes(raw[i:i+3],'little',signed=True)<<8 for i in range(0,len(raw),3)],
                    [int.from_bytes(converted[i:i+4],'little',signed=True) for i in range(0,len(converted),4)])
    def test_immutable_output_and_original_copies(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'compat';result=build(SOURCE,out)
            self.assertEqual(len(result['files']),8)
            for path in SOURCE.glob('*.wav'):self.assertEqual(path.read_bytes(),(out/'masters'/path.name).read_bytes())
            with self.assertRaisesRegex(ValueError,'immutable'):build(SOURCE,out)
    def test_runtime_archive_uses_promoted_bytes(self):
        sys.path.insert(0,str(SOURCE.parent.parent))
        import package_aster_home
        with tempfile.TemporaryDirectory() as tmp:
            result=package_aster_home.build_archive('resource.uisounds.asterhome',Path(tmp),runtime_sounds=True)
            with zipfile.ZipFile(Path(tmp)/result['archive']) as archive:
                for path in SOURCE.glob('*.wav'):
                    self.assertEqual(archive.read('resource.uisounds.asterhome/resources/'+path.name),promote(path.read_bytes()))
