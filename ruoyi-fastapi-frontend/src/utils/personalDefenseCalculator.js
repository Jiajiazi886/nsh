export const ZHOU_TIAN_OPTIONS = ['金火', '火木', '金木']

export const ENTRY_FIELDS = [
  { row: 3, name: '赛年', defaultValue: 0, formula: C => 0.88 * C[3] },
  { row: 4, name: '力量/气海', defaultValue: 0, maxValue: 10, formula: C => 2.5 * C[4] * 0.0455 + C[4] * 0.0425 },
  { row: 5, name: '攻击', defaultValue: 0, maxValue: 33, formula: C => 0.0455 * C[5] },
  { row: 6, name: '破防', defaultValue: 0, maxValue: 33, formula: C => C[6] * 0.0425 },
  { row: 7, name: '流派克制', defaultValue: 0, maxValue: 1.2, formula: C => C[7] },
  { row: 8, name: '会心', defaultValue: 0, maxValue: 66, formula: C => C[8] * 0.0182 },
  { row: 9, name: '最大攻击', defaultValue: 0, maxValue: 36, formula: C => 0.0455 * C[9] / 2 },
  { row: 10, name: '最小攻击', defaultValue: 0, maxValue: 36, formula: C => 0.0455 * C[10] / 2 },
  { row: 11, name: '身法', defaultValue: 0, maxValue: 10, formula: C => C[11] * 0.0182 * 6 },
  { row: 12, name: '耐力', defaultValue: 0, maxValue: 10, formula: C => C[12] * 0.0455 },
  { row: 13, name: '根骨', defaultValue: 0, maxValue: 10, formula: C => C[13] * 0.0455 },
  {
    row: 14,
    name: '灼星贯日-灵',
    defaultValue: 0,
    formula: (C, helpers) => C[14] * (1.875 + 0.1 * (5.5 + helpers.zhongMiao + helpers.jueDian))
  },
  { row: 15, name: '承影锋镝-灵', defaultValue: 0, formula: C => C[15] * 3 },
  { row: 16, name: '绝电惊沙-灵', defaultValue: 0, formula: C => C[16] * 2.46 },
  { row: 17, name: '日月两仪-灵', defaultValue: 0, formula: C => C[17] * 2.2 },
  { row: 18, name: '楚狂歌-灵', defaultValue: 0, formula: C => C[18] * 1.78 },
  { row: 19, name: '众妙-灵', defaultValue: 0, formula: C => C[19] * 1.75 },
  { row: 20, name: '焚刃-灵', defaultValue: 0, formula: C => C[20] * 1.65 },
  { row: 21, name: '斩精-灵', defaultValue: 0, formula: C => C[21] * 1.6 },
  { row: 22, name: '破釜-灵', defaultValue: 0, formula: C => C[22] * 1.6 },
  { row: 23, name: '贯山月(卡轴)-灵', defaultValue: 0, formula: C => C[23] * 1.63 },
  { row: 24, name: '锻寒芒-灵', defaultValue: 0, formula: C => C[24] * 1.65 },
  { row: 25, name: '击衰-灵', defaultValue: 0, formula: C => C[25] * 1.4 },
  { row: 26, name: '惊羽-灵', defaultValue: 0, formula: C => C[26] * 1.6 },
  { row: 27, name: '裁锋-灵', defaultValue: 0, formula: C => C[27] * 1.65 },
  { row: 28, name: '五韵谣-灵', defaultValue: 0, formula: C => C[28] * 1.3 }
]

export const TRAIT_FIELDS = [
  { row: 3, name: '灼星贯日', defaultValue: true },
  { row: 4, name: '承影锋镝', defaultValue: true, fixedGain: 6 },
  { row: 5, name: '绝电惊沙', defaultValue: true, fixedGain: 5.5 },
  { row: 6, name: '日月两仪', defaultValue: false, fixedGain: 4.9 },
  { row: 7, name: '楚狂歌', defaultValue: true, fixedGain: 5.4 },
  { row: 8, name: '众妙', defaultValue: true, fixedGain: 5.25 },
  { row: 9, name: '焚刃', defaultValue: false, fixedGain: 5 },
  { row: 10, name: '斩精', defaultValue: false, fixedGain: 4.8 },
  { row: 11, name: '破釜', defaultValue: false, fixedGain: 4.8 },
  { row: 12, name: '贯山月(卡轴)', defaultValue: false, fixedGain: 4.9 },
  { row: 13, name: '锻寒芒', defaultValue: false, fixedGain: 4.8 },
  { row: 14, name: '击衰', defaultValue: false, fixedGain: 4.2 },
  { row: 15, name: '惊羽', defaultValue: false, fixedGain: 4.8 },
  { row: 16, name: '裁锋', defaultValue: true, fixedGain: 5 },
  { row: 17, name: '五韵谣', defaultValue: false, fixedGain: 1.75 }
]

export function isSpiritEntryField(name) {
  return String(name || '').endsWith('-灵')
}

export const DEFENSE_CALCULATOR_EXAMPLE = {
  '周天': '火木',
  '词条': {
    '赛年': 0,
    '力量/气海': 10,
    '攻击': 120,
    '破防': 80,
    '流派克制': 1.2,
    '会心': 66,
    '最大攻击': 36,
    '最小攻击': 36,
    '身法': 10,
    '耐力': 10,
    '根骨': 10,
    '灼星贯日-灵': 1,
    '承影锋镝-灵': 1,
    '绝电惊沙-灵': 1,
    '日月两仪-灵': 0,
    '楚狂歌-灵': 1,
    '众妙-灵': 1,
    '焚刃-灵': 0,
    '斩精-灵': 0,
    '破釜-灵': 0,
    '贯山月(卡轴)-灵': 0,
    '锻寒芒-灵': 0,
    '击衰-灵': 0,
    '惊羽-灵': 0,
    '裁锋-灵': 1,
    '五韵谣-灵': 0
  },
  '特性': {
    '灼星贯日': true,
    '承影锋镝': true,
    '绝电惊沙': true,
    '日月两仪': false,
    '楚狂歌': true,
    '众妙': true,
    '焚刃': false,
    '斩精': false,
    '破釜': false,
    '贯山月(卡轴)': false,
    '锻寒芒': false,
    '击衰': false,
    '惊羽': false,
    '裁锋': true,
    '五韵谣': false
  }
}

export function createDefaultDefenseInput() {
  return {
    '周天': '火木',
    '词条': Object.fromEntries(ENTRY_FIELDS.map(field => [field.name, field.defaultValue])),
    '特性': Object.fromEntries(TRAIT_FIELDS.map(field => [field.name, field.defaultValue]))
  }
}

export function normalizeDefenseInput(value = {}) {
  const source = isPlainObject(value) ? value : {}
  const sourceEntries = isPlainObject(source['词条']) ? source['词条'] : {}
  const sourceTraits = isPlainObject(source['特性']) ? source['特性'] : {}
  const zhouTian = ZHOU_TIAN_OPTIONS.includes(source['周天']) ? source['周天'] : '火木'

  return {
    '周天': zhouTian,
    '词条': Object.fromEntries(
      ENTRY_FIELDS.map(field => [field.name, parseNumber(sourceEntries[field.name], field.defaultValue)])
    ),
    '特性': Object.fromEntries(
      TRAIT_FIELDS.map(field => [field.name, parseBoolean(sourceTraits[field.name], field.defaultValue)])
    )
  }
}

export function calculatePersonalDefense(input = createDefaultDefenseInput()) {
  const normalizedInput = normalizeDefenseInput(input)
  const C = Object.fromEntries(
    ENTRY_FIELDS.map(field => [field.row, normalizedInput['词条'][field.name]])
  )
  const traitsByRow = Object.fromEntries(
    TRAIT_FIELDS.map(field => [field.row, normalizedInput['特性'][field.name]])
  )
  const helpers = {
    zhongMiao: C[19] === 1 ? 7 : (traitsByRow[8] ? 5.25 : 0),
    jueDian: C[16] === 1 ? 8 : (traitsByRow[5] ? 5.5 : 0)
  }
  const traitGainByRow = {
    ...Object.fromEntries(TRAIT_FIELDS.filter(field => field.fixedGain != null).map(field => [field.row, field.fixedGain])),
    3: 3 + 0.2 * (5.5 + helpers.zhongMiao + helpers.jueDian)
  }
  const entryDetails = ENTRY_FIELDS.map(field => {
    const score = field.formula(C, helpers)
    const fullScore = field.maxValue == null ? null : field.formula({ ...C, [field.row]: field.maxValue }, helpers)
    return {
      '名称': field.name,
      '输入': round(normalizedInput['词条'][field.name]),
      '评分': round(score),
      '满词条输入': field.maxValue ?? null,
      '满词条评分': fullScore == null ? null : round(fullScore)
    }
  })
  const traitDetails = TRAIT_FIELDS.map(field => {
    const carried = normalizedInput['特性'][field.name]
    const gain = traitGainByRow[field.row] || 0
    return {
      '名称': field.name,
      '携带': carried,
      '收益': round(gain),
      '计数': carried ? 1 : 0
    }
  })
  const entryScore = entryDetails.reduce((sum, item) => sum + item['评分'], 0)
  const zhouTianBonus = getZhouTianBonus(normalizedInput['周天'])
  const traitScore = traitDetails.reduce((sum, item) => sum + item['收益'] * item['计数'], zhouTianBonus)

  return {
    summary: {
      '词条分': round(entryScore),
      '特性分': round(traitScore),
      '总分': round(entryScore + traitScore),
      '周天加成': round(zhouTianBonus)
    },
    '词条明细': entryDetails,
    '特性明细': traitDetails,
    normalizedInput
  }
}

export function getZhouTianBonus(value) {
  if (value === '火木') return 2.7
  if (value === '金木') return 2.8
  return 0
}

export function stringifyDefenseJson(value) {
  return JSON.stringify(value, null, 2)
}

function parseNumber(value, fallback = 0) {
  if (value === '' || value == null) return fallback
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

function parseBoolean(value, fallback = false) {
  if (value == null || value === '') return fallback
  if (typeof value === 'boolean') return value
  if (typeof value === 'number') return value === 1
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase()
    if (['true', '1', 'yes', 'y', '是'].includes(normalized)) return true
    if (['false', '0', 'no', 'n', '否'].includes(normalized)) return false
  }
  return Boolean(value)
}

function isPlainObject(value) {
  return Object.prototype.toString.call(value) === '[object Object]'
}

function round(value, precision = 4) {
  const factor = 10 ** precision
  return Math.round((Number(value) || 0) * factor) / factor
}
