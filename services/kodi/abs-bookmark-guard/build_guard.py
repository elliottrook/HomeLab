"""Exact deployed-source overlay builder. No Docker, credentials or deployment."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
IMAGE_ID='sha256:66b24f73e543959d5df7e57bc0edbeab5e759730ec356656198b5da123468c15'
EXPECTED={
 'server/models/User.js':'92630399232fe603d05e00aafa1ddbd2bf2d8c00f52d02ab124777560b497171',
 'server/controllers/MeController.js':'12d7dc5763f26a60f0d58509be5a2506453e1204e251ced94884ec87dc0972f4',
 'server/routers/ApiRouter.js':'64802e101319d0b01123d5c4e564f96b787b9475d916467eaae1c4682deec15c'}
def sha(data):return hashlib.sha256(data).hexdigest()
def once(source,before,after):
    if source.count(before)!=1:raise ValueError('source-anchor-not-unique')
    return source.replace(before,after)
def patch_sources(files):
    user=files['server/models/User.js']
    # Preserve unrelated model methods and comments byte-for-byte.
    for name,operation,signature in (
        ('createBookmark','createLegacy','libraryItemId, time, title'),
        ('updateBookmark','updateLegacy','libraryItemId, time, title'),
        ('removeBookmark','deleteLegacy','libraryItemId, time')):
        pattern=r'  async '+name+r'\('+re.escape(signature)+r'\) \{\n.*?\n  \}'
        match=list(re.finditer(pattern,user,re.S))
        if len(match)!=1:raise ValueError('bookmark-model-method-anchor')
        args='{ item: libraryItemId, time'+(', title' if name!='removeBookmark' else '')+' }'
        replacement=f'  async {name}({signature}) {{\n    return (await this.asterMutateBookmark(\'{operation}\', {args})).value\n  }}'
        user=user[:match[0].start()]+replacement+user[match[0].end():]
    helper="""  async asterMutateBookmark(operation, args) {
    const result = await require('../libs/asterBookmarkGuard').mutate(this, operation, args)
    userCache.delete(this.id)
    return result
  }

"""
    user=once(user,'  findBookmark(libraryItemId, time) {',helper+'  findBookmark(libraryItemId, time) {')
    controller=files['server/controllers/MeController.js']
    old="""    if (!req.user.findBookmark(req.params.id, time)) {
      Logger.error(`[MeController] removeBookmark not found`)
      return res.sendStatus(404)
    }

    await req.user.removeBookmark(req.params.id, time)"""
    controller=once(controller,old,"""    if (!(await req.user.removeBookmark(req.params.id, time))) {
      return res.sendStatus(404)
    }""")
    footer="""// Aster: preserve old routes while containing transaction errors, never retry.
const asterGuard = require('../libs/asterBookmarkGuard')
for (const name of ['createBookmark', 'updateBookmark', 'removeBookmark']) {
  const original = MeController.prototype[name]
  MeController.prototype[name] = function (req, res) {
    return asterGuard.respond(res, () => original.call(this, req, res))
  }
}
const asterController = require('../libs/asterBookmarkController')
module.exports = new MeController()
module.exports.asterBookmarkCapabilities = asterController.capabilities
module.exports.asterBookmarkCreateOnly = asterController.createOnly
module.exports.asterBookmarkDeleteMatch = asterController.deleteMatch"""
    controller=once(controller,'module.exports = new MeController()',footer)
    router=files['server/routers/ApiRouter.js']
    anchor="    this.router.post('/me/item/:id/bookmark', MeController.createBookmark.bind(this))"
    routes="""    this.router.get('/me/item/:id/bookmark/aster-guard', MeController.asterBookmarkCapabilities.bind(this))
    this.router.post('/me/item/:id/bookmark/create-only', MeController.asterBookmarkCreateOnly.bind(this))
    this.router.delete('/me/item/:id/bookmark/conditional/:time', MeController.asterBookmarkDeleteMatch.bind(this))
"""
    router=once(router,anchor,routes+anchor)
    return {'server/models/User.js':user,'server/controllers/MeController.js':controller,'server/routers/ApiRouter.js':router}
def build(source,output,node):
    source,output=Path(source),Path(output)
    if output.exists():raise ValueError('immutable-guard-output')
    files={name:(source/name).read_bytes() for name in EXPECTED}
    for name,digest in EXPECTED.items():
        if sha(files[name])!=digest:raise ValueError('deployed-source-drift:'+name)
    patched={name:text.encode() for name,text in patch_sources({n:d.decode() for n,d in files.items()}).items()}
    for name in ('asterBookmarkGuard.js','asterBookmarkController.js'):patched['server/libs/'+name]=(HERE/name).read_bytes()
    output.mkdir(parents=True)
    for name,data in patched.items():
        path=output/'payload'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        subprocess.run([node,'--check',str(path)],check=True,capture_output=True)
    manifest=dict(kind='aster-abs-bookmark-guard.v1',image='ghcr.io/advplyr/audiobookshelf:2.36.0',base_image_id=IMAGE_ID,
        deployment_authorized=False,schema_migration=False,
        files=[dict(path=name,sha256=sha(data),before_sha256=EXPECTED.get(name)) for name,data in sorted(patched.items())])
    raw=(json.dumps(manifest,indent=2)+'\n').encode();(output/'manifest.json').write_bytes(raw)
    return sha(raw)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True);p.add_argument('--node',required=True)
    args=p.parse_args();print(build(args.source,args.output,args.node))
