const REQUIRED_HEADERS = [
  '玩家名字', '职业', '击败/清泉', '助攻', '资源', '对玩家伤害', '人伤卸甲',
  '对建筑伤害', '破塔卸甲', '治疗值', '承受伤害', '重伤', '复活/清泉', '焚骨'
]

const SIMPLE_FIELDS = [
  ['助攻', 'assists'], ['资源', 'resources'], ['对玩家伤害', 'dmg_to_players'],
  ['人伤卸甲', 'armor_break_players'], ['对建筑伤害', 'dmg_to_buildings'],
  ['破塔卸甲', 'armor_break_buildings'], ['治疗值', 'healing'],
  ['承受伤害', 'dmg_taken'], ['重伤', 'deaths'], ['复活/清泉', 'revives'], ['焚骨', 'burn_bones']
]

function rows(text) {
  const source = String(text || '').replace(/^\uFEFF/, '')
  const result = []
  let row = [], cell = '', quoted = false
  for (let i = 0; i < source.length; i += 1) {
    const char = source[i]
    if (char === '"') {
      if (quoted && source[i + 1] === '"') { cell += '"'; i += 1 }
      else quoted = !quoted
    } else if (char === ',' && !quoted) {
      row.push(cell.trim()); cell = ''
    } else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && source[i + 1] === '\n') i += 1
      row.push(cell.trim())
      if (row.some(Boolean)) result.push(row)
      row = []; cell = ''
    } else cell += char
  }
  if (quoted) throw new Error('CSV 引号没有正确闭合')
  row.push(cell.trim())
  if (row.some(Boolean)) result.push(row)
  return result
}

function decimal(value, label, line) {
  const normalized = String(value ?? '').trim().replaceAll(',', '')
  if (!/^[0-9]+$/.test(normalized)) throw new Error(`第 ${line} 行“${label}”是非法数值`)
  return normalized
}

function pair(value, label, line) {
  const parts = String(value ?? '').trim().split('/')
  if (parts.length !== 2) throw new Error(`第 ${line} 行“${label}”格式应为 数字/数字`)
  return parts.map(part => decimal(part, label, line))
}

function headerMap(row, line) {
  const missing = REQUIRED_HEADERS.filter(name => !row.includes(name))
  if (missing.length) throw new Error(`第 ${line} 行缺少固定字段：${missing.join('、')}`)
  return Object.fromEntries(REQUIRED_HEADERS.map(name => [name, row.indexOf(name)]))
}

function guildHeader(row) {
  if (row.length !== 2 || !row[0] || !/^[0-9]+$/.test(row[1])) return null
  return { name: row[0], declaredCount: Number(row[1]) }
}

export function parseBattleCsv(text) {
  const sourceRows = rows(text)
  if (!sourceRows.length) throw new Error('CSV 文件为空')
  const guilds = []
  const records = []
  const warnings = []
  const duplicateKeys = new Set()
  let currentGuild = null
  let columns = null

  sourceRows.forEach((row, index) => {
    const line = index + 1
    const guild = guildHeader(row)
    if (guild) {
      currentGuild = { ...guild, actualCount: 0 }
      guilds.push(currentGuild)
      columns = null
      return
    }
    if (row[0] === '玩家名字') {
      if (!currentGuild) throw new Error(`第 ${line} 行表头前缺少帮会名称和人数`)
      columns = headerMap(row, line)
      return
    }
    if (!currentGuild || !columns) throw new Error(`第 ${line} 行无法确定所属帮会或固定表头`)
    const name = String(row[columns['玩家名字']] || '').trim()
    const profession = String(row[columns['职业']] || '').trim()
    if (!name) throw new Error(`第 ${line} 行玩家名字不能为空`)
    if (!profession) throw new Error(`第 ${line} 行职业不能为空`)
    const duplicateKey = `${currentGuild.name}\u0000${name.replaceAll(' ', '')}`
    if (duplicateKeys.has(duplicateKey)) throw new Error(`第 ${line} 行存在重复玩家：${name}`)
    duplicateKeys.add(duplicateKey)
    const [kills, qingquanKills] = pair(row[columns['击败/清泉']], '击败/清泉', line)
    const record = {
      guild_name: currentGuild.name,
      player_name: name,
      player_class: profession,
      kills,
      qingquan_kills: qingquanKills,
    }
    for (const [header, field] of SIMPLE_FIELDS) record[field] = decimal(row[columns[header]], header, line)
    records.push(record)
    currentGuild.actualCount += 1
  })

  if (!guilds.length) throw new Error('CSV 中没有识别到帮会分段')
  if (!records.length) throw new Error('CSV 中没有可导入的玩家数据')
  for (const guild of guilds) {
    if (guild.declaredCount !== guild.actualCount) {
      warnings.push(`${guild.name} 声明 ${guild.declaredCount} 人，实际解析 ${guild.actualCount} 人`)
    }
  }
  return { guilds, records, warnings }
}

export function inferBattleFileInfo(filename, fallbackDate = '') {
  const stem = String(filename || '').replace(/\.csv$/i, '')
  const parts = stem.split('_').map(part => part.trim()).filter(Boolean)
  const rawDate = /^\d{8}$/.test(parts[0] || '') ? parts[0] : ''
  const battleDate = rawDate ? `${rawDate.slice(0, 4)}-${rawDate.slice(4, 6)}-${rawDate.slice(6, 8)}` : fallbackDate
  return {
    battleDate,
    myGuildName: parts.length >= 3 ? parts[parts.length - 2] : '',
    opponentName: parts.length >= 2 ? parts[parts.length - 1] : '',
  }
}

export { REQUIRED_HEADERS }
