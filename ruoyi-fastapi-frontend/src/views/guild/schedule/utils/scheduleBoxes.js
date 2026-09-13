const key = value => String(value ?? '')
const copy = value => JSON.parse(JSON.stringify(value || {}))
const ordered = rows => [...(rows || [])].sort((a, b) => Number(a.order_num || 0) - Number(b.order_num || 0))
const isTemporary = member => member?.is_temporary || key(member?.member_id).startsWith('temp_')

function workbookPlayers(workbook) {
  const result = new Map()
  Object.entries(workbook?.sheets || {}).forEach(([sheetId, sheet]) => {
    Object.entries(sheet?.cellData || {}).forEach(([row, columns]) => {
      Object.entries(columns || {}).forEach(([column, cell]) => {
        const player = cell?.custom
        if (!player?.member_id) return
        const id = key(player.member_id)
        if (!result.has(id)) result.set(id, {
          ...player, member_id: isTemporary(player) ? id : player.member_id, is_temporary: !!isTemporary(player),
          player_name: player.player_name || String(cell.v ?? ''),
          cellLabel: `${sheet.name || sheetId} · 行${Number(row) + 1}/列${Number(column) + 1}`
        })
      })
    })
  })
  return [...result.values()]
}

export function readTempMembers(workbook) {
  const members = new Map()
  const listed = workbook?.custom?.guildScheduleTempMembers
  ;[...(Array.isArray(listed) ? listed : []), ...workbookPlayers(workbook).filter(isTemporary)]
    .forEach(member => {
      if (!member?.member_id || !member?.player_name) return
      const id = key(member.member_id)
      if (!members.has(id)) members.set(id, { ...member, member_id: id, is_temporary: true })
    })
  return [...members.values()]
}

function records(workbook) {
  const rows = workbook?.custom?.guildScheduleBoxes?.tempAssignments
  return Array.isArray(rows) ? rows : []
}

function withRecords(workbook, schedule, assignments) {
  const next = copy(workbook)
  next.custom ||= {}
  next.custom.guildScheduleBoxes = {
    ...(next.custom.guildScheduleBoxes || {}), version: 1,
    scheduleId: schedule?.schedule_id, tempAssignments: assignments
  }
  return next
}

export function withTempMembers(workbook, members) {
  const next = copy(workbook)
  next.custom ||= {}
  const unique = new Map()
  ;(members || []).forEach(member => {
    if (member?.member_id && member?.player_name) unique.set(key(member.member_id), {
      ...member, member_id: key(member.member_id), is_temporary: true
    })
  })
  next.custom.guildScheduleTempMembers = [...unique.values()]
  return next
}

export function buildScheduleBoxes(schedule, workbook) {
  const temps = new Map(readTempMembers(workbook).map(member => [key(member.member_id), member]))
  const usedTemps = new Set()
  return ordered(schedule?.teams).map(team => {
    const squads = ordered(team.squads).map(squad => {
      const seats = Array.from({ length: 6 }, (_, index) => ({ orderNum: index + 1, member: null }))
      const overflow = []
      ;(squad.members || []).forEach(member => {
        const slot = seats[Number(member.order_num) - 1]
        if (!slot || slot.member) overflow.push(member)
        else slot.member = member
      })
      records(workbook).forEach(record => {
        if (key(record.teamId) !== key(team.team_id) || key(record.squadId) !== key(squad.squad_id)) return
        const member = temps.get(key(record.memberId))
        const slot = seats[Number(record.orderNum) - 1]
        if (!member || !slot || slot.member || usedTemps.has(key(record.memberId))) return
        slot.member = member
        usedTemps.add(key(record.memberId))
      })
      return { ...squad, seats, overflow, count: seats.filter(seat => seat.member).length + overflow.length }
    })
    return {
      team_id: team.team_id, team_name: team.team_name, order_num: team.order_num,
      squads, count: squads.reduce((sum, squad) => sum + squad.count, 0)
    }
  })
}

function findSquad(schedule, teamId, squadId) {
  const team = (schedule?.teams || []).find(row => key(row.team_id) === key(teamId))
  const squad = (team?.squads || []).find(row => key(row.squad_id) === key(squadId))
  return { team, squad }
}

export function withTempAssignment(workbook, schedule, member, teamId, squadId, orderNum) {
  const { team, squad } = findSquad(schedule, teamId, squadId)
  if (!team || !squad) throw new Error('目标小队不存在')
  if (!Number.isInteger(orderNum) || orderNum < 1 || orderNum > 6) throw new Error('位置必须在 1–6 之间')
  if (!isTemporary(member) || !readTempMembers(workbook).some(row => key(row.member_id) === key(member.member_id))) {
    throw new Error('临时玩家不存在')
  }
  const target = buildScheduleBoxes(schedule, workbook).find(row => key(row.team_id) === key(teamId))
    .squads.find(row => key(row.squad_id) === key(squadId)).seats[orderNum - 1]
  if (target.member && key(target.member.member_id) !== key(member.member_id)) throw new Error('目标位置已有玩家，请先移出')
  const next = records(workbook).filter(row => key(row.memberId) !== key(member.member_id))
  next.push({
    memberId: key(member.member_id), teamId: team.team_id, squadId: squad.squad_id, orderNum,
    teamName: team.team_name, squadName: squad.squad_name,
    teamOrder: team.order_num, squadOrder: squad.order_num
  })
  return withRecords(workbook, schedule, next)
}

export function withoutTempAssignment(workbook, memberId) {
  return withRecords(workbook, { schedule_id: workbook?.custom?.guildScheduleBoxes?.scheduleId },
    records(workbook).filter(row => key(row.memberId) !== key(memberId)))
}

export function pruneTempAssignments(workbook, schedule) {
  const listed = new Set(readTempMembers(workbook).map(member => key(member.member_id)))
  const usedMembers = new Set()
  const usedSlots = new Set()
  const next = records(workbook).filter(record => {
    const { squad } = findSquad(schedule, record.teamId, record.squadId)
    const slotKey = `${record.squadId}:${record.orderNum}`
    if (!squad || !listed.has(key(record.memberId)) || usedMembers.has(key(record.memberId)) || usedSlots.has(slotKey)) return false
    if (!Number.isInteger(record.orderNum) || record.orderNum < 1 || record.orderNum > 6) return false
    if ((squad.members || []).some(member => Number(member.order_num) === record.orderNum)) return false
    usedMembers.add(key(record.memberId))
    usedSlots.add(slotKey)
    return true
  })
  return withRecords(workbook, schedule, next)
}

export function remapTempAssignments(workbook, schedule) {
  const next = records(workbook).flatMap(record => {
    const matches = []
    ;(schedule?.teams || []).forEach(team => {
      if (team.team_name !== record.teamName || Number(team.order_num) !== Number(record.teamOrder)) return
      ;(team.squads || []).forEach(squad => {
        if (squad.squad_name === record.squadName && Number(squad.order_num) === Number(record.squadOrder)) {
          matches.push({ ...record, teamId: team.team_id, squadId: squad.squad_id })
        }
      })
    })
    return matches.length === 1 ? matches : []
  })
  return pruneTempAssignments(withRecords(workbook, schedule, next), schedule)
}

export function collectLegacyMembers(workbook, schedule) {
  const placed = new Set(buildScheduleBoxes(schedule, workbook).flatMap(team => team.squads
    .flatMap(squad => [...squad.seats.map(seat => seat.member).filter(Boolean), ...squad.overflow]))
    .map(member => key(member.member_id)))
  return workbookPlayers(workbook).filter(member => !placed.has(key(member.member_id)))
}

export function groupPlayersByClass(members) {
  const groups = new Map()
  ;(members || []).forEach(member => {
    const name = String(member.player_class || '').trim() || '未设置'
    if (!groups.has(name)) groups.set(name, [])
    groups.get(name).push(member)
  })
  return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b, 'zh-Hans-CN'))
    .map(([className, rows]) => ({ className, members: rows }))
}
