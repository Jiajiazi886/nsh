import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const source = fs.readFileSync(new URL('./ListView.vue', import.meta.url), 'utf8')
const css = fs.readFileSync(new URL('./activity.css', import.meta.url), 'utf8')

test('public battle page has a dedicated filter bar and responsive card grid', () => {
  for (const marker of ['battle-public-toolbar', 'battle-public-grid', 'battle-public-card', 'battle-public-stats', 'battle-public-shortages']) {
    assert.match(source, new RegExp(marker))
    assert.match(css, new RegExp(`\\.${marker}`))
  }
  assert.match(source, /查看并报名/)
  assert.match(source, /清除筛选/)
})
