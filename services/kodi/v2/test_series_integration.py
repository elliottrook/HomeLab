import ast,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
from build_series_integration import SOURCE,dispatcher,build,HERE

class SeriesIntegrationTests(unittest.TestCase):
    def helper(self):
        spec=importlib.util.spec_from_file_location('aster_series_route_template',HERE/'integration/aster_v2_series.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

    def test_only_verified_native_video_show_identity_can_route(self):
        route=self.helper().selected_show
        self.assertEqual(route(10025,50,'tvshow','12'),12)
        for values in ((10502,50,'tvshow','12'),(10025,19,'tvshow','12'),(10025,50,'movie','12'),
                       (10025,50,'season','12'),(10025,50,'episode','12'),(10025,50,'tvshow','12',True),
                       (10025,50,'tvshow','0'),(10025,50,'tvshow','12),PlayMedia(x)'),(10025,50,'tvshow','2147483648')):
            self.assertIsNone(route(*values))

    def test_existing_dispatch_actions_are_byte_for_byte_unchanged(self):
        old=ast.parse(SOURCE.read_text());new=ast.parse(dispatcher(SOURCE.read_text()))
        get=lambda root:next(n for n in root.body if isinstance(n,ast.FunctionDef) and n.name=='dispatched_action')
        self.assertEqual(ast.dump(get(old)),ast.dump(get(new)))
        self.assertIn('if window_id == 10502 and focus_id == 50:',dispatcher(SOURCE.read_text()))
        self.assertTrue(dispatcher(SOURCE.read_text()).endswith("if __name__ == '__main__':\n    main()\n"))

    def test_immutable_bundle_has_only_two_exact_files_and_pins_series(self):
        before=SOURCE.read_bytes()
        with tempfile.TemporaryDirectory() as parent:
            output=Path(parent)/'one';sha=build(output,'aster-series-preview10','a'*64)
            manifest=json.loads((output/'manifest.json').read_text())
            self.assertEqual(hashlib.sha256((output/'manifest.json').read_bytes()).hexdigest(),sha)
            self.assertEqual({r['path'] for r in manifest['files']},{'tools/select_dispatch.py','tools/aster_v2_series.py'})
            self.assertEqual(manifest['series_manifest_sha256'],'a'*64)
            with self.assertRaises(ValueError):build(output,'aster-series-preview10','a'*64)
        self.assertEqual(SOURCE.read_bytes(),before)
