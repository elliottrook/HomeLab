import importlib.util
import tarfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('fp16_stage',Path(__file__).with_name('stage-sycl-fp16.py'))
stage=importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)

class FP16StagingTests(unittest.TestCase):
    def test_accepts_namespaced_file_and_local_symlink(self):
        file=tarfile.TarInfo('llama-b11429/libggml.so.0')
        file.size=42
        link=tarfile.TarInfo('llama-b11429/libggml.so')
        link.type=tarfile.SYMTYPE
        link.linkname='libggml.so.0'
        self.assertEqual(stage.validate_members([file,link]),42)

    def test_rejects_traversal_absolute_and_device_members(self):
        for name in ['../escape','llama-b11429/../../escape','/llama-b11429/file','other/file']:
            with self.assertRaises(AssertionError):
                stage.validate_members([tarfile.TarInfo(name)])
        device=tarfile.TarInfo('llama-b11429/device')
        device.type=tarfile.CHRTYPE
        with self.assertRaises(AssertionError): stage.validate_members([device])

    def test_rejects_escape_symlinks(self):
        for target in ['/etc/passwd','../../etc/passwd']:
            link=tarfile.TarInfo('llama-b11429/link')
            link.type=tarfile.SYMTYPE
            link.linkname=target
            with self.assertRaises(AssertionError): stage.validate_members([link])
