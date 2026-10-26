from pathlib import Path
import tempfile
import unittest

from family_composition import audit_tree, clean_manifest, report


class FamilyCompositionTests(unittest.TestCase):
    def tree(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        return Path(temporary.name)

    def test_clean_tree_has_deterministic_manifest(self):
        root = self.tree()
        (root/'addon.xml').write_text('<addon id="script.asterruntime"/>')
        code = root/'home/default.py'
        code.parent.mkdir()
        code.write_text("ROOT='/storage/.kodi/addons/script.asterruntime/home'\n")
        first = clean_manifest(root)
        second = clean_manifest(root)
        self.assertEqual(first, second)
        self.assertEqual([row['path'] for row in first], ['addon.xml', 'home/default.py'])

    def test_staging_dependencies_are_exact_and_deduplicated(self):
        root = self.tree()
        script = root/'default.py'
        script.write_text("A='/storage/.aster-staging/search/default.py'\n"
                          "B='/storage/.aster-staging/search/movie.py'\n"
                          "C='/storage/.aster-staging/series/default.py'\n")
        result = report(root)
        self.assertFalse(result['passed'])
        self.assertEqual(result['staging_dependencies'], ['search', 'series'])
        self.assertEqual(result['counts'], {'staging-runtime-reference': 2})
        with self.assertRaisesRegex(ValueError, 'not-clean'):
            clean_manifest(root)

    def test_runtime_debris_links_and_special_files_are_rejected(self):
        root = self.tree()
        (root/'._Home.xml').write_bytes(b'debris')
        cache = root/'tools/__pycache__'
        cache.mkdir(parents=True)
        (cache/'helper.pyc').write_bytes(b'compiled')
        old = root/'tools/helper.py.pre-trial'
        old.write_text('old')
        target = root/'target.py'
        target.write_text('safe')
        (root/'linked.py').symlink_to(target)
        findings = audit_tree(root)
        self.assertEqual(sum(item.code == 'runtime-debris' for item in findings), 3)
        self.assertEqual(sum(item.code == 'linked-path' for item in findings), 1)

    def test_binary_payload_does_not_create_false_text_reference(self):
        root = self.tree()
        (root/'image.png').write_bytes(b'/storage/.aster-staging/not-code')
        self.assertEqual(audit_tree(root), ())


if __name__ == '__main__':
    unittest.main()
