const test = require('node:test')
const assert = require('node:assert/strict')

const { derivePlayerOverrides, buildRoleTree } = require('../utils/box-selection')

test('玩家选择保存为相对已选小队的手动增减差异', () => {
  const result = derivePlayerOverrides(
    ['team_player_1', 'team_player_2'],
    ['team_player_2', 'free_player_1']
  )

  assert.deepEqual(result.manualAddIds, ['free_player_1'])
  assert.deepEqual(result.manualRemoveIds, ['team_player_1'])
})

test('玩家按职业构建为可展开的树，并保留职业出现顺序', () => {
  const tree = buildRoleTree([
    { pid: 'p1', name: '甲', role: '铁衣', checked: true },
    { pid: 'p2', name: '乙', role: '神相', checked: false },
    { pid: 'p3', name: '丙', role: '铁衣', checked: false }
  ], '', { 铁衣: false })

  assert.deepEqual(tree.map(item => item.role), ['铁衣', '神相'])
  assert.equal(tree[0].expanded, false)
  assert.equal(tree[0].count, 2)
  assert.equal(tree[0].checkedCount, 1)
  assert.deepEqual(tree[0].players.map(player => player.pid), ['p1', 'p3'])
})

test('职业搜索展示整组玩家，玩家名搜索只展示命中玩家', () => {
  const players = [
    { pid: 'p1', name: '家猫素问', role: '素问', checked: true },
    { pid: 'p2', name: '桃姿素问', role: '素问', checked: false },
    { pid: 'p3', name: '封不觉', role: '龙吟', checked: true }
  ]

  const byRole = buildRoleTree(players, '素问', {})
  assert.equal(byRole.length, 1)
  assert.deepEqual(byRole[0].players.map(player => player.pid), ['p1', 'p2'])

  const byName = buildRoleTree(players, '桃姿', {})
  assert.equal(byName.length, 1)
  assert.deepEqual(byName[0].players.map(player => player.pid), ['p2'])
})
