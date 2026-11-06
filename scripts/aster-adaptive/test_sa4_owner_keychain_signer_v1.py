from pathlib import Path
import os
import subprocess
import tempfile
import unittest


class SA4OwnerKeychainSignerTests(unittest.TestCase):
    def test_source_compiles_and_self_test_has_no_keychain_effect(self):
        source = Path(__file__).with_name("sa4_owner_keychain_signer_v1.swift")
        with tempfile.TemporaryDirectory() as raw:
            binary = Path(raw) / "sa4-owner-signer"
            environment = dict(os.environ)
            environment["SWIFT_MODULECACHE_PATH"] = str(Path(raw) / "swift-cache")
            environment["CLANG_MODULE_CACHE_PATH"] = str(Path(raw) / "clang-cache")
            build = subprocess.run(
                ["xcrun", "swiftc", str(source), "-framework", "Security",
                 "-o", str(binary)], check=False, capture_output=True, text=True,
                env=environment)
            self.assertEqual(0, build.returncode, build.stderr)
            result = subprocess.run([str(binary), "self-test"], check=False,
                                    capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("self-test: pass\n", result.stdout)

    def test_source_exposes_no_private_export_command(self):
        source = Path(__file__).with_name(
            "sa4_owner_keychain_signer_v1.swift").read_text()
        self.assertNotIn('case "export"', source)
        self.assertNotIn("SecKeyCopyExternalRepresentation(privateKey", source)
        self.assertIn("SecAccessCreate", source)
        self.assertIn("[] as CFArray", source)
        self.assertIn("kSecAttrAccess: keyAccess", source)
        self.assertIn("kSecAttrIsExtractable: false", source)
        self.assertIn("kSecAttrIsSensitive: true", source)
        self.assertNotIn("kSecUseDataProtectionKeychain", source)
        self.assertIn("raw.count <= 4096", source)
        self.assertIn('acceptedSignerID = "jason-owner"', source)
        self.assertIn(
            'acceptedKeyDigest = "17738e78d92b3ba4fff496f4d51904b6c6dd18d4acf80b3ef2a34a27ea6de946"',
            source)


if __name__ == "__main__":
    unittest.main()
