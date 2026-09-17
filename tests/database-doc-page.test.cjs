const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')

const root = 'E:/nsh/nshls/html'

function loadData() {
  const window = {}
  vm.runInNewContext(fs.readFileSync(`${root}/assets/database-data.js`, 'utf8'), { window })
  return window.DATABASE_DOC
}

test('数据库说明站点包含独立页面和可维护资源', () => {
  const index = fs.readFileSync(`${root}/index.html`, 'utf8')
  const database = fs.readFileSync(`${root}/database.html`, 'utf8')
  assert.match(index, /href="database\.html"/)
  assert.match(index, /数据库说明/)
  assert.match(database, /assets\/database\.css/)
  assert.match(database, /assets\/database-data\.js/)
  assert.match(database, /assets\/database\.js/)
  assert.match(database, /核心业务关系图/)
  assert.match(database, /全部 56 张表/)
})

test('数据库只读快照的表数、分类和行数保持一致', () => {
  const doc = loadData()
  assert.equal(doc.snapshot.database, 'nsh_activity_dev_20260914')
  assert.equal(doc.tables.length, 56)
  assert.equal(new Set(doc.tables.map((table) => table.name)).size, 56)
  assert.equal(doc.tables.some((table) => table.name === 'guild_info'), false)
  assert.equal(doc.tables.some((table) => table.name === 'guild_review'), false)
  assert.equal(doc.tables.reduce((sum, table) => sum + table.rows, 0), doc.snapshot.rowCount)
  for (const group of doc.groups) {
    const tables = doc.tables.filter((table) => table.group === group.id)
    assert.equal(tables.length, group.count, `${group.name} 表数量不一致`)
    assert.equal(tables.reduce((sum, table) => sum + table.rows, 0), group.rows, `${group.name} 行数不一致`)
  }
})

test('核心账号、活动、快照、报名和战报表具有字段说明', () => {
  const doc = loadData()
  const required = [
    'sys_user',
    'integration_account_player_profile',
    'integration_organization',
    'integration_activity',
    'integration_activity_snapshot',
    'integration_activity_participation',
    'guild_member',
    'integration_activity_report'
  ]
  for (const name of required) {
    assert.ok(doc.tables.some((table) => table.name === name), `${name} 不在表清单中`)
    assert.ok(doc.coreSchemas[name]?.fields.length, `${name} 缺少核心字段说明`)
  }
})
