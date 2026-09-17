import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { defaultBattleTime, formatBattleTime, toLegacyActivityTimes } from './activityTime.mjs'

test('默认约战时间选择最近尚未错过的周二或周四 20:30', () => {
  assert.equal(defaultBattleTime(new Date(2026, 8, 14, 9, 0)), '2026-09-15T20:30:00')
  assert.equal(defaultBattleTime(new Date(2026, 8, 15, 20, 29)), '2026-09-15T20:30:00')
  assert.equal(defaultBattleTime(new Date(2026, 8, 15, 20, 31)), '2026-09-17T20:30:00')
  assert.equal(defaultBattleTime(new Date(2026, 8, 16, 12, 0)), '2026-09-17T20:30:00')
  assert.equal(defaultBattleTime(new Date(2026, 8, 17, 20, 30)), '2026-09-17T20:30:00')
  assert.equal(defaultBattleTime(new Date(2026, 8, 17, 20, 31)), '2026-09-22T20:30:00')
  assert.equal(defaultBattleTime(new Date(2026, 8, 18, 9, 0)), '2026-09-22T20:30:00')
})

test('创建界面只提交约战时间，内部生成旧接口兼容字段', () => {
  assert.deepEqual(toLegacyActivityTimes('2026-09-17T20:30:00'), {
    startsAt: '2026-09-17T20:30:00',
    endsAt: '2026-09-17T22:30:00'
  })
  assert.throws(() => toLegacyActivityTimes(''), /请选择约战时间/)
})

test('列表和详情只格式化一个约战时间', () => {
  assert.equal(formatBattleTime('2026-09-17T20:30:00'), '2026-09-17 20:30')
  assert.equal(formatBattleTime(''), '时间未设置')
})

test('创建弹窗和活动展示不再出现开始时间与结束时间', () => {
  const schedule = fs.readFileSync(new URL('./ScheduleEntry.vue', import.meta.url), 'utf8')
  const list = fs.readFileSync(new URL('./ListView.vue', import.meta.url), 'utf8')
  const detail = fs.readFileSync(new URL('./detail.vue', import.meta.url), 'utf8')
  assert.match(schedule, /<FieldLabel[^>]*>约战时间<\/FieldLabel>/)
  assert.doesNotMatch(schedule, />开始时间<|>结束时间</)
  assert.doesNotMatch(list, /a\.endsAt/)
  assert.doesNotMatch(detail, /activity\.endsAt/)
})
