import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const list = fs.readFileSync(new URL('./ListView.vue', import.meta.url), 'utf8')
const schedule = fs.readFileSync(new URL('./ScheduleEntry.vue', import.meta.url), 'utf8')

test('activity creation exists only in the lineup schedule entry', () => {
  assert.doesNotMatch(list, /创建约战|openCreate|createActivity|createVisible/)
  assert.match(schedule, /创建约战/)
  assert.match(schedule, /activityApi\.createActivity/)
  assert.match(schedule, /创建并配置排表/)
})
