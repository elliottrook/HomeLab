import importlib.util
from pathlib import Path
import tempfile
import unittest


class ProbeTests(unittest.TestCase):
    def setUp(self):
        path=Path(__file__).parent/'tools/validate_album_order.py'
        spec=importlib.util.spec_from_file_location('album_probe',path)
        self.probe=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.probe)

    def test_probe_compiles_and_cannot_overwrite_existing_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'probe.py'
            self.probe.build_probe(output)
            compile(output.read_text(),str(output),'exec')
            self.assertIn('def read_album(',output.read_text())
            with self.assertRaises(FileExistsError):self.probe.build_probe(output)

    def test_mutating_probe_methods_fail_before_network(self):
        for method in ('Player.Open','Playlist.Clear','Playlist.Add',
                       'AudioLibrary.SetSongDetails','GUI.ActivateWindow'):
            with self.assertRaisesRegex(ValueError,'Read-only probe method required'):
                self.probe.rpc(method)


if __name__=='__main__':unittest.main()
