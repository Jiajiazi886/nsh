import {readFileSync} from 'node:fs'
import {test} from 'node:test'
import assert from 'node:assert/strict'
test('stable activity editor works independently of nested legacy menu paths',()=>{
  const source=readFileSync(new URL('./index.js',import.meta.url),'utf8')
  assert.match(source,/path:\s*['"]\/guild\/schedule['"]/)
  assert.match(source,/name:\s*['"]ActivityLineupEditor['"]/)
  assert.match(source,/import\(['"]@\/views\/guild\/schedule\/index.vue['"]\)/)
})
