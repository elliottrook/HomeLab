'use strict'
const Database = require('../Database')
const SocketAuthority = require('../SocketAuthority')
const guard = require('./asterBookmarkGuard')
async function book(req) {
  if (!req.user || req.user.isGuest || req.user.isLocked) throw new guard.GuardError(403, 'bookmark_access_denied')
  if (typeof req.params.id !== 'string' || !/^[A-Za-z0-9_-]{1,128}$/.test(req.params.id)) throw new guard.GuardError(400, 'invalid_bookmark_item')
  const item = await Database.libraryItemModel.getExpandedById(req.params.id)
  if (!item) throw new guard.GuardError(404, 'bookmark_item_not_found')
  if (!req.user.checkCanAccessLibraryItem(item)) throw new guard.GuardError(403, 'bookmark_access_denied')
  if (item.isBook !== true) throw new guard.GuardError(400, 'bookmark_books_only')
  return item
}
async function capabilities(req, res) {
  return guard.respond(res, async () => {
    await book(req)
    return res.set('Cache-Control', 'no-store').json({ protocol: 'aster-bookmark-guard.v1', createOnly: true, conditionalDelete: true })
  })
}
async function createOnly(req, res) {
  return guard.respond(res, async () => {
    const item = await book(req)
    const time = req.body?.time, title = req.body?.title
    const duration = item.media?.duration
    if (!Number.isFinite(duration) || duration <= 0) throw new guard.GuardError(503, 'bookmark_duration_unavailable')
    if (!Number.isSafeInteger(time) || time < 0 || time >= duration) throw new guard.GuardError(400, 'invalid_bookmark_time')
    const result = await req.user.asterMutateBookmark('createOnly', { item: req.params.id, time, title })
    SocketAuthority.clientEmitter(req.user.id, 'user_updated', req.user.toOldJSONForBrowser())
    return res.set('Cache-Control', 'no-store').set('ETag', result.etag).set('X-Aster-Bookmark-Guard', '1').status(201).json(result.value)
  })
}
async function deleteMatch(req, res) {
  return guard.respond(res, async () => {
    await book(req)
    const time = /^\d+$/.test(req.params.time || '') ? Number(req.params.time) : NaN
    await req.user.asterMutateBookmark('deleteMatch', { item: req.params.id, time, match: req.get('If-Match') })
    SocketAuthority.clientEmitter(req.user.id, 'user_updated', req.user.toOldJSONForBrowser())
    return res.set('Cache-Control', 'no-store').set('X-Aster-Bookmark-Guard', '1').status(204).end()
  })
}
module.exports = { capabilities, createOnly, deleteMatch }
