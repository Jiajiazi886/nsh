import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const page = fs.readFileSync(new URL('./index.vue', import.meta.url), 'utf8')
const router = fs.readFileSync(new URL('../../../router/index.js', import.meta.url), 'utf8')

test('public leave page is a dedicated simple mobile flow with a second confirmation', () => {
  assert.match(router, /\/public\/activity-leave\/:leaveCode/)
  assert.match(page, /activityLeaveMembers/)
  assert.match(page, /submitActivityLeave/)
  assert.match(page, /搜索玩家名字/)
  assert.match(page, /可选：请假说明/)
  assert.match(page, /AlertDialog/)
  assert.match(page, /确认请假/)
  assert.match(page, /role="status"/)
  assert.doesNotMatch(page, /window\.alert/)
  assert.doesNotMatch(page, /注册|登录|报名/)
})
