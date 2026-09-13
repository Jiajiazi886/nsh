import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  buildScheduleBoxes, collectLegacyMembers, groupPlayersByClass,
  readTempMembers, withTempMembers, withTempAssignment, withoutTempAssignment,
  pruneTempAssignments, remapTempAssignments
} from './scheduleBoxes.js'
import { withTeamManagementRoute } from '../../../../store/modules/guildGroupRoutes.js'

const fixture = () => ({ schedule_id: 1, teams: [{
  team_id: 10, team_name: '进攻一团', order_num: 1, squads: [{
    squad_id: 20, squad_name: '一队', order_num: 1, max_members: 6,
    members: [{ member_id: 7, player_name: '玩家甲', player_class: '铁衣', order_num: 3 }]
  }]
}] })
const temporary = { member_id: 'temp_a', player_name: '替补甲', player_class: '素问', is_temporary: true }

test('六个位置按 order_num 构造，不按数组下标；团没有直属玩家', () => {
  const data = fixture()
  const boxes = buildScheduleBoxes(data, {})
  assert.equal(boxes[0].squads[0].seats.length, 6)
  assert.equal(boxes[0].squads[0].seats[2].member.member_id, 7)
  assert.equal(boxes[0].squads[0].seats[0].member, null)
  assert.equal(boxes[0].count, 1)
  assert.equal('members' in boxes[0], false)
  assert.equal(data.teams[0].squads[0].members.length, 1)
})

test('旧超员、非法或重复位置不会静默丢失', () => {
  const data = fixture()
  data.teams[0].squads[0].max_members = 12
  data.teams[0].squads[0].members.push(
    { member_id: 8, player_name: '超员', order_num: 7 },
    { member_id: 9, player_name: '重复位置', order_num: 3 },
    { member_id: 11, player_name: '坏位置', order_num: 0 }
  )
  const squad = buildScheduleBoxes(data, {})[0].squads[0]
  assert.equal(squad.seats.length, 6)
  assert.deepEqual(squad.overflow.map(m => m.member_id), [8, 9, 11])
  assert.equal(squad.count, 4)
})

test('临时名单和位置通过元数据保存，保留原 workbook 的全部内容', () => {
  const old = { sheets: { sheet1: { cellData: {} } }, styles: { s: {} }, custom: { other: '保留' } }
  const listed = withTempMembers(old, [temporary])
  const next = withTempAssignment(listed, fixture(), temporary, 10, 20, 4)
  assert.deepEqual(next.sheets, old.sheets)
  assert.deepEqual(next.styles, old.styles)
  assert.equal(next.custom.other, '保留')
  assert.equal(old.custom.guildScheduleTempMembers, undefined)
  assert.equal(readTempMembers(next)[0].member_id, 'temp_a')
  const squad = buildScheduleBoxes(fixture(), next)[0].squads[0]
  assert.equal(squad.seats[3].member.member_id, 'temp_a')
  assert.equal(squad.count, 2)
})

test('非法位置和占位拒绝；失败不污染旧对象', () => {
  const old = withTempMembers({}, [temporary])
  assert.throws(() => withTempAssignment(old, fixture(), temporary, 10, 20, 7), /位置/)
  assert.throws(() => withTempAssignment(old, fixture(), temporary, 10, 20, 3), /已有/)
  assert.throws(() => withTempAssignment(old, fixture(), temporary, 10, 999, 1), /小队/)
  assert.equal(old.custom.guildScheduleBoxes, undefined)
})

test('移动临时玩家只占一个位置，清除不删除名单', () => {
  const original = withTempAssignment(withTempMembers({}, [temporary]), fixture(), temporary, 10, 20, 2)
  const moved = withTempAssignment(original, fixture(), temporary, 10, 20, 5)
  assert.equal(moved.custom.guildScheduleBoxes.tempAssignments.length, 1)
  assert.equal(buildScheduleBoxes(fixture(), moved)[0].squads[0].seats[1].member, null)
  const cleared = withoutTempAssignment(moved, temporary.member_id)
  assert.equal(buildScheduleBoxes(fixture(), cleared)[0].count, 1)
  assert.equal(readTempMembers(cleared).length, 1)
})

test('删除小队后的临时位置清理，不删除替补名单/旧表格', () => {
  const old = withTempAssignment(withTempMembers({ custom: { other: 1 } }, [temporary]), fixture(), temporary, 10, 20, 2)
  const empty = fixture()
  empty.teams[0].squads = []
  const next = pruneTempAssignments(old, empty)
  assert.equal(next.custom.guildScheduleBoxes.tempAssignments.length, 0)
  assert.equal(readTempMembers(next).length, 1)
  assert.equal(next.custom.other, 1)
})

test('恢复快照后的新 ID 通过唯一结构锚点重映射，刷新仍能读取', () => {
  const old = withTempAssignment(withTempMembers({}, [temporary]), fixture(), temporary, 10, 20, 2)
  const restored = fixture()
  restored.schedule_id = 2
  restored.teams[0].team_id = 110
  restored.teams[0].squads[0].squad_id = 120
  const next = remapTempAssignments(old, restored)
  assert.equal(next.custom.guildScheduleBoxes.tempAssignments[0].teamId, 110)
  assert.equal(next.custom.guildScheduleBoxes.tempAssignments[0].squadId, 120)
  assert.equal(buildScheduleBoxes(restored, next)[0].squads[0].seats[1].member.member_id, 'temp_a')
})

test('不能唯一映射、成员不存在或正式玩家已占位时不制造假分配', () => {
  const old = withTempAssignment(withTempMembers({}, [temporary]), fixture(), temporary, 10, 20, 2)
  const changed = fixture()
  changed.teams[0].team_id = 110
  changed.teams[0].squads[0].squad_id = 120
  changed.teams[0].squads[0].members.push({ member_id: 99, order_num: 2 })
  const next = remapTempAssignments(old, changed)
  assert.equal(buildScheduleBoxes(changed, next)[0].count, 2)
  assert.equal(next.custom.guildScheduleBoxes.tempAssignments.length, 0)
  assert.equal(readTempMembers(next).length, 1)
})

test('结构锚点重复时不任意挑选一个小队，名单保留待安排', () => {
  const old = withTempAssignment(withTempMembers({}, [temporary]), fixture(), temporary, 10, 20, 2)
  const restored = fixture()
  restored.teams[0].team_id = 110
  restored.teams[0].squads[0].squad_id = 120
  restored.teams[0].squads.push({ ...restored.teams[0].squads[0], squad_id: 121 })
  const next = remapTempAssignments(old, restored)
  assert.equal(next.custom.guildScheduleBoxes.tempAssignments.length, 0)
  assert.equal(readTempMembers(next).length, 1)
  assert.equal(old.custom.guildScheduleBoxes.tempAssignments.length, 1)
})

test('旧表格玩家可收集并去重，多页内容不丢失，已有分配不重复显示', () => {
  const workbook = { sheets: { a: { cellData: { 1: { 1: { v: '甲', custom: { member_id: 7, player_name: '甲' } } } } },
    b: { cellData: { 2: { 1: { v: '替补甲', custom: temporary }, 2: { v: '替补甲', custom: temporary } } } } } }
  const legacy = collectLegacyMembers(workbook, fixture())
  assert.deepEqual(legacy.map(m => m.member_id), ['temp_a'])
})

test('职业树归类，未知职业和未设置职业也保留', () => {
  const groups = groupPlayersByClass([
    { member_id: 1, player_class: '素问' }, { member_id: 2, player_class: '铁衣' },
    { member_id: 3, player_class: '素问' }, { member_id: 4 }, { member_id: 5, player_class: '未来职业' }
  ])
  assert.equal(groups.find(g => g.className === '素问').members.length, 2)
  assert.equal(groups.flatMap(g => g.members).length, 5)
  assert.ok(groups.find(g => g.className === '未设置'))
})

test('旧附加名单格式错误不导致页面崩溃', () => {
  assert.deepEqual(readTempMembers({ custom: { guildScheduleTempMembers: { invalid: true } } }), [])
})

test('旧临时 ID 即使缺少标志也识别为临时玩家，不传给正式分配接口', () => {
  const workbook = { sheets: { a: { cellData: { 1: { 1: { custom: { member_id: 'temp_old', player_name: '旧临时' } } } } } } }
  assert.equal(collectLegacyMembers(workbook, fixture())[0].is_temporary, true)
})

test('团队管理只插入可见分团父节点，独立同级占位页面，不改输入路由', () => {
  const source = [{ path: 'guild', children: [{ path: 'group', component: 'ParentView', meta: { title: '分团管理' }, children: [
    { path: 'schedule', name: 'Schedule', component: 'guild/schedule/index', meta: { title: '约战排表' } }
  ] }] }]
  const next = withTeamManagementRoute(source)
  assert.equal(source[0].children[0].children.length, 1)
  const children = next[0].children[0].children
  assert.equal(children[0].meta.title, '团队管理')
  assert.equal(children[0].component, 'guild/teamManagement/index')
  assert.equal(children[1].component, 'guild/schedule/index')
  assert.equal(withTeamManagementRoute(next)[0].children[0].children.length, 2)
})

test('没有分团/排表权限的菜单不增加入口，隐藏父节点不补菜单', () => {
  assert.deepEqual(withTeamManagementRoute([{ path: 'guild', children: [] }]), [{ path: 'guild', children: [] }])
  const hidden = [{ path: 'group', component: 'ParentView', hidden: true, meta: { title: '分团管理' }, children: [{ component: 'guild/schedule/index' }] }]
  assert.equal(withTeamManagementRoute(hidden)[0].children.length, 1)
})
