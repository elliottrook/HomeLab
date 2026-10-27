import ast,json,tempfile,unittest
from pathlib import Path

import build_series_latency_followup as builder
import series_latency_followup as subject

FIXTURE=Path('/private/tmp/aster-series-latency1')

@unittest.skipUnless(FIXTURE.is_dir(),'HP series-latency fixture unavailable')
class SeriesLatencyFollowupTests(unittest.TestCase):
    def changed(self):
        raw={name:(FIXTURE/name).read_bytes() for name in builder.TARGETS}
        runtime=subject.runtime(raw['default.py'],Path(__file__).parent/'series_preview/default.py')
        component=subject.component(raw['component-manifest.json'],runtime)
        launcher=subject.launcher(raw['aster_v2_series.py'],component)
        dispatcher=subject.dispatcher(raw['select_dispatch.py'])
        family=subject.family(raw['family-manifest.json'],component,launcher,dispatcher)
        return runtime,component,launcher,dispatcher,family
    def test_art_is_backgrounded_and_all_tv_routes_converge(self):
        runtime,component,launcher,dispatcher,_=self.changed()
        ast.parse(runtime);ast.parse(launcher);ast.parse(dispatcher)
        self.assertIn(b'threading.Thread',runtime)
        self.assertNotIn(b'cache.localize(client.season',runtime)
        self.assertIn(b'((10025,50),(10000,110))',launcher)
        self.assertIn(b'Container(\'+str(container)+\')',launcher)
        self.assertIn(b'((10025, 50), (10000, 110))',dispatcher)
        record=next(row for row in json.loads(component)['files'] if row['path']=='default.py')
        self.assertEqual(record['sha256'],subject.sha(runtime))
    def test_family_and_immutable_candidate(self):
        _,component,launcher,dispatcher,family=self.changed();value=json.loads(family)
        self.assertEqual(value['components']['aster-series-preview24']['manifest_sha256'],subject.sha(component))
        self.assertEqual(value['skin']['tools/aster_v2_series.py'],subject.sha(launcher))
        self.assertEqual(value['skin']['tools/select_dispatch.py'],subject.sha(dispatcher))
        with tempfile.TemporaryDirectory() as parent:
            target=Path(parent)/'candidate';pin=builder.build(FIXTURE,target)
            manifest=json.loads((target/'manifest.json').read_bytes())
            self.assertEqual(manifest['kind'],'hp-series-latency-followup.v1')
            self.assertEqual(len(manifest['files']),5)
            self.assertEqual(subject.sha((target/'manifest.json').read_bytes()),pin)

if __name__=='__main__':unittest.main()
