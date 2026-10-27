from pathlib import Path
import tempfile
import unittest

from family_composition import audit_tree, clean_manifest, report
from build_family_runtime import addon_launches, rewrite_component


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

    def test_camera_launchers_use_installed_addon(self):
        source = (b'<onload>RunScript(/storage/.aster-camera/view.py,entry)</onload>'
                  b'<onclick>RunScript(/storage/.aster-camera/view.py,toggle)</onclick>'
                  b'<onunload>RunScript(/storage/.aster-camera/view.py,leave)</onunload>')
        result = addon_launches(source)
        self.assertNotIn(b'/storage/.aster-camera/view.py', result)
        self.assertEqual(result.count(
            b'RunScript(script.asterruntime,aster-camera2,view,'), 3)

    def test_camera_component_keeps_only_view_controller(self):
        files = {
            'view.py': (b"SCRIPT='/storage/.aster-camera/view.py'\n"
                        b"PATH='/storage/.aster-staging/aster-home-status1/default.py'\n"),
            'proxy.py': b'private-local-service\n',
            'frame.py': b'remote-source\n',
            'aster-camera.service': b'unit\n',
            'camera-idle.png': b'pixels',
            'custom_1112_home.xml': b'<window/>',
        }
        result = rewrite_component('aster-camera2', files, {})
        self.assertEqual(set(result), {'view.py'})
        self.assertIn(b"SCRIPT='script.asterruntime,aster-camera2,view'",
                      result['view.py'])
        self.assertIn(b'/storage/.kodi/addons/script.asterruntime/aster-home-status1/default.py',
                      result['view.py'])

    def test_home_component_does_not_open_retired_legacy_feed(self):
        files = {'default.py': (
            b"SCRIPT='/storage/.aster-staging/aster-home-status1/default.py'\n"
            b"def main(action):\n"
            b"    if action=='entry':\n"
            b"        hub_data.main('home')\n"
            b"        xbmc.executebuiltin('AlarmClock(AsterHomeStatus,RunScript('+SCRIPT+',tick)')\n")}
        result = rewrite_component('aster-home-status1', files, {})['default.py']
        self.assertNotIn(b"hub_data.main('home')", result)
        self.assertIn(b"('TimerDigital','--:--')", result)
        self.assertIn(b"SCRIPT='script.asterruntime,aster-home-status1,default'", result)

    def test_books_doctor_keeps_separately_pinned_reader_boundary(self):
        installed=b'/storage/.kodi/addons/script.asterruntime/aster-books-compiler-reader-v1'
        files={'default.py':(
            b'import deploy_startup as guard\n'
            b"sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')\n"),
            'epub_reader_doctor.py':(
                b"READER = Path('/storage/.aster-staging/aster-books-compiler-reader-v1')\n")}
        result=rewrite_component('aster-network-preview6',files,{})
        self.assertNotIn(installed,result['epub_reader_doctor.py'])
        self.assertIn(b'/storage/.aster-staging/aster-books-compiler-reader-v1',
                      result['epub_reader_doctor.py'])
        self.assertIn(b'import runtime_guard as guard',result['default.py'])


if __name__ == '__main__':
    unittest.main()
