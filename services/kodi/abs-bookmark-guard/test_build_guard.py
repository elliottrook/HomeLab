"""Synthetic builder/fail-closed/removal tests; no network or real state."""
import hashlib,importlib.util,json,os,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import verify_guard as verifier
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('build_guard',HERE/'build_guard.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
NODE=os.environ.get('ASTER_GUARD_NODE','node')
class BuilderTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source=self.root/'source';self.output=self.root/'package'
        sources={
            'server/models/User.js':"""class User {
  findBookmark(libraryItemId, time) { return null }
  async createBookmark(libraryItemId, time, title) {
    return 'old'
  }
  async updateBookmark(libraryItemId, time, title) {
    return 'old'
  }
  async removeBookmark(libraryItemId, time) {
    return false
  }
  untouched() { return 'unchanged sentinel' }
}
""",
            'server/controllers/MeController.js':"""class MeController {
  async removeBookmark(req, res) {
    const time = 0
    if (!req.user.findBookmark(req.params.id, time)) {
      Logger.error(`[MeController] removeBookmark not found`)
      return res.sendStatus(404)
    }

    await req.user.removeBookmark(req.params.id, time)
  }
}
module.exports = new MeController()
""",
            'server/routers/ApiRouter.js':"""class Router {
  init() {
    this.router.post('/me/item/:id/bookmark', MeController.createBookmark.bind(this))
  }
}
"""}
        for name,text in sources.items():
            p=self.source/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
        self.expected={name:builder.sha(text.encode()) for name,text in sources.items()}
        p=patch.object(builder,'EXPECTED',self.expected);p.start();self.addCleanup(p.stop)
        p=patch.object(verifier,'EXPECTED',self.expected);p.start();self.addCleanup(p.stop)
    def build(self):return builder.build(self.source,self.output,NODE)
    def test_exact_five_members_and_dedicated_routes(self):
        digest=self.build();manifest=json.loads((self.output/'manifest.json').read_text())
        self.assertEqual(digest,builder.sha((self.output/'manifest.json').read_bytes()))
        self.assertEqual(len(manifest['files']),5);self.assertFalse(manifest['deployment_authorized'])
        self.assertEqual(manifest['base_image_id'],builder.IMAGE_ID)
        user=(self.output/'payload/server/models/User.js').read_text()
        self.assertIn('unchanged sentinel',user);self.assertIn('createLegacy',user)
        controller=(self.output/'payload/server/controllers/MeController.js').read_text()
        self.assertNotIn('if (!req.user.findBookmark',controller)
        router=(self.output/'payload/server/routers/ApiRouter.js').read_text()
        self.assertIn("post('/me/item/:id/bookmark/create-only'",router)
        self.assertIn("delete('/me/item/:id/bookmark/conditional/:time'",router)
        self.assertIn("post('/me/item/:id/bookmark',",router)
    def test_unknown_source_refused_before_output(self):
        (self.source/'server/models/User.js').write_text('unexpected newer version')
        with self.assertRaisesRegex(ValueError,'source-drift'):self.build()
        self.assertFalse(self.output.exists())
    def test_immutable_output(self):
        self.build()
        with self.assertRaisesRegex(ValueError,'immutable'):self.build()
    def test_verifier_accepts_exact_artifact_without_activation(self):
        result=verifier.verify(self.output,self.build())
        self.assertEqual(result,dict(verified=True,files_verified=5,activation_performed=False))
    def test_verifier_refuses_changed_payload(self):
        digest=self.build();(self.output/'payload/server/models/User.js').write_text('unexpected code')
        with self.assertRaisesRegex(ValueError,'file-drift'):verifier.verify(self.output,digest)
    def test_verifier_refuses_added_target_even_with_recomputed_manifest_hash(self):
        self.build();path=self.output/'manifest.json';m=json.loads(path.read_text())
        m['files'][0]['path']='../not-an-approved-target'
        raw=json.dumps(m).encode();path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError,'five-targets'):verifier.verify(self.output,builder.sha(raw))
    def test_removing_overlay_restores_all_original_code_without_data_restore(self):
        self.build();application=self.root/'synthetic-app';shutil.copytree(self.source,application)
        fake_data=application/'private-progress';fake_data.write_text('legitimate new position')
        manifest=json.loads((self.output/'manifest.json').read_text())
        before={name:(application/name).read_bytes() for name in self.expected}
        for row in manifest['files']:
            target=application/row['path'];target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes((self.output/'payload'/row['path']).read_bytes())
            self.assertEqual(builder.sha(target.read_bytes()),row['sha256'])
        for name,data in before.items():(application/name).write_bytes(data)
        self.assertTrue(all(builder.sha((application/n).read_bytes())==digest for n,digest in self.expected.items()))
        self.assertEqual(fake_data.read_text(),'legitimate new position')
        self.assertNotIn('create-only',(application/'server/routers/ApiRouter.js').read_text())
        # Inert new modules are not called once the original router/model return.
