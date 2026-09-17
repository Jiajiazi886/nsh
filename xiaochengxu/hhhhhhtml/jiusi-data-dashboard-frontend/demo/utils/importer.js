const CSV_COLUMNS = [
  '玩家名字',
  '职业',
  '击败/清泉',
  '助攻',
  '资源',
  '对玩家伤害',
  '人伤卸甲',
  '对建筑伤害',
  '破塔卸甲',
  '治疗值',
  '承受伤害',
  '重伤',
  '复活/清泉',
  '焚骨'
]

const METRICS = [
  { id: 'kills_spring', label: '击败/清泉', kind: 'pair', aggregate: 'sum' },
  { id: 'assists', label: '助攻', kind: 'number', aggregate: 'sum' },
  { id: 'resource', label: '资源', kind: 'number', aggregate: 'sum' },
  { id: 'player_damage', label: '对玩家伤害', kind: 'number', aggregate: 'sum' },
  { id: 'player_armor_break', label: '人伤卸甲', kind: 'number', aggregate: 'sum' },
  { id: 'structure_damage', label: '对建筑伤害', kind: 'number', aggregate: 'sum' },
  { id: 'tower_armor_break', label: '破塔卸甲', kind: 'number', aggregate: 'sum' },
  { id: 'healing', label: '治疗值', kind: 'number', aggregate: 'sum' },
  { id: 'damage_taken', label: '承受伤害', kind: 'number', aggregate: 'sum' },
  { id: 'deaths', label: '重伤', kind: 'number', aggregate: 'sum' },
  { id: 'revive_spring', label: '复活/清泉', kind: 'number', aggregate: 'sum' },
  { id: 'burn_bone', label: '焚骨', kind: 'number', aggregate: 'sum' }
]

function normalizeName(value) {
  return String(value == null ? '' : value)
    .replace(/^\uFEFF/, '')
    .trim()
    .toLowerCase()
    .replace(/[丶丷·•・\s]+$/g, '')
    .replace(/\s+/g, '')
}

function cleanText(value) {
  return String(value == null ? '' : value).replace(/^\uFEFF/, '').trim()
}

function uniqueStrings(values) {
  const seen = {}
  const out = []
  ;(values || []).forEach(function (value) {
    const text = cleanText(value)
    const key = normalizeName(text)
    if (!key || seen[key]) return
    seen[key] = true
    out.push(text)
  })
  return out
}

function parseCsvRows(text) {
  const source = String(text == null ? '' : text).replace(/^\uFEFF/, '')
  const rows = []
  let row = []
  let cell = ''
  let quoted = false

  for (let i = 0; i < source.length; i++) {
    const ch = source[i]
    if (quoted) {
      if (ch === '"') {
        if (source[i + 1] === '"') {
          cell += '"'
          i++
        } else {
          quoted = false
        }
      } else {
        cell += ch
      }
      continue
    }

    if (ch === '"') {
      quoted = true
    } else if (ch === ',') {
      row.push(cell)
      cell = ''
    } else if (ch === '\r' || ch === '\n') {
      row.push(cell)
      cell = ''
      if (row.some(function (value) { return cleanText(value) !== '' })) rows.push(row)
      row = []
      if (ch === '\r' && source[i + 1] === '\n') i++
    } else {
      cell += ch
    }
  }

  if (quoted) throw new Error('CSV 中存在未闭合的双引号')
  if (cell !== '' || row.length) {
    row.push(cell)
    if (row.some(function (value) { return cleanText(value) !== '' })) rows.push(row)
  }
  return rows
}

function parseStrictNumber(value, location) {
  const raw = cleanText(value).replace(/,/g, '')
  if (raw === '') return 0
  if (!/^[+-]?(?:\d+\.?\d*|\.\d+)$/.test(raw)) {
    throw new Error(location + '不是有效数字：' + cleanText(value))
  }
  const number = Number(raw)
  if (!isFinite(number)) throw new Error(location + '超出可处理范围')
  return number
}

function parseMetricValue(value, metric, location) {
  if (metric.kind !== 'pair') return parseStrictNumber(value, location)
  const parts = cleanText(value).split('/')
  if (parts.length !== 2) throw new Error(location + '必须是“数字/数字”格式')
  return {
    a: parseStrictNumber(parts[0], location),
    b: parseStrictNumber(parts[1], location)
  }
}

function assertCsvHeader(cells, lineNo) {
  if (cells.length !== CSV_COLUMNS.length) {
    throw new Error('CSV 第 ' + lineNo + ' 行字段数量不正确，应为 ' + CSV_COLUMNS.length + ' 列')
  }
  for (let i = 0; i < CSV_COLUMNS.length; i++) {
    if (cleanText(cells[i]) !== CSV_COLUMNS[i]) {
      throw new Error('CSV 第 ' + lineNo + ' 行第 ' + (i + 1) + ' 列应为“' + CSV_COLUMNS[i] + '”')
    }
  }
}

function finalizeCamp(camp) {
  if (!camp.headerLine) throw new Error('帮会“' + camp.name + '”缺少玩家字段头')
  if (!camp.rawRows.length) throw new Error('帮会“' + camp.name + '”没有玩家数据')

  const seen = {}
  const players = camp.rawRows.map(function (entry, index) {
    const cells = entry.cells
    const lineNo = entry.lineNo
    if (cells.length !== CSV_COLUMNS.length) {
      throw new Error('CSV 第 ' + lineNo + ' 行字段数量不正确，应为 ' + CSV_COLUMNS.length + ' 列')
    }
    const name = cleanText(cells[0])
    if (!name) throw new Error('CSV 第 ' + lineNo + ' 行缺少玩家名字')
    const key = normalizeName(name)
    if (seen[key]) throw new Error('帮会“' + camp.name + '”存在重复玩家：' + name)
    seen[key] = true

    const stats = {}
    METRICS.forEach(function (metric, metricIndex) {
      stats[metric.id] = parseMetricValue(
        cells[metricIndex + 2],
        metric,
        'CSV 第 ' + lineNo + ' 行“' + metric.label + '”'
      )
    })
    return {
      sourceIndex: index,
      name: name,
      role: cleanText(cells[1]) || '未知',
      stats: stats
    }
  })

  const warnings = []
  if (camp.declaredCount !== players.length) {
    warnings.push('“' + camp.name + '”声明 ' + camp.declaredCount + ' 人，实际读取 ' + players.length + ' 人')
  }
  return {
    name: camp.name,
    declaredCount: camp.declaredCount,
    players: players,
    warnings: warnings,
    sourceIndex: camp.sourceIndex
  }
}

function parseCsvCamps(text) {
  const rows = parseCsvRows(text)
  const camps = []
  let current = null

  rows.forEach(function (rawCells, index) {
    const cells = rawCells.map(cleanText)
    const lineNo = index + 1
    if (cells.length === 2 && cells[0] && /^\d+$/.test(cells[1])) {
      current = {
        name: cells[0],
        declaredCount: Number(cells[1]),
        headerLine: 0,
        rawRows: [],
        sourceIndex: camps.length
      }
      camps.push(current)
      return
    }
    if (cells[0] === '玩家名字') {
      if (!current) throw new Error('CSV 第 ' + lineNo + ' 行之前缺少“帮会名,人数”')
      assertCsvHeader(cells, lineNo)
      current.headerLine = lineNo
      return
    }
    if (current && !current.headerLine && cells.length === CSV_COLUMNS.length) {
      throw new Error('CSV 第 ' + lineNo + ' 行应为固定字段头，第一列必须是“玩家名字”')
    }
    if (!current || !current.headerLine) {
      throw new Error('CSV 第 ' + lineNo + ' 行无法识别，请检查帮会区块格式')
    }
    current.rawRows.push({ cells: cells, lineNo: lineNo })
  })

  if (!camps.length) throw new Error('没有识别到“帮会名,人数”数据区块')
  return camps.map(finalizeCamp)
}

function buildIdentityIndex(players) {
  const index = {}
  ;(players || []).forEach(function (player) {
    const identities = [player.name].concat(player.aliases || [])
    identities.forEach(function (identity) {
      const key = normalizeName(identity)
      if (!key) return
      if (index[key] && index[key].id !== player.id) {
        throw new Error('玩家名称或别名冲突：“' + identity + '”同时指向多个玩家')
      }
      index[key] = player
    })
  })
  return index
}

function scoreCamp(camp, rosterPlayers) {
  const index = buildIdentityIndex(rosterPlayers)
  const matchedIds = {}
  camp.players.forEach(function (player) {
    const match = index[normalizeName(player.name)]
    if (match) matchedIds[match.id] = true
  })
  const matchedCount = Object.keys(matchedIds).length
  return {
    name: camp.name,
    declaredCount: camp.declaredCount,
    actualCount: camp.players.length,
    matchedCount: matchedCount,
    matchRate: rosterPlayers.length ? matchedCount / rosterPlayers.length : 0,
    sourceIndex: camp.sourceIndex,
    warnings: camp.warnings.slice()
  }
}

function selectBestCamp(camps, rosterPlayers) {
  if (!camps || !camps.length) throw new Error('没有可选择的帮会数据')
  const scores = camps.map(function (camp) { return scoreCamp(camp, rosterPlayers || []) })
  const ranked = scores.slice().sort(function (a, b) {
    return (b.matchedCount - a.matchedCount) ||
      (b.matchRate - a.matchRate) ||
      (a.sourceIndex - b.sourceIndex)
  })
  const selectedScore = ranked[0]
  return {
    camp: camps[selectedScore.sourceIndex],
    selectedScore: selectedScore,
    scores: scores
  }
}

function parsePlayerConfig(value, location) {
  if (typeof value === 'string') {
    const simpleName = cleanText(value)
    if (!simpleName) throw new Error(location + '的玩家名字不能为空')
    return { name: simpleName, aliases: [] }
  }
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(location + '必须是玩家对象或玩家名字字符串')
  }
  const name = cleanText(value.name)
  if (!name) throw new Error(location + '缺少 name')
  if (value.aliases !== undefined && !Array.isArray(value.aliases)) {
    throw new Error(location + '.aliases 必须是数组')
  }
  return { name: name, aliases: uniqueStrings(value.aliases || []) }
}

function parseTeamConfig(input) {
  let config = input
  if (typeof input === 'string') {
    try {
      config = JSON.parse(input.replace(/^\uFEFF/, ''))
    } catch (error) {
      throw new Error('JSON 解析失败：' + error.message)
    }
  }
  if (!config || typeof config !== 'object' || Array.isArray(config)) {
    throw new Error('团队配置顶层必须是 JSON 对象')
  }
  if (config.version !== undefined && Number(config.version) !== 1) {
    throw new Error('不支持的团队配置版本：' + config.version)
  }
  if (!Array.isArray(config.groups) || !config.groups.length) {
    throw new Error('团队配置缺少非空 groups 数组')
  }

  const groupNames = {}
  const identityOwners = {}
  let teamCount = 0
  let playerCount = 0

  const groups = config.groups.map(function (group, groupIndex) {
    const groupLocation = 'groups[' + groupIndex + ']'
    if (!group || typeof group !== 'object' || Array.isArray(group)) {
      throw new Error(groupLocation + '必须是对象')
    }
    const name = cleanText(group.name)
    if (!name) throw new Error(groupLocation + '缺少 name')
    const groupKey = normalizeName(name)
    if (groupNames[groupKey]) throw new Error('团名重复：' + name)
    groupNames[groupKey] = true
    if (!Array.isArray(group.teams) || !group.teams.length) {
      throw new Error('团“' + name + '”缺少非空 teams 数组')
    }

    const teamNames = {}
    const teams = group.teams.map(function (team, teamIndex) {
      const teamLocation = groupLocation + '.teams[' + teamIndex + ']'
      if (!team || typeof team !== 'object' || Array.isArray(team)) {
        throw new Error(teamLocation + '必须是对象')
      }
      const teamName = cleanText(team.name)
      if (!teamName) throw new Error(teamLocation + '缺少 name')
      const teamKey = normalizeName(teamName)
      if (teamNames[teamKey]) throw new Error('团“' + name + '”中的队名重复：' + teamName)
      teamNames[teamKey] = true
      if (!Array.isArray(team.players) || !team.players.length) {
        throw new Error('队伍“' + name + ' · ' + teamName + '”缺少非空 players 数组')
      }

      const players = team.players.map(function (player, playerIndex) {
        const parsed = parsePlayerConfig(player, teamLocation + '.players[' + playerIndex + ']')
        const identities = [parsed.name].concat(parsed.aliases)
        const playerOwner = name + ' · ' + teamName + ' · ' + parsed.name
        identities.forEach(function (identity) {
          const identityKey = normalizeName(identity)
          if (!identityKey) throw new Error('玩家名称或别名不能为空')
          const owner = identityOwners[identityKey]
          if (owner && owner !== playerOwner) {
            throw new Error('玩家名称或别名重复：“' + identity + '”已属于“' + owner + '”')
          }
          identityOwners[identityKey] = playerOwner
        })
        playerCount++
        return parsed
      })
      teamCount++
      return { name: teamName, players: players }
    })
    return { name: name, teams: teams }
  })

  return {
    version: 1,
    groups: groups,
    groupCount: groups.length,
    teamCount: teamCount,
    playerCount: playerCount
  }
}

module.exports = {
  CSV_COLUMNS: CSV_COLUMNS,
  METRICS: METRICS,
  normalizeName: normalizeName,
  parseCsvRows: parseCsvRows,
  parseCsvCamps: parseCsvCamps,
  buildIdentityIndex: buildIdentityIndex,
  scoreCamp: scoreCamp,
  selectBestCamp: selectBestCamp,
  parseTeamConfig: parseTeamConfig
}
