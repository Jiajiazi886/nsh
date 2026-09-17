import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const source = fs.readFileSync(new URL('./LineupEditor.vue', import.meta.url), 'utf8')

test('candidate professions use one animated accordion and remaining over total counts', () => {
  assert.match(source, /<Accordion[^>]+type="single"[^>]+collapsible/)
  assert.match(source, /folder\.remaining\s*\}\}\s*\/\s*\{\{\s*folder\.total/)
  assert.doesNotMatch(source, /<details/)
})

test('manager lineup exposes the automatic leave link and leave records', () => {
  assert.match(source, /复制请假链接/)
  assert.match(source, /请假名单/)
  assert.match(source, /activityLeaves/)
  assert.match(source, /activityProfiles\(props\.activity\.orgId,\s*props\.activity\.activityId\)/)
})

test('a new activity defaults to the latest saved organization lineup and can choose history', () => {
  assert.match(source, /activityLineupTemplates/)
  assert.match(source, /历史排表/)
  assert.match(source, /templates\.value\[0\]/)
  assert.match(source, /sanitizeTemplateTeams/)
})
