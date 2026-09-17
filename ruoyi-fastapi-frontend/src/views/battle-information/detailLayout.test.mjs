import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const source = fs.readFileSync(new URL('./detail.vue', import.meta.url), 'utf8')

test('activity detail uses direct CSV import and no manual report-id dialog', () => {
  assert.match(source, /上传 CSV/)
  assert.match(source, /BattleCsvImport/)
  assert.doesNotMatch(source, /关联已有 CSV 战报|请输入已有 CSV 战报 ID|const reportId|v-model="reportId"|linkReport/)
})

test('activity detail has compact summary, action, lineup and report regions', () => {
  for (const className of ['battle-detail-head', 'battle-detail-summary', 'battle-detail-actions', 'battle-detail-lineup', 'battle-detail-reports']) {
    assert.match(source, new RegExp(className))
  }
})

test('expired historical activities do not offer publish or lineup editing actions', () => {
  assert.match(source, /activity\.canManage && activity\.state !== 'ended' && !activity\.isPublic && activity\.snapshot/)
  assert.match(source, /<Button v-if="activity\.canManage && activity\.state !== 'ended'"[^>]*@click="openLineup">配置排表/)
})
