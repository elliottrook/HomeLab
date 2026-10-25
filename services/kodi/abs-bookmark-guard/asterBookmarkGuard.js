'use strict'
// Aster-owned overlay. No source DB/config is read by the local test harness.
const crypto = require('node:crypto')
const { performance } = require('node:perf_hooks')
class GuardError extends Error {
  constructor(status, code) { super(code); this.status = status; this.code = code }
}
const fail = (status, code) => { throw new GuardError(status, code) }
const queues = new WeakMap()
async function exclusive(db, work) {
  let queue = queues.get(db)
  if (!queue) { queue = { tail: Promise.resolve(), count: 0 }; queues.set(db, queue) }
  if (queue.count >= 32) fail(503, 'bookmark_busy')
  queue.count++
  const enqueued = performance.now()
  const previous = queue.tail
  let release
  queue.tail = new Promise(resolve => { release = resolve })
  try { await previous; if (performance.now() - enqueued > 2000) fail(503, 'bookmark_busy'); return await work() }
  finally { queue.count--; release() }
}
function etag(account, row) {
  return '"' + crypto.createHash('sha256').update(JSON.stringify([
    account, row.libraryItemId, row.time, row.title, row.createdAt, row.asterGuardGeneration || null
  ])).digest('hex') + '"'
}
function validate(operation, args) {
  if (!args || typeof args.item !== 'string' || !/^[A-Za-z0-9_-]{1,128}$/.test(args.item)) fail(400, 'invalid_bookmark_item')
  if (!Number.isFinite(Number(args.time)) || Number(args.time) < 0) fail(400, 'invalid_bookmark_time')
  if (operation === 'createOnly' || operation === 'deleteMatch') {
    if (!Number.isSafeInteger(args.time) || args.time > 604800) fail(400, 'invalid_bookmark_time')
  }
  if (['createOnly', 'createLegacy', 'updateLegacy'].includes(operation) &&
      (typeof args.title !== 'string' || !args.title.length)) fail(400, 'invalid_bookmark_title')
  if (operation === 'createOnly' && (args.title.length > 160 || /[\x00-\x1f\x7f]/.test(args.title))) fail(400, 'invalid_bookmark_title')
  if (operation === 'deleteMatch' && (typeof args.match !== 'string' || !/^"[0-9a-f]{64}"$/.test(args.match))) fail(428, 'bookmark_precondition_required')
}
function change(account, source, operation, args, now = Date.now, generation = () => crypto.randomBytes(16).toString('hex')) {
  validate(operation, args)
  if (!Array.isArray(source) || source.length > 10000 || source.some(row => !row || typeof row !== 'object')) fail(503, 'bookmark_state_unavailable')
  const rows = source.map(row => ({ ...row }))
  const matches = rows.filter(row => row.libraryItemId === args.item && Number(row.time) === Number(args.time))
  if (matches.length > 1) fail(409, 'bookmark_identity_ambiguous')
  const current = matches[0]
  if (operation === 'createOnly' && current) fail(409, 'bookmark_already_exists')
  if (operation === 'deleteMatch') {
    if (!current) fail(404, 'bookmark_not_found')
    if (etag(account, current) !== args.match) fail(412, 'bookmark_changed')
  }
  if (operation === 'deleteMatch' || operation === 'deleteLegacy') {
    return { rows: rows.filter(row => row !== current), value: !!current, changed: !!current }
  }
  if (operation === 'updateLegacy' && !current) return { rows, value: null, changed: false }
  if (!['createOnly', 'createLegacy', 'updateLegacy'].includes(operation)) fail(400, 'invalid_bookmark_operation')
  if (current) {
    const changed = current.title !== args.title
    if (changed) { current.title = args.title; current.asterGuardGeneration = generation() }
    return { rows, value: { ...current }, changed }
  }
  const created = { libraryItemId: args.item, time: Number(args.time), title: args.title,
    createdAt: now(), asterGuardGeneration: generation() }
  rows.push(created)
  return { rows, value: { ...created }, changed: true }
}
async function mutate(user, operation, args) {
  validate(operation, args)
  const Model = user.constructor, db = Model.sequelize
  if (!db || db.getDialect() !== 'sqlite') fail(503, 'bookmark_guard_unsupported')
  try {
    return await exclusive(db, async () => {
      const outcome = await db.transaction({ type: 'IMMEDIATE', retry: { max: 0 } }, async transaction => {
        const fresh = await Model.findByPk(user.id, { attributes: ['id', 'bookmarks'], transaction })
        if (!fresh) fail(404, 'bookmark_user_not_found')
        const result = change(user.id, fresh.bookmarks, operation, args)
        if (result.changed) {
          fresh.setDataValue('bookmarks', result.rows); fresh.changed('bookmarks', true)
          await fresh.save({ fields: ['bookmarks'], silent: true, transaction, retry: { max: 0 } })
        }
        return result
      })
      // Refresh just this request instance; never save stale profile/progress fields.
      user.setDataValue('bookmarks', outcome.rows); user.changed('bookmarks', false)
      return { value: outcome.value, etag: outcome.value && typeof outcome.value === 'object' ? etag(user.id, outcome.value) : null }
    })
  } catch (error) {
    if (error instanceof GuardError) throw error
    const code = error.original?.code || error.parent?.code || error.code
    fail(code === 'SQLITE_BUSY' || code === 'SQLITE_LOCKED' ? 503 : 500,
      code === 'SQLITE_BUSY' || code === 'SQLITE_LOCKED' ? 'bookmark_busy' : 'bookmark_guard_failed')
  }
}
async function respond(res, work) {
  try { return await work() }
  catch (error) {
    if (res.headersSent) return
    return res.set('Cache-Control', 'no-store').status(error instanceof GuardError ? error.status : 500)
      .json({ error: error instanceof GuardError ? error.code : 'bookmark_guard_failed' })
  }
}
module.exports = { GuardError, change, mutate, etag, respond }
