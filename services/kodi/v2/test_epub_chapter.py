from io import BytesIO
import unittest
import zipfile
from epub_chapter import chapter, resource, xml

def book(body='<h1>Chapter One</h1><p>Hello <em>quiet</em> world.</p>', extra=None, href='one.xhtml', package_meta=''):
    data = BytesIO()
    files = {
        'mimetype': 'application/epub+zip',
        'META-INF/container.xml': '<container><rootfiles><rootfile full-path="OPS/book.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',
        'OPS/book.opf': '<package xmlns="http://www.idpf.org/2007/opf"><metadata><title>Example Book</title>'+package_meta+'</metadata><manifest><item id="one" href="'+href+'" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="one"/></spine></package>',
        'OPS/one.xhtml': '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Ignore head</title></head><body>'+body+'</body></html>',
    }
    files.update(extra or {})
    with zipfile.ZipFile(data, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, value in files.items(): archive.writestr(name, value)
    return data.getvalue()

class ChapterTests(unittest.TestCase):
    def test_text_blocks_words_and_stable_content_identity(self):
        data = book(); value = chapter(data)
        self.assertEqual(value.title, 'Example Book')
        self.assertEqual(value.text, 'Chapter One\n\nHello quiet world.')
        self.assertEqual([(b.offset, b.kind) for b in value.blocks], [(0, 'heading'), (13, 'paragraph')])
        self.assertEqual([value.text[a:b] for a,b in value.words], ['Chapter', 'One', 'Hello', 'quiet', 'world.'])
        self.assertEqual(value, chapter(data))
        self.assertNotEqual(value.chapter_sha256, chapter(book('<p>Changed</p>')).chapter_sha256)
    def test_scripts_navigation_styles_are_not_read(self):
        value = chapter(book('<script>secret script</script><style>css</style><nav>menu</nav><p>A<br/>B &amp; C.</p>'))
        self.assertEqual(value.text, 'A B & C.')
    def test_external_traversal_ambiguous_and_protected_refused(self):
        for href in ('https://host/chapter', '//host/one', '../one.xhtml', '%2e%2e/one.xhtml', '/one.xhtml', 'one.xhtml?token=private', 'one.xhtml#part', 'C:one.xhtml'):
            with self.subTest(href=href), self.assertRaises(ValueError): chapter(book(href=href))
        for extra in ({'META-INF/encryption.xml':'<encryption/>'}, {'../other':'x'}):
            with self.assertRaises(ValueError): chapter(book(extra=extra))
    def test_bounded_input_invalid_index_fixed_layout_and_empty(self):
        for value in (b'', b'not-a-zip', 'book', b'x'*(32*1024*1024+1)):
            with self.assertRaises(ValueError): chapter(value)
        for index in (True, -1, 1, '0'):
            with self.assertRaises(ValueError): chapter(book(), index)
        with self.assertRaises(ValueError): chapter(book('<p> </p>'))
        with self.assertRaisesRegex(ValueError, 'fixed-layout'):
            chapter(book(package_meta='<meta property="rendition:layout">pre-paginated</meta>'))
    def test_entity_bombs_and_wide_xml_rejected_but_html5_doctype_allowed(self):
        for value in (b'<!DOCTYPE a [<!ENTITY x "words">]><a>&x;</a>', '<a/>'.encode('utf-16')):
            with self.assertRaises(ValueError): xml(value)
        self.assertEqual(xml(b'<!DOCTYPE html><html/>').tag, 'html')
    def test_utf8_offsets_and_inline_tail(self):
        value = chapter(book('<p>été <b>日本語</b> again.</p>'))
        self.assertEqual(value.text, 'été 日本語 again.')
        self.assertEqual([value.text[a:b] for a,b in value.words], ['été', '日本語', 'again.'])
    def test_deep_markup_is_rejected_before_recursive_render(self):
        with self.assertRaisesRegex(ValueError, 'complexity'):
            chapter(book('<div>'*70+'text'+'</div>'*70))
    def test_duplicate_zip_names_and_symlink_members_are_rejected(self):
        import warnings
        for linked in (False, True):
            data = BytesIO(book())
            with zipfile.ZipFile(data, 'a') as archive:
                if linked:
                    entry = zipfile.ZipInfo('link'); entry.external_attr = (0o120777 << 16)
                    archive.writestr(entry, 'other')
                else:
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore'); archive.writestr('OPS/one.xhtml', '<html/>')
            with self.assertRaises(ValueError): chapter(data.getvalue())

if __name__ == '__main__': unittest.main()
