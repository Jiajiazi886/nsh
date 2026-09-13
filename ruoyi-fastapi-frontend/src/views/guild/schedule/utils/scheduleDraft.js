import { buildScheduleBoxes, readTempMembers, withTempMembers, withTempAssignment,
  withoutTempAssignment, pruneTempAssignments, remapTempAssignments } from './scheduleBoxes.js'

export const cloneDraft = value => JSON.parse(JSON.stringify(value))
const key = value => String(value ?? '')
const temporary = member => member?.is_temporary || key(member?.member_id).startsWith('temp_')
const canonical = value => Array.isArray(value) ? value.map(canonical) : value && typeof value === 'object'
  ? Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])])) : value
const sorted = rows => [...(rows || [])].sort((a, b) => key(a[0]).localeCompare(key(b[0])))

export function scheduleFingerprint(schedule, workbook) {
  const teams = sorted((schedule?.teams || []).map(team => [key(team.team_id), team.team_name, Number(team.order_num),
    sorted((team.squads || []).map(squad => [key(squad.squad_id), squad.squad_name, Number(squad.order_num), Number(squad.max_members || 6),
      sorted((squad.members || []).map(member => [key(member.member_id), Number(member.order_num)]))]))]))
  return JSON.stringify([teams, canonical(workbook || {})])
}

export function createScheduleDraft(schedule, workbook) {
  return { version: 1, schedule: cloneDraft(schedule), workbook: cloneDraft(workbook || {}),
    baseFingerprint: scheduleFingerprint(schedule, workbook), dirty: false, revision: 0, updatedAt: Date.now() }
}
function changed(draft, schedule, workbook) {
  return { ...draft, schedule, workbook, dirty: scheduleFingerprint(schedule, workbook) !== draft.baseFingerprint,
    revision: draft.revision + 1, updatedAt: Date.now() }
}
function findSquad(schedule, teamId, squadId) {
  const team = schedule.teams.find(row => key(row.team_id) === key(teamId))
  const squad = team?.squads.find(row => key(row.squad_id) === key(squadId))
  return { team, squad }
}
function validName(name) {
  const value = String(name || '').trim()
  if (!value || value.length > 30) throw Error('名称不能为空且最多 30 个字')
  return value
}
export function addDraftTeam(draft, name, id) {
  const schedule = cloneDraft(draft.schedule), value = validName(name)
  if (schedule.teams.some(team => team.team_name === value)) throw Error('团队名称已存在')
  schedule.teams.push({ team_id: id, team_name: value, order_num: Math.max(0, ...schedule.teams.map(t => Number(t.order_num))) + 1, squads: [] })
  return changed(draft, schedule, draft.workbook)
}
export function addDraftSquad(draft, teamId, name, id) {
  const schedule = cloneDraft(draft.schedule), { team } = findSquad(schedule, teamId), value = validName(name)
  if (!team) throw Error('团队不存在')
  if (team.squads.some(squad => squad.squad_name === value)) throw Error('该团队的小队名称已存在')
  team.squads.push({ squad_id: id, squad_name: value, order_num: Math.max(0, ...team.squads.map(s => Number(s.order_num))) + 1, max_members: 6, members: [] })
  return changed(draft, schedule, draft.workbook)
}
export function removeDraftStructure(draft, teamId, squadId) {
  const schedule = cloneDraft(draft.schedule)
  if (squadId == null) schedule.teams = schedule.teams.filter(team => key(team.team_id) !== key(teamId))
  else {
    const { team } = findSquad(schedule, teamId)
    if (!team) throw Error('团队不存在')
    team.squads = team.squads.filter(squad => key(squad.squad_id) !== key(squadId))
  }
  return changed(draft, schedule, pruneTempAssignments(draft.workbook, schedule))
}
function locatePlayer(draft, memberId) {
  for (const team of buildScheduleBoxes(draft.schedule, draft.workbook)) {
    for (const squad of team.squads) {
      for (const seat of squad.seats) if (key(seat.member?.member_id) === key(memberId)) return { teamId: team.team_id, squadId: squad.squad_id, orderNum: seat.orderNum }
      const overflow = squad.overflow.find(member => key(member.member_id) === key(memberId))
      if (overflow) return { teamId: team.team_id, squadId: squad.squad_id, orderNum: Number(overflow.order_num) }
    }
  }
  return null
}
function detach(schedule, workbook, memberId) {
  schedule.teams.forEach(team => team.squads.forEach(squad => {
    squad.members = squad.members.filter(member => key(member.member_id) !== key(memberId))
  }))
  return withoutTempAssignment(workbook, memberId)
}
function putPlayer(schedule, workbook, member, target) {
  if (temporary(member)) return withTempAssignment(workbook, schedule, member, target.teamId, target.squadId, target.orderNum)
  if (!Number.isInteger(Number(member.member_id)) || Number(member.member_id) <= 0) throw Error('正式成员 ID 无效')
  const { squad } = findSquad(schedule, target.teamId, target.squadId)
  const { assignment_id, ...fields } = member
  squad.members.push({ ...fields, order_num: target.orderNum })
  return workbook
}
export function assignDraftPlayer(draft, member, teamId, squadId, orderNum) {
  const { squad } = findSquad(draft.schedule, teamId, squadId)
  if (!squad) throw Error('目标小队不存在')
  if (!Number.isInteger(orderNum) || orderNum < 1 || orderNum > 6) throw Error('位置必须在 1–6 之间')
  const target = buildScheduleBoxes(draft.schedule, draft.workbook).find(team => key(team.team_id) === key(teamId))
    .squads.find(s => key(s.squad_id) === key(squadId)).seats[orderNum - 1].member
  if (target && key(target.member_id) === key(member.member_id)) return draft
  const origin = locatePlayer(draft, member.member_id)
  if (target && !origin) throw Error('目标位置已有玩家，请先移出，或选择已排玩家交换')
  if (target && (!Number.isInteger(origin.orderNum) || origin.orderNum < 1 || origin.orderNum > 6)) throw Error('旧兼容位置不能交换，请先选择空位')
  const schedule = cloneDraft(draft.schedule)
  let workbook = detach(schedule, draft.workbook, member.member_id)
  if (target) workbook = detach(schedule, workbook, target.member_id)
  workbook = putPlayer(schedule, workbook, member, { teamId, squadId, orderNum })
  if (target) workbook = putPlayer(schedule, workbook, target, origin)
  return changed(draft, schedule, workbook)
}
export function clearDraftPlayer(draft, memberId) {
  const schedule = cloneDraft(draft.schedule)
  return changed(draft, schedule, detach(schedule, draft.workbook, memberId))
}
export function upsertDraftTempMember(draft, member) {
  const listed = readTempMembers(draft.workbook).filter(row => key(row.member_id) !== key(member.member_id))
  return changed(draft, draft.schedule, withTempMembers(draft.workbook, [...listed, member]))
}
export function loadHistoryIntoDraft(draft, history, workbook, makeId) {
  const schedule = cloneDraft(draft.schedule)
  schedule.teams = cloneDraft(history.teams || []).map(team => ({ ...team, team_id: makeId('team'),
    squads: (team.squads || []).map(squad => ({ ...squad, squad_id: makeId('squad') })) }))
  return changed(draft, schedule, remapTempAssignments(workbook || {}, schedule))
}
export function validateScheduleDraft(draft) {
  const players = new Set(), teams = new Set(), squads = new Set()
  draft.schedule.teams.forEach(team => {
    validName(team.team_name)
    if (teams.has(key(team.team_id))) throw Error('团队 ID 重复')
    teams.add(key(team.team_id))
    team.squads.forEach(squad => {
      validName(squad.squad_name)
      if (squads.has(key(squad.squad_id))) throw Error('小队 ID 重复')
      squads.add(key(squad.squad_id))
      const positions = new Set(), limit = Number(squad.max_members || 6)
      squad.members.forEach(member => {
        if (!Number.isInteger(Number(member.member_id)) || Number(member.member_id) <= 0 || temporary(member)) throw Error('正式玩家 ID 无效')
        if (players.has(key(member.member_id))) throw Error(`玩家「${member.player_name}」重复编队`)
        players.add(key(member.member_id))
        if (!Number.isInteger(member.order_num) || member.order_num < 1 || member.order_num > limit || positions.has(member.order_num)) throw Error(`「${team.team_name}/${squad.squad_name}」存在无效或重复位置，请整理兼容人员后保存`)
        positions.add(member.order_num)
      })
    })
  })
}

export function createDraftAutosaver({ read, persist, onSuccess = () => {}, onError = () => {},
  setTimer = setInterval, clearTimer = clearInterval }) {
  let timer, lastSignature = '', pending = Promise.resolve()
  function flush(force = false) {
    pending = pending.then(async () => {
      const value = read()
      if (!value) return true
      const snapshot = cloneDraft(value), signature = JSON.stringify(snapshot)
      if (!force && signature === lastSignature) return true
      try { await persist(snapshot); lastSignature = signature; onSuccess(snapshot); return true }
      catch (error) { onError(error); return false }
    })
    return pending
  }
  function stop() { if (timer !== undefined) { clearTimer(timer); timer = undefined } }
  return { flush, stop, start() { stop(); timer = setTimer(() => flush(), 10000) } }
}
