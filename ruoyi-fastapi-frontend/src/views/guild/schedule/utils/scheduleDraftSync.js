import { cloneDraft, scheduleFingerprint, validateScheduleDraft, createScheduleDraft } from './scheduleDraft.js'
import { pruneTempAssignments } from './scheduleBoxes.js'

const key = value => String(value ?? '')
const local = value => key(value).startsWith('local_')
const assignments = rows => JSON.stringify((rows || []).map(member => [Number(member.member_id), Number(member.order_num)]).sort((a, b) => a[0] - b[0]))

function remapIds(draft, server, teamMap = {}, squadMap = {}) {
  draft.schedule.teams.forEach(team => {
    team.team_id = teamMap[key(team.team_id)] ?? team.team_id
    const real = server.teams.find(t => key(t.team_id) === key(team.team_id))
    if (real) team.order_num = real.order_num
    team.squads.forEach(squad => {
      squad.squad_id = squadMap[key(squad.squad_id)] ?? squad.squad_id
      const actual = real?.squads.find(s => key(s.squad_id) === key(squad.squad_id))
      if (actual) squad.order_num = actual.order_num
    })
  })
  const records = draft.workbook.custom?.guildScheduleBoxes?.tempAssignments
  if (Array.isArray(records)) records.forEach(record => {
    record.teamId = teamMap[key(record.teamId)] ?? record.teamId
    record.squadId = squadMap[key(record.squadId)] ?? record.squadId
    const team = draft.schedule.teams.find(t => key(t.team_id) === key(record.teamId))
    const squad = team?.squads.find(s => key(s.squad_id) === key(record.squadId))
    if (team && squad) { record.teamOrder = team.order_num; record.squadOrder = squad.order_num }
  })
}

// Called only by an explicit Save operation. Existing endpoints commit per request,
// so checkpoint the preserved draft after each step and reconcile fresh state on retry.
export async function syncScheduleDraft(input, api, { onCheckpoint = async () => {}, force = false } = {}) {
  validateScheduleDraft(input)
  const draft = cloneDraft(input)
  let server, serverWorkbook
  async function readServer() {
    const [s, w] = await Promise.all([api.getCurrentSchedule(), api.getCurrentScheduleWorkbook()])
    server = s.data
    if (key(server?.schedule_id) !== key(draft.schedule.schedule_id) || key(w.data?.schedule_id) !== key(server?.schedule_id)) throw Error('当前排表已经变化，草稿已保留，请重新读取')
    serverWorkbook = w.data?.workbook || {}
  }
  await readServer()
  const fingerprint = scheduleFingerprint(server, serverWorkbook)
  if (!force && fingerprint !== (draft.expectedFingerprint || draft.baseFingerprint)) {
    const error = Error('后端排表已变化，本地草稿尚未覆盖后端')
    error.code = 'SCHEDULE_CONFLICT'
    throw error
  }
  async function checkpoint() {
    draft.dirty = true
    draft.syncPending = true
    draft.expectedFingerprint = scheduleFingerprint(server, serverWorkbook)
    await onCheckpoint(cloneDraft(draft))
  }
  await checkpoint()
  try {
    // Remove only structures absent from the user's final draft, not guild members.
    for (const team of [...server.teams]) {
      const desired = draft.schedule.teams.find(t => key(t.team_id) === key(team.team_id))
      if (!desired) {
        await api.deleteScheduleTeam(team.team_id)
        server.teams = server.teams.filter(t => key(t.team_id) !== key(team.team_id))
        await checkpoint()
      } else for (const squad of [...team.squads]) {
        if (!desired.squads.some(s => key(s.squad_id) === key(squad.squad_id))) {
          await api.deleteScheduleSquad(team.team_id, squad.squad_id)
          team.squads = team.squads.filter(s => key(s.squad_id) !== key(squad.squad_id))
          await checkpoint()
        }
      }
    }
    for (const team of draft.schedule.teams) {
      if (local(team.team_id)) {
        const oldId = key(team.team_id)
        // A previous uncertain response may already have created this unique name.
        let matches = server.teams.filter(t => t.team_name === team.team_name)
        if (!matches.length) { await api.addScheduleTeam({ team_name: team.team_name }, { repeatSubmit: false }); await readServer(); matches = server.teams.filter(t => t.team_name === team.team_name) }
        if (matches.length !== 1) throw Error('团队创建结果不唯一，草稿已保留')
        remapIds(draft, server, { [oldId]: matches[0].team_id })
        await checkpoint()
      }
      const actualTeam = server.teams.find(t => key(t.team_id) === key(team.team_id))
      if (!actualTeam) throw Error('目标团队已经不存在，草稿已保留')
      for (const squad of team.squads) {
        if (local(squad.squad_id)) {
          const oldId = key(squad.squad_id)
          let actual = server.teams.find(t => key(t.team_id) === key(team.team_id))
          let matches = actual.squads.filter(s => s.squad_name === squad.squad_name)
          if (!matches.length) { await api.addScheduleSquad(team.team_id, { squad_name: squad.squad_name }, { repeatSubmit: false }); await readServer(); actual = server.teams.find(t => key(t.team_id) === key(team.team_id)); matches = actual.squads.filter(s => s.squad_name === squad.squad_name) }
          if (matches.length !== 1) throw Error('小队创建结果不唯一，草稿已保留')
          remapIds(draft, server, {}, { [oldId]: matches[0].squad_id })
          await checkpoint()
        }
      }
    }
    for (const team of draft.schedule.teams) for (const squad of team.squads) {
      const actual = server.teams.flatMap(t => t.squads).find(s => key(s.squad_id) === key(squad.squad_id))
      if (!actual) throw Error('目标小队已经不存在，草稿已保留')
      if (Number(actual.max_members) !== Number(squad.max_members) || actual.squad_name !== squad.squad_name) {
        await api.updateRegionSquad(squad.squad_id, { squad_name: squad.squad_name, max_members: squad.max_members }, { repeatSubmit: false })
        actual.max_members = squad.max_members; actual.squad_name = squad.squad_name
        await checkpoint()
      }
      if (assignments(actual.members) !== assignments(squad.members)) {
        await api.syncRegionSquadAssignments(squad.squad_id, { members: squad.members.map(member => ({ member_id: Number(member.member_id), order_num: member.order_num })) }, { repeatSubmit: false })
        const ids = new Set(squad.members.map(member => key(member.member_id)))
        server.teams.forEach(t => t.squads.forEach(s => { s.members = key(s.squad_id) === key(squad.squad_id) ? cloneDraft(squad.members) : s.members.filter(m => !ids.has(key(m.member_id))) }))
        await checkpoint()
      }
    }
    draft.workbook = pruneTempAssignments(draft.workbook, draft.schedule)
    // Don't create an empty metadata namespace just for an unchanged no-op Save.
    if (!input.workbook.custom?.guildScheduleBoxes && !draft.workbook.custom.guildScheduleBoxes.tempAssignments.length &&
        !input.dirty && !input.syncPending) draft.workbook = cloneDraft(input.workbook)
    if (JSON.stringify(draft.workbook) !== JSON.stringify(serverWorkbook)) {
      await api.saveCurrentScheduleWorkbook(draft.workbook, { repeatSubmit: false })
      serverWorkbook = cloneDraft(draft.workbook)
      await checkpoint()
    }
    await readServer()
    if (scheduleFingerprint(draft.schedule, draft.workbook) !== scheduleFingerprint(server, serverWorkbook)) throw Error('后端阵容与草稿不一致，未完整提交，请再次保存')
    const result = createScheduleDraft(server, serverWorkbook)
    result.storageKey = draft.storageKey
    result.revision = draft.revision + 1
    await onCheckpoint(cloneDraft(result))
    return result
  } catch (error) {
    // Keep real IDs after partial or uncertain writes; never discard the desired roster.
    try {
      await readServer()
      const teamMap = {}, squadMap = {}
      draft.schedule.teams.filter(t => local(t.team_id)).forEach(team => {
        const matches = server.teams.filter(t => t.team_name === team.team_name)
        if (matches.length === 1) teamMap[key(team.team_id)] = matches[0].team_id
      })
      remapIds(draft, server, teamMap)
      draft.schedule.teams.forEach(team => team.squads.filter(s => local(s.squad_id)).forEach(squad => {
        const matches = server.teams.find(t => key(t.team_id) === key(team.team_id))?.squads.filter(s => s.squad_name === squad.squad_name) || []
        if (matches.length === 1) squadMap[key(squad.squad_id)] = matches[0].squad_id
      }))
      remapIds(draft, server, {}, squadMap)
      await checkpoint()
    } catch { /* Original error remains authoritative; prior checkpoint is retained. */ }
    throw error
  }
}
