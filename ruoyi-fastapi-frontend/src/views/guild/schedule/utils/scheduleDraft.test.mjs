import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  createScheduleDraft, addDraftTeam, addDraftSquad, removeDraftStructure,
  assignDraftPlayer, clearDraftPlayer, upsertDraftTempMember, loadHistoryIntoDraft,
  createDraftAutosaver, scheduleFingerprint, validateScheduleDraft
} from './scheduleDraft.js'
import { syncScheduleDraft } from './scheduleDraftSync.js'
import { buildScheduleBoxes } from './scheduleBoxes.js'
import { draftStorageKey } from './scheduleDraftDb.js'

const clone = value => JSON.parse(JSON.stringify(value))
const player = (id, name = `玩家${id}`) => ({ member_id: id, player_name: name, player_class: '铁衣' })
const fixture = () => ({ schedule_id: 1, teams: [{ team_id: 10, team_name: '进攻团', order_num: 1,
  squads: [{ squad_id: 20, squad_name: '一队', order_num: 1, max_members: 6, members: [{ ...player(7), order_num: 1 }] }] }] })
const temp = { ...player('temp_a', '临时替补'), is_temporary: true }

test('本地创建/删除和分配不改输入，不需要任何 API；每小队六位置', () => {
  const source = createScheduleDraft(fixture(), { custom: { keep: 1 } })
  let next = addDraftTeam(source, '防守团', 'local_team_a')
  next = addDraftSquad(next, 'local_team_a', '二队', 'local_squad_a')
  next = assignDraftPlayer(next, player(8), 'local_team_a', 'local_squad_a', 6)
  assert.equal(next.dirty, true)
  assert.equal(source.schedule.teams.length, 1)
  assert.equal(buildScheduleBoxes(next.schedule, next.workbook)[1].squads[0].seats.length, 6)
  next = removeDraftStructure(next, 'local_team_a')
  assert.equal(next.schedule.teams.length, 1)
  assert.equal(next.workbook.custom.keep, 1)
})

test('正式玩家本地移动和交换，位置占用拒绝且输入不污染', () => {
  const initial = createScheduleDraft(fixture(), {})
  let next = assignDraftPlayer(initial, player(8), 10, 20, 2)
  next = assignDraftPlayer(next, player(7), 10, 20, 2)
  const seats = buildScheduleBoxes(next.schedule, next.workbook)[0].squads[0].seats
  assert.equal(seats[0].member.member_id, 8)
  assert.equal(seats[1].member.member_id, 7)
  assert.throws(() => assignDraftPlayer(next, player(9), 10, 20, 2), /已有/)
  assert.throws(() => assignDraftPlayer(next, player(9), 10, 20, 7), /位置/)
  assert.equal(initial.schedule.teams[0].squads[0].members.length, 1)
})

test('临时替补和正式玩家在本地可交换，移出/删除小队不删临时名单或旧 workbook', () => {
  const wb = { sheets: { old: {} }, custom: { keep: '保留' } }
  let draft = upsertDraftTempMember(createScheduleDraft(fixture(), wb), temp)
  draft = assignDraftPlayer(draft, temp, 10, 20, 2)
  draft = assignDraftPlayer(draft, player(7), 10, 20, 2)
  const seats = buildScheduleBoxes(draft.schedule, draft.workbook)[0].squads[0].seats
  assert.equal(seats[0].member.member_id, 'temp_a')
  assert.equal(seats[1].member.member_id, 7)
  draft = clearDraftPlayer(draft, 7)
  draft = removeDraftStructure(draft, 10, 20)
  assert.equal(draft.workbook.custom.guildScheduleTempMembers.length, 1)
  assert.equal(draft.workbook.custom.guildScheduleBoxes.tempAssignments.length, 0)
  assert.deepEqual(draft.workbook.sheets, wb.sheets)
  assert.equal(draft.workbook.custom.keep, '保留')
})

test('六人限制、重复成员、非法配置在提交前阻止；旧合法超过六人的配置不静默丢人', () => {
  let draft = createScheduleDraft(fixture(), {})
  for (let i = 2; i <= 6; i++) draft = assignDraftPlayer(draft, player(i + 7), 10, 20, i)
  assert.throws(() => assignDraftPlayer(draft, player(99), 10, 20, 6), /已有/)
  const broken = clone(draft)
  broken.schedule.teams[0].squads[0].members.push({ ...player(99), order_num: 6 })
  assert.throws(() => validateScheduleDraft(broken), /位置/)
  const legacy = createScheduleDraft(fixture(), {})
  legacy.schedule.teams[0].squads[0].max_members = 12
  legacy.schedule.teams[0].squads[0].members.push({ ...player(99), order_num: 7 })
  assert.doesNotThrow(() => validateScheduleDraft(legacy))
  assert.equal(buildScheduleBoxes(legacy.schedule, legacy.workbook)[0].squads[0].overflow.length, 1)
})

test('加载历史只产生本地 ID 和草稿，临时位置按名称/顺序恢复，不改历史输入', () => {
  let source = upsertDraftTempMember(createScheduleDraft(fixture(), {}), temp)
  source = assignDraftPlayer(source, temp, 10, 20, 2)
  const history = clone(source.schedule)
  history.schedule_id = 100
  history.teams[0].team_id = 110
  history.teams[0].squads[0].squad_id = 120
  const loaded = loadHistoryIntoDraft(createScheduleDraft(fixture(), {}), history, source.workbook, type => `local_${type}_history`)
  assert.equal(loaded.schedule.schedule_id, 1)
  assert.equal(loaded.schedule.teams[0].team_id, 'local_team_history')
  assert.equal(buildScheduleBoxes(loaded.schedule, loaded.workbook)[0].squads[0].seats[1].member.member_id, 'temp_a')
  assert.equal(history.teams[0].team_id, 110)
  assert.equal(loaded.dirty, true)
})

test('每 10000ms 定时调用本地存储，不调用后端；错误不报告成功，重复周期不重复写', async () => {
  let tick, interval, clears = 0, writes = 0, success = 0, errors = 0
  const draft = assignDraftPlayer(createScheduleDraft(fixture(), {}), player(8), 10, 20, 2)
  const autosaver = createDraftAutosaver({
    read: () => draft, persist: async value => { assert.notEqual(value, draft); writes++ },
    onSuccess: () => success++, onError: () => errors++,
    setTimer: (fn, ms) => { tick = fn; interval = ms; return 1 }, clearTimer: () => clears++
  })
  autosaver.start()
  assert.equal(interval, 10000)
  assert.equal(writes, 0)
  await tick()
  await tick()
  assert.equal(writes, 1)
  assert.equal(success, 1)
  autosaver.stop()
  assert.equal(clears, 1)
  const failing = createDraftAutosaver({ read: () => draft, persist: async () => { throw Error('磁盘满') }, onSuccess: () => success++, onError: () => errors++ })
  await failing.flush()
  assert.equal(errors, 1)
  assert.equal(success, 1)
})

function mockApi(schedule = fixture(), wb = {}) {
  let server = clone(schedule), workbook = clone(wb), teamId = 1000, squadId = 2000
  const writes = []
  let failWorkbook = false
  const api = {
    getCurrentSchedule: async () => ({ data: clone(server) }),
    getCurrentScheduleWorkbook: async () => ({ data: { schedule_id: 1, workbook: clone(workbook) } }),
    addScheduleTeam: async body => { writes.push(['team', body]); server.teams.push({ team_id: teamId++, team_name: body.team_name, order_num: server.teams.length + 1, squads: [] }) },
    addScheduleSquad: async (id, body) => { writes.push(['squad', body]); const team = server.teams.find(t => t.team_id === id); team.squads.push({ squad_id: squadId++, squad_name: body.squad_name, order_num: team.squads.length + 1, max_members: 6, members: [] }) },
    deleteScheduleTeam: async id => { writes.push(['deleteTeam', id]); server.teams = server.teams.filter(t => t.team_id !== id) },
    deleteScheduleSquad: async (id, sid) => { writes.push(['deleteSquad', sid]); const team = server.teams.find(t => t.team_id === id); team.squads = team.squads.filter(s => s.squad_id !== sid) },
    updateRegionSquad: async (sid, body) => { writes.push(['resize', body]); Object.assign(server.teams.flatMap(t => t.squads).find(s => s.squad_id === sid), body) },
    syncRegionSquadAssignments: async (sid, body) => {
      writes.push(['assign', body])
      const squads = server.teams.flatMap(t => t.squads), ids = new Set(body.members.map(m => m.member_id))
      squads.forEach(s => { s.members = s.squad_id === sid ? [] : s.members.filter(m => !ids.has(m.member_id)) })
      squads.find(s => s.squad_id === sid).members = body.members.map(m => ({ ...player(m.member_id), order_num: m.order_num }))
    },
    saveCurrentScheduleWorkbook: async value => { writes.push(['workbook', clone(value)]); if (failWorkbook) throw Error('模拟保存失败'); workbook = clone(value) }
  }
  return { api, writes, state: () => ({ schedule: clone(server), workbook: clone(workbook) }), fail: value => { failWorkbook = value } }
}

test('只有显式同步才调用 API；新团队 ID 转换后批量保存玩家和临时位置，重复保存无多余写入', async () => {
  const mock = mockApi()
  let draft = addDraftTeam(createScheduleDraft(fixture(), {}), '防守团', 'local_team_a')
  draft = addDraftSquad(draft, 'local_team_a', '二队', 'local_squad_a')
  draft = assignDraftPlayer(draft, player(7), 'local_team_a', 'local_squad_a', 6)
  draft = assignDraftPlayer(upsertDraftTempMember(draft, temp), temp, 'local_team_a', 'local_squad_a', 2)
  assert.equal(mock.writes.length, 0)
  const result = await syncScheduleDraft(draft, mock.api)
  assert.equal(result.dirty, false)
  assert.equal(result.schedule.teams[1].team_id, 1000)
  assert.equal(result.workbook.custom.guildScheduleBoxes.tempAssignments[0].squadId, 2000)
  assert.ok(mock.writes.filter(w => w[0] === 'assign').every(w => w[1].members.every(m => Number.isInteger(m.member_id))))
  const count = mock.writes.length
  await syncScheduleDraft(result, mock.api)
  assert.equal(mock.writes.length, count)
})

test('保存失败保留草稿和已创建 ID，重新读取后重试不重复创建团队或小队', async () => {
  const mock = mockApi()
  let draft = addDraftTeam(createScheduleDraft(fixture(), {}), '防守团', 'local_team_a')
  draft = addDraftSquad(draft, 'local_team_a', '二队', 'local_squad_a')
  draft = assignDraftPlayer(upsertDraftTempMember(draft, temp), temp, 'local_team_a', 'local_squad_a', 2)
  let checkpoint = draft
  mock.fail(true)
  await assert.rejects(syncScheduleDraft(draft, mock.api, { onCheckpoint: async value => { checkpoint = clone(value) } }), /模拟保存失败/)
  assert.equal(checkpoint.dirty, true)
  assert.equal(checkpoint.schedule.teams[1].team_id, 1000)
  assert.equal(buildScheduleBoxes(checkpoint.schedule, checkpoint.workbook)[1].squads[0].seats[1].member.member_id, 'temp_a')
  mock.fail(false)
  const result = await syncScheduleDraft(checkpoint, mock.api)
  assert.equal(result.dirty, false)
  assert.equal(mock.writes.filter(w => w[0] === 'team').length, 1)
  assert.equal(mock.writes.filter(w => w[0] === 'squad').length, 1)
})

test('并发修改阻止无提示覆盖，校验失败不能先创建或删除后端记录', async () => {
  const mock = mockApi()
  const draft = assignDraftPlayer(createScheduleDraft(fixture(), {}), player(8), 10, 20, 2)
  await mock.api.addScheduleTeam({ team_name: '其他窗口的团队' })
  const count = mock.writes.length
  await assert.rejects(syncScheduleDraft(draft, mock.api), error => error.code === 'SCHEDULE_CONFLICT')
  assert.equal(mock.writes.length, count)
  const invalid = clone(draft)
  invalid.schedule.teams[0].squads[0].members[0].order_num = 0
  await assert.rejects(syncScheduleDraft(invalid, mock.api, { force: true }), /位置/)
  assert.equal(mock.writes.length, count)
  assert.notEqual(scheduleFingerprint(fixture(), {}), scheduleFingerprint(mock.state().schedule, {}))
})

test('提交完成后仍保留账号隔离的 IndexedDB key，所有进度与最终结果都可以存回同一草稿', async () => {
  const mock = mockApi(), saved = []
  const draft = assignDraftPlayer(createScheduleDraft(fixture(), {}), player(8), 10, 20, 2)
  draft.storageKey = '[1,"账号甲","1","/dev-api"]'
  const result = await syncScheduleDraft(draft, mock.api, { onCheckpoint: async value => { saved.push(value.storageKey) } })
  assert.equal(result.storageKey, draft.storageKey)
  assert.ok(saved.every(value => value === draft.storageKey))
})

test('后端返回成功但实际阵容未保存时不能假报提交完成', async () => {
  const mock = mockApi()
  mock.api.syncRegionSquadAssignments = async () => {}
  const draft = assignDraftPlayer(createScheduleDraft(fixture(), {}), player(8), 10, 20, 2)
  await assert.rejects(syncScheduleDraft(draft, mock.api), /不一致|未完整/)
  assert.equal(draft.dirty, true)
})

test('本地数据库 key 隔离账号、排表和接口环境，缺少账号不能退回共用 key', () => {
  const a = draftStorageKey(1, 10, '/dev-api')
  assert.notEqual(a, draftStorageKey(2, 10, '/dev-api'))
  assert.notEqual(a, draftStorageKey(1, 11, '/dev-api'))
  assert.notEqual(a, draftStorageKey(1, 10, 'https://other-api'))
  assert.throws(() => draftStorageKey('', 10, '/dev-api'), /账号/)
})

test('同步流程可即时重试幂等请求，不依赖全局关闭防重复提交', async () => {
  const mock = mockApi()
  const save = mock.api.saveCurrentScheduleWorkbook
  mock.api.saveCurrentScheduleWorkbook = async (value, options) => { assert.equal(options.repeatSubmit, false); await save(value) }
  const draft = upsertDraftTempMember(createScheduleDraft(fixture(), {}), temp)
  assert.equal((await syncScheduleDraft(draft, mock.api)).dirty, false)
})
