'use strict'
// All users/books/SQLite files here are synthetic; no live server is contacted.
const { test } = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs'), os = require('node:os'), path = require('node:path'), vm = require('node:vm')
const http = require('node:http')
const { fork } = require('node:child_process')
const { Sequelize, Model, DataTypes } = require('sequelize')
const guard = require('./asterBookmarkGuard')
const candidate = process.env.ASTER_GUARD_CANDIDATE
assert.ok(candidate, 'exact built candidate required')
const userSource = fs.readFileSync(path.join(candidate, 'payload/server/models/User.js'), 'utf8')
const controllerSource = fs.readFileSync(path.join(candidate, 'payload/server/controllers/MeController.js'), 'utf8')
const controllerAddon = fs.readFileSync(path.join(candidate, 'payload/server/libs/asterBookmarkController.js'), 'utf8')
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms))
let fixtures = 0
async function setup(existingPath) {
  const folder = existingPath ? null : fs.mkdtempSync(path.join(os.tmpdir(), 'aster-guard-test-'))
  const filename = existingPath || path.join(folder, 'synthetic.sqlite')
  const db = new Sequelize({ dialect: 'sqlite', storage: filename, logging: false, retry: { max: 0 } })
  class User extends Model {}
  User.init({ id: { type: DataTypes.STRING, primaryKey: true }, bookmarks: DataTypes.JSON,
    username: DataTypes.STRING, token: DataTypes.STRING, outside: DataTypes.STRING }, { sequelize: db, modelName: 'user' })
  const sandbox = { Model, require: name => {
    assert.equal(name, '../libs/asterBookmarkGuard'); return guard
  }, userCache: { delete() {} } }
  const methods = ['asterMutateBookmark', 'createBookmark', 'updateBookmark', 'removeBookmark'].map(name => {
    const match = userSource.match(new RegExp('  async ' + name + '\\([^)]*\\) \\{\\n[\\s\\S]*?\\n  \\}'))
    assert.ok(match, 'patched model method ' + name); return match[0]
  }).join('\n')
  const patched = vm.runInNewContext('(class Patched extends Model {\n' + methods + '\n})', sandbox)
  for (const name of ['asterMutateBookmark', 'createBookmark', 'updateBookmark', 'removeBookmark']) User.prototype[name] = patched.prototype[name]
  if (!existingPath) {
    await db.sync()
    await User.create({ id: 'household', bookmarks: [], username: 'unchanged-name', token: 'synthetic-only', outside: 'unchanged-position' })
    await User.create({ id: 'other', bookmarks: [], username: 'other', token: 'synthetic-other', outside: 'other-position' })
  }
  fixtures++
  return { db, User, filename,
    async user(id = 'household') { return User.findByPk(id) },
    async rows(id = 'household') { return (await User.findByPk(id)).bookmarks },
    async close() { await db.close(); if (folder) fs.rmSync(folder, { recursive: true }) } }
}
function oldRow(title = 'Family note') { return { libraryItemId: 'book', time: 42, title, createdAt: 1000 } }
const args = { item: 'book', time: 42, title: 'New note' }
async function rejectsStatus(promise, status, code) {
  await assert.rejects(promise, error => error.status === status && error.code === code)
}
test('create-only conflict preserves original record, including same-title collision', () => {
  const source = [oldRow()]
  for (const title of ['New note', 'Family note']) assert.throws(() => guard.change('household', source, 'createOnly', { ...args, title }), e => e.status === 409)
  assert.deepEqual(source, [oldRow()])
})
test('fresh creates have unique guard generations and account-bound ETags', () => {
  const a = guard.change('household', [], 'createOnly', args, () => 1000, () => 'first').value
  const b = guard.change('household', [], 'createOnly', args, () => 1000, () => 'second').value
  assert.notEqual(guard.etag('household', a), guard.etag('household', b))
  assert.notEqual(guard.etag('household', a), guard.etag('other', a))
})
test('conditional delete requires strong exact ETag; edit-away/back invalidates it', () => {
  let rows = guard.change('household', [], 'createOnly', args, () => 1000, () => 'first').rows
  const tag = guard.etag('household', rows[0])
  rows = guard.change('household', rows, 'updateLegacy', { ...args, title: 'Changed' }, Date.now, () => 'second').rows
  rows = guard.change('household', rows, 'updateLegacy', args, Date.now, () => 'third').rows
  assert.throws(() => guard.change('household', rows, 'deleteMatch', { ...args, match: tag }), e => e.status === 412)
  for (const match of [undefined, '*', 'W/' + tag]) assert.throws(() => guard.change('household', rows, 'deleteMatch', { ...args, match }), e => e.status === 428)
})
test('delete/recreate in the same millisecond cannot reuse cleanup token', () => {
  const before = guard.change('household', [], 'createOnly', args, () => 1000, () => 'first').value
  const newer = guard.change('household', [], 'createLegacy', args, () => 1000, () => 'second').value
  assert.throws(() => guard.change('household', [newer], 'deleteMatch', { ...args, match: guard.etag('household', before) }), e => e.status === 412)
})
test('invalid input and ambiguous state fail closed', () => {
  for (const time of [-1, NaN, 1.2, '42', 604801]) assert.throws(() => guard.change('household', [], 'createOnly', { ...args, time }))
  for (const title of ['', 'bad\nlabel', 'x'.repeat(161)]) assert.throws(() => guard.change('household', [], 'createOnly', { ...args, title }))
  assert.throws(() => guard.change('household', [oldRow(), oldRow()], 'createOnly', args), e => e.code === 'bookmark_identity_ambiguous')
})
test('real SQLite: stale independent request instances cannot overwrite one timestamp', async () => {
  const f = await setup()
  try {
    const stale1 = await f.user(), stale2 = await f.user()
    const original = await stale1.asterMutateBookmark('createOnly', args)
    await rejectsStatus(stale2.asterMutateBookmark('createOnly', { ...args, title: 'Overwriter' }), 409, 'bookmark_already_exists')
    assert.deepEqual(await f.rows(), [original.value])
  } finally { await f.close() }
})
test('real SQLite: parallel different timestamps preserve all records and other fields', async () => {
  const f = await setup()
  try {
    const before = (await f.user()).toJSON()
    const instances = await Promise.all(Array.from({ length: 20 }, () => f.user()))
    await Promise.all(instances.map((u, i) => u.asterMutateBookmark('createOnly', { ...args, time: i, title: 'Note ' + i })))
    assert.equal((await f.rows()).length, 20)
    const after = (await f.user()).toJSON()
    for (const key of ['id', 'username', 'token', 'outside', 'createdAt', 'updatedAt']) assert.deepEqual(after[key], before[key])
    assert.deepEqual(await f.rows('other'), [])
  } finally { await f.close() }
})
test('real SQLite: legacy create/rename/update/delete remain compatible and use fresh state', async () => {
  const f = await setup()
  try {
    const one = await f.user(), stale = await f.user()
    const first = await one.createBookmark('book', 42, 'First')
    const renamed = await stale.createBookmark('book', '42', 'Legacy rename')
    assert.equal(renamed.createdAt, first.createdAt); assert.equal(renamed.title, 'Legacy rename')
    assert.equal((await one.updateBookmark('book', 42, 'Explicit edit')).title, 'Explicit edit')
    assert.equal(await stale.removeBookmark('book', 42), true)
    assert.equal(await one.removeBookmark('book', 42), false)
    assert.equal(await one.updateBookmark('book', 42, 'Missing'), null)
    assert.deepEqual(await f.rows(), [])
  } finally { await f.close() }
})
test('real SQLite: legacy mutation invalidates conditional cleanup token', async () => {
  const f = await setup()
  try {
    const user = await f.user(), other = await f.user()
    const created = await user.asterMutateBookmark('createOnly', args)
    await other.updateBookmark('book', 42, 'Family changed this')
    await rejectsStatus(user.asterMutateBookmark('deleteMatch', { ...args, match: created.etag }), 412, 'bookmark_changed')
    assert.equal((await f.rows())[0].title, 'Family changed this')
  } finally { await f.close() }
})
test('real SQLite: conditional delete removes only exact new record', async () => {
  const f = await setup()
  try {
    const user = await f.user()
    await user.createBookmark('book', 10, 'Keep me')
    const created = await user.asterMutateBookmark('createOnly', args)
    assert.equal((await user.asterMutateBookmark('deleteMatch', { ...args, match: created.etag })).value, true)
    assert.deepEqual((await f.rows()).map(r => [r.time, r.title]), [[10, 'Keep me']])
    await rejectsStatus(user.asterMutateBookmark('deleteMatch', { ...args, match: created.etag }), 404, 'bookmark_not_found')
  } finally { await f.close() }
})
test('real SQLite: failed save rolls transaction back without caller-cache mutation', async () => {
  const f = await setup()
  try {
    const user = await f.user()
    f.User.addHook('afterSave', 'synthetic-failure', () => { throw Error('secret-looking diagnostic must not escape') })
    await rejectsStatus(user.asterMutateBookmark('createOnly', args), 500, 'bookmark_guard_failed')
    f.User.removeHook('afterSave', 'synthetic-failure')
    assert.deepEqual(await f.rows(), []); assert.deepEqual(user.bookmarks, [])
  } finally { await f.close() }
})
test('real SQLite: separate DB connections serialize the same timestamp atomically', async () => {
  const f = await setup(), g = await setup(f.filename)
  try {
    const [a, b] = await Promise.all([f.user(), g.user()])
    const results = await Promise.allSettled([a.asterMutateBookmark('createOnly', args), b.asterMutateBookmark('createOnly', { ...args, title: 'Second contender' })])
    assert.equal(results.filter(r => r.status === 'fulfilled').length, 1)
    assert.equal(results.find(r => r.status === 'rejected').reason.status, 409)
    assert.equal((await f.rows()).length, 1)
  } finally { await g.close(); await f.close() }
})
test('real SQLite: separate DB connections preserve concurrent distinct timestamps', async () => {
  const f = await setup(), g = await setup(f.filename)
  try {
    const [a, b] = await Promise.all([f.user(), g.user()])
    await Promise.all([a.asterMutateBookmark('createOnly', args), b.createBookmark('book', 55, 'Legacy simultaneous')])
    assert.deepEqual((await f.rows()).map(r => r.time).sort(), [42, 55])
  } finally { await g.close(); await f.close() }
})
test('real SQLite: two independent processes race, exactly one creation wins', { timeout: 10000 }, async () => {
  const f = await setup(), children = []
  function worker() {
    const child = fork(path.join(__dirname, 'guard_worker.cjs'), [], { stdio: ['ignore', 'ignore', 'ignore', 'ipc'] })
    children.push(child)
    const ready = new Promise((resolve, reject) => {
      child.on('message', msg => { if (msg.kind === 'ready') resolve(); else if (msg.kind === 'failed') reject(Error('worker failed')) })
      child.on('error', reject)
    })
    const result = new Promise((resolve, reject) => {
      child.on('message', msg => { if (msg.kind === 'result') resolve(msg) })
      child.on('error', reject)
    })
    child.send({ kind: 'init', filename: f.filename, candidate })
    return { child, ready, result }
  }
  try {
    const a = worker(), b = worker()
    await Promise.all([a.ready, b.ready])
    a.child.send({ kind: 'go', title: 'Process A' }); b.child.send({ kind: 'go', title: 'Process B' })
    const results = await Promise.all([a.result, b.result])
    assert.deepEqual(results.map(r => r.status).sort(), [201, 409])
    assert.equal((await f.rows()).length, 1)
  } finally { for (const child of children) if (child.connected) child.kill(); await f.close() }
})
test('real SQLite: held external write lock yields busy, no write and no replay', async () => {
  const f = await setup(), sqlite = require('sqlite3'), locker = new sqlite.Database(f.filename)
  const run = sql => new Promise((resolve, reject) => locker.run(sql, error => error ? reject(error) : resolve()))
  try {
    const user = await f.user(); await run('BEGIN IMMEDIATE')
    await rejectsStatus(user.asterMutateBookmark('createOnly', args), 503, 'bookmark_busy')
    await run('ROLLBACK'); assert.deepEqual(await f.rows(), [])
    await sleep(50); assert.deepEqual(await f.rows(), [])
    // A later explicit new operation works; the failed operation was not replayed.
    await user.asterMutateBookmark('createOnly', { ...args, time: 55 })
    assert.deepEqual((await f.rows()).map(r => r.time), [55])
  } finally { await new Promise(resolve => locker.close(resolve)); await f.close() }
})
test('real SQLite: expired queued request refuses before its transaction', async () => {
  const f = await setup()
  try {
    const a = await f.user(), b = await f.user()
    let first = true
    f.User.addHook('afterSave', 'hold-first', async () => { if (first) { first = false; await sleep(2100) } })
    const results = await Promise.allSettled([a.asterMutateBookmark('createOnly', args),
      b.asterMutateBookmark('createOnly', { ...args, time: 55 })])
    assert.equal(results[0].status, 'fulfilled'); assert.equal(results[1].reason.code, 'bookmark_busy')
    assert.equal((await f.rows()).length, 1)
  } finally { await f.close() }
})
test('real SQLite: unsupported database dialect is refused, never downgraded', async () => {
  const f = await setup()
  try {
    const user = await f.user(), original = f.db.getDialect
    f.db.getDialect = () => 'unsupported'
    try { await rejectsStatus(user.asterMutateBookmark('createOnly', args), 503, 'bookmark_guard_unsupported') }
    finally { f.db.getDialect = original }
    assert.deepEqual(await f.rows(), [])
  } finally { await f.close() }
})
for (const journal of ['DELETE', 'WAL']) test('real SQLite: concurrent progress writes preserved in ' + journal + ' mode', async () => {
  const f = await setup(), g = await setup(f.filename)
  try {
    await f.db.query('PRAGMA journal_mode = ' + journal)
    class Progress extends Model {}
    Progress.init({ id: { type: DataTypes.STRING, primaryKey: true }, time: DataTypes.INTEGER }, { sequelize: g.db, modelName: 'synthetic_progress' })
    await Progress.sync(); await Progress.create({ id: 'listening', time: 0 })
    const users = await Promise.all(Array.from({ length: 20 }, () => f.user()))
    const start = performance.now()
    await Promise.all([
      ...users.map((u, i) => u.asterMutateBookmark('createOnly', { ...args, time: i })),
      (async () => { for (let i = 0; i < 50; i++) await Progress.increment('time', { by: 1, where: { id: 'listening' } }) })()
    ])
    assert.equal((await Progress.findByPk('listening')).time, 50)
    assert.equal((await f.rows()).length, 20)
    assert.ok(performance.now() - start < 10000, 'synthetic workload bounded')
  } finally { await g.close(); await f.close() }
})
function loadControllers(database, emitter) {
  const requireAddon = name => {
    if (name === '../Database') return database
    if (name === '../SocketAuthority') return emitter
    if (name === './asterBookmarkGuard') return guard
    throw Error('unexpected addon dependency ' + name)
  }
  const moduleAddon = { exports: {} }
  vm.runInNewContext(controllerAddon, { require: requireAddon, module: moduleAddon, Number, NaN })
  const moduleBase = { exports: {} }
  vm.runInNewContext(controllerSource, { module: moduleBase, require: name => {
    if (name === '../Database') return database
    if (name === '../SocketAuthority') return emitter
    if (name === '../libs/asterBookmarkGuard') return guard
    if (name === '../libs/asterBookmarkController') return moduleAddon.exports
    if (name === '../utils/index') return { isNullOrNaN: x => x === null || x === undefined || isNaN(x) }
    if (name === '../Logger') return { error() {}, warn() {} }
    return {}
  } })
  return moduleBase.exports
}
test('HTTP: auth/book access, create201, conflict409, precondition412 and legacy routes', async () => {
  const f = await setup()
  const controller = loadControllers({ libraryItemModel: { async getExpandedById(id) {
    if (id === 'missing') return null
    return { isBook: id !== 'podcast', id, media: { duration: 1000 } }
  } } }, { clientEmitter() {} })
  const server = http.createServer(async (req, out) => {
    let body = ''; for await (const chunk of req) body += chunk
    const [, item, action, time] = req.url.split('/')
    const user = req.headers.authorization ? await f.user() : undefined
    if (user) {
      user.isGuest = req.headers.authorization === 'guest'; user.isLocked = req.headers.authorization === 'locked'
      user.checkCanAccessLibraryItem = row => row.id !== 'denied'
      user.toOldJSONForBrowser = () => ({ bookmarks: user.bookmarks })
    }
    const request = { user, params: { id: item, time }, body: body ? JSON.parse(body) : {}, get: name => req.headers[name.toLowerCase()] }
    const response = { get headersSent() { return out.headersSent }, status(code) { out.statusCode = code; return this },
      set(name, value) { out.setHeader(name, value); return this }, json(data) { out.setHeader('Content-Type', 'application/json'); out.end(JSON.stringify(data)); return this },
      end() { out.end(); return this }, sendStatus(code) { out.statusCode = code; out.end(); return this } }
    const handler = { create: 'asterBookmarkCreateOnly', remove: 'asterBookmarkDeleteMatch', info: 'asterBookmarkCapabilities',
      legacycreate: 'createBookmark', legacyedit: 'updateBookmark', legacydelete: 'removeBookmark' }[action]
    if (!handler) return response.sendStatus(404)
    await controller[handler](request, response)
  })
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve))
  const base = 'http://127.0.0.1:' + server.address().port
  async function call(item, action, body, auth = 'synthetic', match) {
    return fetch(base + '/' + item + '/' + action + '/42', { method: body ? 'POST' : 'GET',
      headers: { ...(auth ? { Authorization: auth } : {}), ...(match ? { 'If-Match': match } : {}), 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined })
  }
  try {
    for (const auth of ['', 'guest', 'locked']) assert.equal((await call('book', 'create', args, auth)).status, 403)
    assert.equal((await call('denied', 'create', args)).status, 403)
    assert.equal((await call('missing', 'create', args)).status, 404)
    assert.equal((await call('podcast', 'create', args)).status, 400)
    assert.equal((await call('book', 'create', { time: 1001, title: 'Outside book' })).status, 400)
    assert.equal((await call('book', 'info')).status, 200)
    const created = await call('book', 'create', args)
    assert.equal(created.status, 201); const tag = created.headers.get('etag')
    assert.equal(created.headers.get('x-aster-bookmark-guard'), '1')
    const original = await created.json()
    assert.equal((await call('book', 'create', { ...args, title: 'Must not replace' })).status, 409)
    assert.deepEqual((await f.rows())[0], original)
    assert.equal((await call('book', 'remove', null)).status, 428)
    assert.equal((await call('book', 'legacyedit', { time: 42, title: 'Legacy edited' })).status, 200)
    assert.equal((await call('book', 'remove', null, 'synthetic', tag)).status, 412)
    assert.equal((await call('book', 'legacydelete')).status, 200)
    assert.equal((await call('book', 'legacydelete')).status, 404)
    const next = await call('book', 'create', args)
    assert.equal((await call('book', 'remove', null, 'synthetic', next.headers.get('etag'))).status, 204)
    assert.deepEqual(await f.rows(), [])
  } finally { await new Promise(resolve => server.close(resolve)); await f.close() }
})
