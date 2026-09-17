import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const source = fs.readFileSync(new URL('./ListView.vue', import.meta.url), 'utf8')

test('history page only lists activities and has no legacy unlinked-report region', () => {
  assert.doesNotMatch(source, /战报记录（含未关联旧战报）|loadReports|reportTotal|reportPage|reportDialog/)
  assert.match(source, /历史约战/)
  assert.match(source, /上传 CSV/)
})

test('my battles is compact and does not render report status', () => {
  assert.match(source, /battle-compact-card/)
  assert.match(source, /participatingOnly/)
  assert.doesNotMatch(source, /已有战报|暂无战报数据/)
  assert.doesNotMatch(source, /创建俱乐部/)
  assert.doesNotMatch(source, /缺 \{\{ count \}\}/)
})
