from pathlib import Path
import tempfile
import unittest

from skin_contract import audit_skin, report, require_clean_skin


REPOSITORY_SKIN = Path(__file__).resolve().parents[1]/'skin.asterhome'


class SkinContractTests(unittest.TestCase):
    def tree(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root/'1080i').mkdir()
        (root/'1080i'/'Font.xml').write_text(
            '<fonts><fontset><font><name>font24</name></font></fontset></fonts>',
            encoding='utf-8')
        (root/'1080i'/'Home.xml').write_text(
            '<window><controls><control><font>font24</font></control>'
            '</controls></window>', encoding='utf-8')
        return root

    def test_clean_tree_passes_with_deterministic_report(self):
        root = self.tree()
        self.assertEqual(audit_skin(root), ())
        self.assertEqual(report(root), {'passed': True, 'findings': [],
                                        'counts': {}})
        self.assertTrue(require_clean_skin(root))

    def test_appledouble_metadata_is_rejected_before_xml_parsing(self):
        root = self.tree()
        (root/'1080i'/'._Home.xml').write_bytes(b'\x00\x05\x16\x07metadata')
        findings = audit_skin(root)
        self.assertEqual(findings[-1].code, 'appledouble-metadata')
        self.assertNotIn('invalid-xml', {item.code for item in findings})

    def test_malformed_xml_is_rejected(self):
        root = self.tree()
        (root/'1080i'/'Broken.xml').write_text('<window>', encoding='utf-8')
        self.assertIn('invalid-xml', {item.code for item in audit_skin(root)})

    def test_undefined_font_is_rejected(self):
        root = self.tree()
        (root/'1080i'/'Home.xml').write_text(
            '<window><control><font>font18</font></control></window>',
            encoding='utf-8')
        findings = audit_skin(root)
        self.assertEqual([(item.code, item.path, item.value) for item in findings],
                         [('undefined-font', '1080i/Home.xml', 'font18')])
        with self.assertRaisesRegex(ValueError, 'not-clean'):
            require_clean_skin(root)

    def test_missing_font_catalogue_is_rejected(self):
        root = self.tree()
        (root/'1080i'/'Font.xml').unlink()
        self.assertIn('missing-font-catalogue',
                      {item.code for item in audit_skin(root)})

    def test_repository_skin_passes_the_deployable_contract(self):
        self.assertEqual(audit_skin(REPOSITORY_SKIN), ())


if __name__ == '__main__':
    unittest.main()
