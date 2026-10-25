'use strict'
// Child process for synthetic SQLite contention tests; never a deployment tool.
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm')
const { Sequelize, Model, DataTypes } = require('sequelize')
const guard = require('./asterBookmarkGuard')
let db, User
process.on('message', async message => {
  try {
    if (message.kind === 'init') {
      db = new Sequelize({ dialect: 'sqlite', storage: message.filename, logging: false, retry: { max: 0 } })
      User = class extends Model {}
      User.init({ id: { type: DataTypes.STRING, primaryKey: true }, bookmarks: DataTypes.JSON,
        username: DataTypes.STRING, token: DataTypes.STRING, outside: DataTypes.STRING }, { sequelize: db, modelName: 'user' })
      const source = fs.readFileSync(path.join(message.candidate, 'payload/server/models/User.js'), 'utf8')
      const names = ['asterMutateBookmark', 'createBookmark', 'updateBookmark', 'removeBookmark']
      const methods = names.map(name => source.match(new RegExp('  async ' + name + '\\([^)]*\\) \\{\\n[\\s\\S]*?\\n  \\}'))[0]).join('\n')
      const patched = vm.runInNewContext('(class extends Model {\n' + methods + '\n})', { Model,
        userCache: { delete() {} }, require: () => guard })
      for (const name of names) User.prototype[name] = patched.prototype[name]
      // Both processes hold an independently loaded stale request instance.
      User.request = await User.findByPk('household')
      process.send({ kind: 'ready' })
    } else if (message.kind === 'go') {
      try {
        await User.request.asterMutateBookmark('createOnly', { item: 'book', time: 42, title: message.title })
        process.send({ kind: 'result', status: 201 })
      } catch (error) { process.send({ kind: 'result', status: error.status || 500, code: error.code || 'failed' }) }
      await db.close(); process.disconnect()
    }
  } catch { process.send({ kind: 'failed' }); if (db) await db.close(); process.disconnect() }
})
