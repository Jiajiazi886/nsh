import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const source = fs.readFileSync(new URL('./index.vue', import.meta.url), 'utf8')

test('guild information keeps one member summary and count-only profession rows', () => {
  assert.equal((source.match(/>帮会成员</g) || []).length, 1)
  assert.doesNotMatch(source, /职业数量|人数最多职业|getClassPercent|class-bar/)
  assert.match(source, /item\.count \}\} 人/)
  assert.doesNotMatch(source, /\}\}%/)
})

test('guild information composes local shadcn-vue components', () => {
  assert.match(source, /@\/components\/ui\/card/)
  assert.match(source, /@\/components\/ui\/accordion/)
  assert.match(source, /@\/components\/ui\/button/)
})
