const METRIC_KEYS = [
  'kills', 'qingquan_kills', 'assists', 'resources', 'dmg_to_players',
  'armor_break_players', 'dmg_to_buildings', 'armor_break_buildings',
  'healing', 'dmg_taken', 'deaths', 'revives', 'qingquan_revives', 'burn_bones',
]

export function normalizePlayerName(value) {
  return String(value || '').trim().replace(/\s+/gu, '').replace(/[.。．·]+$/gu, '')
}

function playerRows(teams) {
  const rows = []
  for (const team of teams || []) {
    for (const squad of team.squads || []) {
      for (const seat of squad.seats || []) {
        if (!seat.player?.name) continue
        rows.push({ team, squad, seat, player: seat.player, key: normalizePlayerName(seat.player.name) })
      }
    }
  }
  return rows
}

function addMetric(target, key, value) {
  const normalized = String(value ?? '0').replaceAll(',', '').trim() || '0'
  target[key] = (BigInt(target[key] || '0') + BigInt(/^[0-9]+$/.test(normalized) ? normalized : '0')).toString()
}

function totals(records) {
  const result = Object.fromEntries(METRIC_KEYS.map(key => [key, '0']))
  for (const record of records) for (const key of METRIC_KEYS) addMetric(result, key, record?.[key])
  return result
}

function groupedRecords(records) {
  const order = []
  const groups = new Map()
  for (const record of records || []) {
    const name = String(record.guild_name || '').trim()
    if (!groups.has(name)) { groups.set(name, []); order.push(name) }
    groups.get(name).push(record)
  }
  return { order, groups }
}

export function buildBoxAnalysis(teams, records) {
  const roster = playerRows(teams)
  const rosterKeys = new Set(roster.map(item => item.key))
  const { order, groups } = groupedRecords(records)
  const candidates = order.map((name, index) => {
    const rows = groups.get(name)
    const matched = new Set(rows.map(row => normalizePlayerName(row.player_name)).filter(key => rosterKeys.has(key))).size
    return { name, index, rows, matched, rate: rows.length ? matched / rows.length : 0 }
  })
  candidates.sort((a, b) => b.matched - a.matched || b.rate - a.rate || a.index - b.index)
  const selected = candidates[0] || { name: '', rows: [], matched: 0 }
  const recordMap = new Map(selected.rows.map(record => [normalizePlayerName(record.player_name), record]))
  const makePlayer = row => ({
    name: row.player.name,
    profession: row.player.profession || row.record?.player_class || '',
    hasData: !!row.record,
    metrics: totals(row.record ? [row.record] : []),
  })
  const boxes = (teams || []).map(team => {
    const teamRows = roster.filter(row => row.team.id === team.id).map(row => ({ ...row, record: recordMap.get(row.key) }))
    return {
      id: team.id,
      name: team.name,
      configuredPlayers: teamRows.length,
      matchedPlayers: teamRows.filter(row => row.record).length,
      metrics: totals(teamRows.map(row => row.record).filter(Boolean)),
      squads: (team.squads || []).map(squad => {
        const squadRows = teamRows.filter(row => row.squad.id === squad.id)
        return {
          id: squad.id,
          name: squad.name,
          configuredPlayers: squadRows.length,
          matchedPlayers: squadRows.filter(row => row.record).length,
          metrics: totals(squadRows.map(row => row.record).filter(Boolean)),
          players: squadRows.map(makePlayer),
        }
      }),
    }
  })
  const selectedKeys = new Set(selected.rows.map(row => normalizePlayerName(row.player_name)))
  return {
    selectedGuild: selected.name,
    guilds: candidates.sort((a, b) => a.index - b.index).map(item => ({ name: item.name, players: item.rows.length, matched: item.matched })),
    configuredPlayers: rosterKeys.size,
    csvPlayers: selected.rows.length,
    matchedPlayers: selected.matched,
    csvOnlyPlayers: selected.rows.filter(row => !rosterKeys.has(normalizePlayerName(row.player_name))).length,
    missingDataPlayers: [...rosterKeys].filter(key => !selectedKeys.has(key)).length,
    metrics: totals(selected.rows.filter(row => rosterKeys.has(normalizePlayerName(row.player_name)))),
    boxes,
  }
}

export { METRIC_KEYS }
