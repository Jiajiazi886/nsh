const DATA = require('../data/data')
const Importer = require('./importer')

const KEY = 'jiusi_mp_state_v3'
const LEGACY_KEY = 'jiusi_mp_state_v2'
const S = { state: null }

function clone(value) { return JSON.parse(JSON.stringify(value)) }

function uid(prefix) {
  return (prefix || 'id') + '_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 7)
}

function nowText() {
  const date = new Date()
  const pad = function (value) { return String(value).padStart(2, '0') }
  return date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(date.getDate()) +
    ' ' + pad(date.getHours()) + ':' + pad(date.getMinutes())
}

function isValidState(state) {
  return !!(
    state && typeof state === 'object' &&
    Array.isArray(state.players) && Array.isArray(state.teams) &&
    Array.isArray(state.metrics) && Array.isArray(state.boxes) &&
    state.dataset && typeof state.dataset === 'object' &&
    state.dataset.stats && typeof state.dataset.stats === 'object'
  )
}

function normalizeAliases(name, aliases) {
  const owner = Importer.normalizeName(name)
  const seen = {}
  const out = []
  ;(aliases || []).forEach(function (alias) {
    const text = String(alias == null ? '' : alias).trim()
    const key = Importer.normalizeName(text)
    if (!key || key === owner || seen[key]) return
    seen[key] = true
    out.push(text)
  })
  return out
}

function mergeAliases(name, values) { return normalizeAliases(name, values) }

function rosterIds(state) {
  const out = []
  ;(state.teams || []).forEach(function (team) {
    ;(team.playerIds || []).forEach(function (id) {
      if (out.indexOf(id) < 0) out.push(id)
    })
  })
  return out
}

function groupCount(state) {
  const groups = []
  ;(state.teams || []).forEach(function (team) {
    if (groups.indexOf(team.group) < 0) groups.push(team.group)
  })
  return groups.length
}

function ensure(state) {
  state.version = 3
  if (!Array.isArray(state.players)) state.players = []
  if (!Array.isArray(state.teams)) state.teams = []
  if (!Array.isArray(state.metrics) || !state.metrics.length) state.metrics = clone(Importer.METRICS)
  if (!state.dataset || typeof state.dataset !== 'object') {
    state.dataset = { name: '空数据集', source: '', playerIds: [], stats: {} }
  }
  if (!state.dataset.stats || typeof state.dataset.stats !== 'object') state.dataset.stats = {}
  if (!Array.isArray(state.dataset.playerIds)) state.dataset.playerIds = Object.keys(state.dataset.stats)
  if (!Array.isArray(state.boxes)) state.boxes = []

  state.players = state.players
    .filter(function (player) { return player && typeof player === 'object' && player.id && player.name })
    .map(function (player) {
      return {
        id: String(player.id),
        name: String(player.name).trim(),
        role: String(player.role || '未知').trim() || '未知',
        aliases: normalizeAliases(player.name, player.aliases)
      }
    })

  state.teams = state.teams
    .filter(function (team) { return team && typeof team === 'object' })
    .map(function (team, index) {
      return {
        id: String(team.id || ('team_' + index)),
        group: String(team.group || '未分团').trim() || '未分团',
        name: String(team.name || ('队伍 ' + (index + 1))).trim() || ('队伍 ' + (index + 1)),
        playerIds: Array.isArray(team.playerIds) ? team.playerIds.map(String) : []
      }
    })

  const playerIds = {}
  state.players.forEach(function (player) { playerIds[player.id] = true })
  state.dataset.playerIds = state.dataset.playerIds.map(String).filter(function (id, index, list) {
    return playerIds[id] && list.indexOf(id) === index
  })

  state.boxes = state.boxes
    .filter(function (box) { return box && typeof box === 'object' })
    .map(function (box, index) {
      return {
        id: typeof box.id === 'string' && box.id ? box.id : uid('box'),
        name: typeof box.name === 'string' && box.name.trim() ? box.name.trim() : '分析盒子 ' + (index + 1),
        teamIds: Array.isArray(box.teamIds) ? box.teamIds.map(String) : [],
        manualAddIds: Array.isArray(box.manualAddIds) ? box.manualAddIds.map(String) : [],
        manualRemoveIds: Array.isArray(box.manualRemoveIds) ? box.manualRemoveIds.map(String) : [],
        metricIds: Array.isArray(box.metricIds) ? box.metricIds.map(String) : [],
        view: box.view === 'players' ? 'players' : 'teams',
        tableSort: box.tableSort &&
          (box.tableSort.view === 'teams' || box.tableSort.view === 'players') &&
          typeof box.tableSort.key === 'string'
          ? {
              view: box.tableSort.view,
              key: box.tableSort.key,
              dir: box.tableSort.dir === 'asc' ? 'asc' : 'desc'
            }
          : null,
        sortMetricId: typeof box.sortMetricId === 'string' && box.sortMetricId ? box.sortMetricId : 'player_damage',
        collapsed: !!box.collapsed,
        tableCollapsed: !!box.tableCollapsed
      }
    })

  const rids = rosterIds(state)
  if (!state.teamConfig || typeof state.teamConfig !== 'object') {
    state.teamConfig = {
      source: '内置团队配置', importedAt: '', groupCount: groupCount(state),
      teamCount: state.teams.length, playerCount: rids.length
    }
  }
  if (state.lastImportReport === undefined) state.lastImportReport = null
  return state
}

function persist(state) { wx.setStorageSync(KEY, JSON.stringify(state)) }

function commit(candidate) {
  ensure(candidate)
  persist(candidate)
  S.state = candidate
  return clone(candidate.lastImportReport)
}

function toNumber(value) {
  const number = Number(String(value == null ? '' : value).replace(/,/g, '').trim())
  return isFinite(number) ? number : 0
}

function formatNumber(number, compact) {
  number = Number(number) || 0
  if (!compact) return Math.round(number).toLocaleString('zh-CN')
  if (Math.abs(number) >= 1e8) return (number / 1e8).toFixed(2).replace(/\.00$/, '') + '亿'
  if (Math.abs(number) >= 1e4) return (number / 1e4).toFixed(2).replace(/\.00$/, '') + '万'
  return Math.round(number).toLocaleString('zh-CN')
}

function zeroMetric(metric) { return metric && metric.kind === 'pair' ? { a: 0, b: 0 } : 0 }

function metricValue(stats, metric) {
  if (!metric) return 0
  const value = stats && stats[metric.id]
  if (value === undefined || value === null) return zeroMetric(metric)
  return value
}

function addMetric(accumulator, value, metric) {
  if (!metric) return accumulator
  if (metric.kind === 'pair') {
    accumulator.a += (value && value.a) || 0
    accumulator.b += (value && value.b) || 0
    return accumulator
  }
  return (accumulator || 0) + (Number(value) || 0)
}

function formatMetric(value, metric, compact) {
  if (!metric) return '—'
  if (metric.kind === 'pair') {
    return formatNumber((value && value.a) || 0, compact) + ' / ' + formatNumber((value && value.b) || 0, compact)
  }
  return formatNumber(value, compact)
}

function metricSortValue(value, metric) {
  if (!metric) return 0
  if (metric.kind === 'pair') return [(Number(value && value.a) || 0), (Number(value && value.b) || 0)]
  return Number(value) || 0
}

function findConfigMatch(index, playerConfig) {
  const identities = [playerConfig.name].concat(playerConfig.aliases || [])
  for (let i = 0; i < identities.length; i++) {
    const found = index[Importer.normalizeName(identities[i])]
    if (found) return found
  }
  return null
}

function defaultBox(state) {
  return {
    id: uid('box'), name: '全部队员',
    teamIds: state.teams.map(function (team) { return team.id }),
    manualAddIds: [], manualRemoveIds: [],
    metricIds: state.metrics.filter(function (metric) { return metric.id !== 'resource' }).map(function (metric) { return metric.id }),
    view: 'teams', tableSort: null, sortMetricId: 'player_damage', collapsed: false, tableCollapsed: false
  }
}

S.load = function () {
  let state = null
  let migrated = false
  try {
    const raw = wx.getStorageSync(KEY)
    if (raw) state = JSON.parse(raw)
  } catch (error) { state = null }
  if (!isValidState(state)) {
    try {
      const legacy = wx.getStorageSync(LEGACY_KEY)
      if (legacy) {
        const parsed = JSON.parse(legacy)
        if (isValidState(parsed)) { state = parsed; migrated = true }
      }
    } catch (error) { state = null }
  }
  if (!isValidState(state)) state = clone(DATA)
  S.state = ensure(state)
  if (migrated) {
    try { persist(S.state) } catch (error) {}
  }
  return S.state
}

S.save = function () {
  try { persist(S.state); return true } catch (error) { return false }
}

S.reset = function () {
  const candidate = ensure(clone(DATA))
  candidate.lastImportReport = {
    kind: 'reset', title: '已恢复内置示例', source: '内置九肆数据',
    importedAt: nowText(), tone: 'neutral',
    lines: ['60 名数据玩家 · 10 支队伍 · 3 个团']
  }
  commit(candidate)
}

S.getState = function () { if (!S.state) S.load(); return S.state }

S.playerMap = function () {
  const out = {}
  S.getState().players.forEach(function (player) { out[player.id] = player })
  return out
}

S.teamMap = function () {
  const out = {}
  S.getState().teams.forEach(function (team) { out[team.id] = team })
  return out
}

S.metricMap = function () {
  const out = {}
  S.getState().metrics.forEach(function (metric) { out[metric.id] = metric })
  return out
}

S.datasetPlayerSet = function () { return new Set(S.getState().dataset.playerIds || []) }
S.rosterPlayerIds = function () { return rosterIds(S.getState()) }

S.matchSummary = function () {
  const state = S.getState()
  const dataSet = S.datasetPlayerSet()
  const rids = rosterIds(state)
  const matchedCount = rids.filter(function (id) { return dataSet.has(id) }).length
  return {
    datasetName: state.dataset.name || '未命名数据',
    datasetSource: state.dataset.source || '内置数据',
    dataPlayerCount: state.dataset.playerIds.length,
    rosterPlayerCount: rids.length,
    matchedCount: matchedCount,
    missingCount: Math.max(0, rids.length - matchedCount),
    teamCount: state.teams.length,
    groupCount: groupCount(state)
  }
}

S.effectivePlayerIds = function (box) {
  const teamMap = S.teamMap()
  const dataSet = S.datasetPlayerSet()
  const ids = []
  const boxTeamIds = box.teamIds || []
  for (let i = 0; i < boxTeamIds.length; i++) {
    const team = teamMap[boxTeamIds[i]]
    const playerIds = (team && team.playerIds) || []
    for (let j = 0; j < playerIds.length; j++) {
      if (dataSet.has(playerIds[j]) && ids.indexOf(playerIds[j]) < 0) ids.push(playerIds[j])
    }
  }
  const adds = box.manualAddIds || []
  for (let i = 0; i < adds.length; i++) {
    if (dataSet.has(adds[i]) && ids.indexOf(adds[i]) < 0) ids.push(adds[i])
  }
  const removed = new Set(box.manualRemoveIds || [])
  return ids.filter(function (id) { return !removed.has(id) })
}

S.aggregate = function (playerIds, metricIds) {
  const metricMap = S.metricMap()
  const stats = S.getState().dataset.stats || {}
  const out = {}
  for (let metricIndex = 0; metricIndex < metricIds.length; metricIndex++) {
    const metricId = metricIds[metricIndex]
    const metric = metricMap[metricId]
    if (!metric) continue
    let accumulator = zeroMetric(metric)
    for (let playerIndex = 0; playerIndex < playerIds.length; playerIndex++) {
      accumulator = addMetric(accumulator, metricValue(stats[playerIds[playerIndex]], metric), metric)
    }
    out[metricId] = accumulator
  }
  return out
}

S.findPlayerByName = function (name) {
  const key = Importer.normalizeName(name)
  return S.getState().players.find(function (player) {
    return Importer.normalizeName(player.name) === key || (player.aliases || []).some(function (alias) {
      return Importer.normalizeName(alias) === key
    })
  }) || null
}

S.previewTeamConfig = function (text) { return Importer.parseTeamConfig(text) }

S.importTeamConfig = function (text, sourceName) {
  const parsed = Importer.parseTeamConfig(text)
  const candidate = clone(S.getState())
  const dataIds = new Set(candidate.dataset.playerIds || [])
  const dataPlayers = candidate.players.filter(function (player) { return dataIds.has(player.id) })
  const dataIndex = Importer.buildIdentityIndex(dataPlayers)
  const assignedDataIds = {}
  const newPlayers = dataPlayers.map(clone)
  const newPlayerMap = {}
  newPlayers.forEach(function (player) { newPlayerMap[player.id] = player })
  const teams = []

  parsed.groups.forEach(function (group, groupIndex) {
    group.teams.forEach(function (team, teamIndex) {
      const ids = team.players.map(function (playerConfig) {
        const matched = findConfigMatch(dataIndex, playerConfig)
        let player
        if (matched) {
          if (assignedDataIds[matched.id]) throw new Error('多个团队玩家匹配到同一条数据：' + playerConfig.name)
          assignedDataIds[matched.id] = true
          player = newPlayerMap[matched.id]
          const oldName = player.name
          player.name = playerConfig.name
          player.aliases = mergeAliases(player.name, (player.aliases || []).concat([oldName]).concat(playerConfig.aliases || []))
        } else {
          player = { id: uid('player'), name: playerConfig.name, role: '未知', aliases: mergeAliases(playerConfig.name, playerConfig.aliases || []) }
          newPlayers.push(player)
          newPlayerMap[player.id] = player
        }
        return player.id
      })
      teams.push({
        id: 'team_' + (groupIndex + 1) + '_' + (teamIndex + 1),
        group: group.name, name: team.name, playerIds: ids
      })
    })
  })

  candidate.players = newPlayers
  candidate.teams = teams
  candidate.teamConfig = {
    source: sourceName || '团队配置.json', importedAt: nowText(),
    groupCount: parsed.groupCount, teamCount: parsed.teamCount, playerCount: parsed.playerCount
  }
  candidate.boxes = [defaultBox(candidate)]

  const matchedCount = Object.keys(assignedDataIds).length
  const csvOnlyCount = Math.max(0, dataPlayers.length - matchedCount)
  const missingCount = Math.max(0, parsed.playerCount - matchedCount)
  candidate.lastImportReport = {
    kind: 'teams', title: '团队配置导入成功', source: sourceName || '团队配置.json',
    importedAt: nowText(), tone: matchedCount ? 'success' : 'warning',
    lines: [
      parsed.groupCount + ' 个团 · ' + parsed.teamCount + ' 支队伍 · ' + parsed.playerCount + ' 名配置玩家',
      '当前比赛数据匹配 ' + matchedCount + '/' + parsed.playerCount + ' 人',
      '团队缺少数据 ' + missingCount + ' 人 · CSV 未编队 ' + csvOnlyCount + ' 人',
      '旧盒子已清空，并重建“全部队员”盒子'
    ]
  }
  return commit(candidate)
}

S.importCsv = function (text, sourceName) {
  const camps = Importer.parseCsvCamps(text)
  const candidate = clone(S.getState())
  const playerMap = {}
  candidate.players.forEach(function (player) { playerMap[player.id] = player })
  const rids = rosterIds(candidate)
  const rosterPlayers = rids.map(function (id) { return playerMap[id] }).filter(Boolean)
  const selection = Importer.selectBestCamp(camps, rosterPlayers)
  const selected = selection.camp
  const rosterIndex = Importer.buildIdentityIndex(rosterPlayers)
  const matchedRosterIds = {}
  const newPlayers = rosterPlayers.map(clone)
  const newPlayerMap = {}
  newPlayers.forEach(function (player) { newPlayerMap[player.id] = player })
  const datasetPlayerIds = []
  const stats = {}

  selected.players.forEach(function (row) {
    const matched = rosterIndex[Importer.normalizeName(row.name)]
    let player
    if (matched) {
      matchedRosterIds[matched.id] = true
      player = newPlayerMap[matched.id]
      player.role = row.role
      player.aliases = mergeAliases(player.name, (player.aliases || []).concat([row.name]))
    } else {
      player = { id: uid('data'), name: row.name, role: row.role, aliases: [] }
      newPlayers.push(player)
      newPlayerMap[player.id] = player
    }
    datasetPlayerIds.push(player.id)
    stats[player.id] = clone(row.stats)
  })

  candidate.players = newPlayers
  candidate.metrics = clone(Importer.METRICS)
  candidate.dataset = {
    name: selected.name, source: sourceName || '比赛数据.csv', importedAt: nowText(),
    playerIds: datasetPlayerIds, stats: stats
  }

  const dataIdSet = new Set(datasetPlayerIds)
  const rosterIdSet = new Set(rids)
  const metricIds = {}
  candidate.metrics.forEach(function (metric) { metricIds[metric.id] = true })
  candidate.boxes = candidate.boxes.map(function (box) {
    box.manualAddIds = (box.manualAddIds || []).filter(function (id) { return dataIdSet.has(id) })
    box.manualRemoveIds = (box.manualRemoveIds || []).filter(function (id) { return rosterIdSet.has(id) })
    box.metricIds = (box.metricIds || []).filter(function (id) { return metricIds[id] })
    if (!metricIds[box.sortMetricId]) box.sortMetricId = 'player_damage'
    return box
  })

  const matchedCount = Object.keys(matchedRosterIds).length
  const csvOnlyCount = Math.max(0, selected.players.length - matchedCount)
  const missingCount = Math.max(0, rosterPlayers.length - matchedCount)
  const scoreLine = selection.scores.map(function (score) {
    return score.name + ' ' + score.matchedCount + '/' + rosterPlayers.length
  }).join(' · ')
  const lines = [
    '检测到 ' + camps.length + ' 个帮会，自动选择“' + selected.name + '”',
    '匹配 ' + matchedCount + '/' + rosterPlayers.length + ' 名团队玩家 · 读取 ' + selected.players.length + ' 条数据',
    'CSV 未编队 ' + csvOnlyCount + ' 人 · 团队缺少数据 ' + missingCount + ' 人',
    '候选匹配：' + scoreLine
  ].concat(selected.warnings || [])
  if (!matchedCount) lines.push('警告：没有玩家与当前团队匹配，已按文件顺序选择第一个帮会')

  candidate.lastImportReport = {
    kind: 'csv', title: '比赛数据导入成功', source: sourceName || '比赛数据.csv',
    importedAt: nowText(), tone: matchedCount ? 'success' : 'warning', lines: lines,
    camps: selection.scores
  }
  return commit(candidate)
}

S.getSampleTeamConfig = function () {
  const playerMap = {}
  DATA.players.forEach(function (player) { playerMap[player.id] = player })
  const groups = []
  DATA.teams.forEach(function (team) {
    let group = groups.find(function (item) { return item.name === team.group })
    if (!group) { group = { name: team.group, teams: [] }; groups.push(group) }
    group.teams.push({
      name: team.name,
      players: (team.playerIds || []).map(function (id) {
        const player = playerMap[id]
        return { name: player.name, aliases: clone(player.aliases || []) }
      })
    })
  })
  return { version: 1, groups: groups }
}

module.exports = {
  DATA: DATA, store: S, clone: clone, uid: uid,
  normalizeName: Importer.normalizeName, toNumber: toNumber,
  formatNumber: formatNumber, zeroMetric: zeroMetric, metricValue: metricValue,
  addMetric: addMetric, formatMetric: formatMetric, metricSortValue: metricSortValue
}
