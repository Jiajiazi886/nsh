import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const router = fs.readFileSync(new URL('../../router/index.js', import.meta.url), 'utf8')
const dashboard = fs.readFileSync(new URL('../dashboard/index.vue', import.meta.url), 'utf8')

test('legacy group and review interfaces are no longer routed or shown', () => {
  assert.doesNotMatch(router, /GuildTeam|views\/guild\/team|title:\s*['"]分团管理/)
  assert.doesNotMatch(dashboard, /约战审核|创建报名链接|guild\/review/)
  assert.match(dashboard, /约战排表/)
  assert.match(dashboard, /历史约战/)
})

test('retired workbook group-schedule implementation is removed from the production tree', () => {
  for (const relative of [
    './schedule/components/ScheduleBoxes.vue',
    './schedule/components/ScheduleUniverSheet.vue',
    './schedule/components/ScheduleWorkbookTable.vue',
    './schedule/utils/scheduleBoxes.js',
    './schedule/utils/scheduleDraft.js',
    './schedule/utils/scheduleDraftSync.js',
    './schedule/utils/scheduleWorkbook.js',
  ]) {
    assert.equal(fs.existsSync(new URL(relative, import.meta.url)), false, `旧排表文件仍存在：${relative}`)
  }
})
