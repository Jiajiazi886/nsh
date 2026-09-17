const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')

const Importer = require('../utils/importer')

const PROJECT_ROOT = path.resolve(__dirname, '..')
const SAMPLE_JSON_PATH = path.join(PROJECT_ROOT, 'data', '团队配置示例.json')
const PROVIDED_CSV_PATH = process.env.JIUSI_SAMPLE_CSV || ''

const HEADER = Importer.CSV_COLUMNS.map(value => JSON.stringify(value)).join(',')

function csvPlayer(name, role, seed) {
  const values = [
    name, role, seed + '/' + (seed + 1), seed + 2, 0, seed + 3,
    0, seed + 4, 0, seed + 5, seed + 6, seed + 7, seed + 8, 0
  ]
  return values.map(value => JSON.stringify(String(value))).join(',')
}

function twoCampCsv() {
  return [
    '"对手帮会","2"', HEADER,
    csvPlayer('陌生甲', '神相', 1), csvPlayer('陌生乙', '素问', 2),
    '"༺九肆✈","2"', HEADER,
    csvPlayer('封不觉', '龙吟', 3), csvPlayer('万斯琳', '潮光', 4)
  ].join('\r\n')
}

function loadFreshStore(memory) {
  global.wx = {
    getStorageSync(key) { return memory[key] || '' },
    setStorageSync(key, value) { memory[key] = value }
  }
  const storePath = require.resolve('../utils/store')
  delete require.cache[storePath]
  return require('../utils/store').store
}

test('完整团队示例包含 3 个团、10 支队伍、60 名唯一玩家', () => {
  const parsed = Importer.parseTeamConfig(fs.readFileSync(SAMPLE_JSON_PATH, 'utf8'))
  assert.equal(parsed.groupCount, 3)
  assert.equal(parsed.teamCount, 10)
  assert.equal(parsed.playerCount, 60)
})

test('名称标准化支持空格、尾部点号和别名', () => {
  assert.equal(Importer.normalizeName('  万 斯 琳丶 '), '万斯琳')
  const roster = [{ id: 'p1', name: '封不覺', aliases: ['封不觉'] }]
  const camp = Importer.parseCsvCamps([
    '"测试","1"', HEADER, csvPlayer('封不觉', '龙吟', 1)
  ].join('\n'))[0]
  assert.equal(Importer.scoreCamp(camp, roster).matchedCount, 1)
})

test('多帮会 CSV 自动选择团队匹配人数最多的帮会', () => {
  const config = Importer.parseTeamConfig(fs.readFileSync(SAMPLE_JSON_PATH, 'utf8'))
  const roster = []
  let id = 0
  config.groups.forEach(group => group.teams.forEach(team => team.players.forEach(player => {
    roster.push({ id: 'p' + (++id), name: player.name, aliases: player.aliases })
  })))
  const camps = Importer.parseCsvCamps(twoCampCsv())
  const selection = Importer.selectBestCamp(camps, roster)
  assert.equal(selection.camp.name, '༺九肆✈')
  assert.equal(selection.selectedScore.matchedCount, 2)
  assert.deepEqual(selection.scores.map(score => score.matchedCount), [0, 2])
})

test('团队配置拒绝玩家跨队重复', () => {
  const invalid = {
    version: 1,
    groups: [{
      name: '一团',
      teams: [
        { name: '一队', players: [{ name: '同名玩家', aliases: [] }] },
        { name: '二队', players: [{ name: '同名玩家丶', aliases: [] }] }
      ]
    }]
  }
  assert.throws(() => Importer.parseTeamConfig(invalid), /重复/)
})

test('CSV 拒绝错误表头和非法数值', () => {
  const badHeader = '"帮会","1"\n' + HEADER.replace('玩家名字', '角色名字') + '\n' + csvPlayer('玩家', '素问', 1)
  assert.throws(() => Importer.parseCsvCamps(badHeader), /玩家名字/)

  const badRow = csvPlayer('玩家', '素问', 1).replace('"3"', '"不是数字"')
  assert.throws(() => Importer.parseCsvCamps('"帮会","1"\n' + HEADER + '\n' + badRow), /有效数字/)
})

test('团队和 CSV 可按任意顺序导入，且失败不会污染旧状态', () => {
  const memory = {}
  const store = loadFreshStore(memory)
  store.load()
  const sample = fs.readFileSync(SAMPLE_JSON_PATH, 'utf8')

  store.importTeamConfig(sample, '团队配置示例.json')
  const csvReport = store.importCsv(twoCampCsv(), '双帮会.csv')
  assert.equal(csvReport.kind, 'csv')
  assert.equal(store.getState().dataset.name, '༺九肆✈')
  assert.equal(store.matchSummary().matchedCount, 2)

  const before = JSON.stringify(store.getState())
  assert.throws(() => store.importCsv('损坏的 CSV', 'bad.csv'))
  assert.equal(JSON.stringify(store.getState()), before)

  const teamReport = store.importTeamConfig(sample, '团队配置示例.json')
  assert.equal(teamReport.kind, 'teams')
  assert.equal(store.getState().boxes.length, 1)
  assert.equal(store.getState().boxes[0].name, '全部队员')
  assert.equal(store.matchSummary().matchedCount, 2)
})

test('v2 本地状态会迁移到 v3 且保留旧键', () => {
  const data = require('../data/data')
  const legacy = JSON.parse(JSON.stringify(data))
  const memory = { jiusi_mp_state_v2: JSON.stringify(legacy) }
  const store = loadFreshStore(memory)
  const state = store.load()
  assert.equal(state.version, 3)
  assert.ok(memory.jiusi_mp_state_v2)
  assert.ok(memory.jiusi_mp_state_v3)
})

test('用户提供的双帮会 CSV 实际匹配为九肆 60、月野 0', {
  skip: !PROVIDED_CSV_PATH || !fs.existsSync(PROVIDED_CSV_PATH)
}, () => {
  const memory = {}
  const store = loadFreshStore(memory)
  store.load()
  const report = store.importCsv(fs.readFileSync(PROVIDED_CSV_PATH, 'utf8'), path.basename(PROVIDED_CSV_PATH))
  assert.equal(store.getState().dataset.name, '༺九肆✈')
  assert.equal(store.matchSummary().matchedCount, 60)
  assert.deepEqual(report.camps.map(camp => [camp.name, camp.actualCount, camp.matchedCount]), [
    ['༺九肆✈', 60, 60],
    ['月野☽', 60, 0]
  ])
})
