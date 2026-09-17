import test from 'node:test'
import assert from 'node:assert/strict'
import { addBattleInformationMenus } from './battleInformationMenus.mjs'

test('guild omits Find Battles while personal keeps it and history is renamed', () => {
  const routes = [{ path: '/guild', children: [] }, { path: '/personal', children: [] }]

  addBattleInformationMenus(routes)
  addBattleInformationMenus(routes)

  assert.ok(routes.every(route => route.children.length === 1), 'menu injection must be idempotent')
  const guildChildren = routes[0].children[0].children
  const personalChildren = routes[1].children[0].children
  assert.deepEqual(guildChildren.map(route => route.path), ['mine', 'history'])
  assert.deepEqual(personalChildren.map(route => route.path), ['mine', 'public', 'history'])
  assert.ok(!guildChildren.some(route => route.meta.title === '找约战'))
  assert.equal(personalChildren.find(route => route.path === 'history').meta.title, '历史约战')
  assert.ok(!JSON.stringify(routes).includes('schedule:edit'))
})
