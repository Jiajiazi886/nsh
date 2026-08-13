export const ATTACK_PANEL_JSON_FIELDS = [
  ['攻击', 'attack'],
  ['破防', 'breakDefense'],
  ['克制数值', 'restraintValue'],
  ['会心', 'crit'],
  ['会伤增幅', 'critDmg'],
  ['额外会心率', 'extraCritRate'],
  ['流派克制百分比', 'restraintPct'],
  ['技能增强', 'skillBonus'],
  ['技能增强百分比', 'skillBonusPct'],
  ['技巧克制', 'techniqueRestraint'],
  ['内功增伤', 'internalBonus'],
  ['装备增伤', 'gearBonus'],
  ['武蕴增伤', 'martialBonus'],
  ['其他增伤', 'otherBonus']
]

export const ATTACK_PANEL_JSON_EXAMPLE = {
  面板名称: '联赛标准面板',
  状态: '启用',
  备注: '',
  攻击: 1750,
  破防: 1100,
  克制数值: 285,
  会心: 2100,
  会伤增幅: 0.575,
  额外会心率: 0,
  流派克制百分比: 0,
  技能增强: 0,
  技能增强百分比: 0,
  技巧克制: 0,
  内功增伤: 0,
  装备增伤: 0,
  武蕴增伤: 0,
  其他增伤: 0
}

export function parseAttackPanelJson(text, { requireMetadata = true } = {}) {
  let value
  try {
    value = JSON.parse(String(text || '').trim())
  } catch {
    throw new Error('JSON 格式不正确，请检查逗号、引号和括号')
  }
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error('JSON 根结构必须是单个面板对象')
  }

  const result = {}
  if (requireMetadata) {
    const panelName = String(value['面板名称'] ?? '').trim()
    if (!panelName) throw new Error('“面板名称”不能为空')
    if (panelName.length > 100) throw new Error('“面板名称”不能超过 100 个字符')
    if (!['启用', '停用'].includes(value['状态'])) throw new Error('“状态”只能填写“启用”或“停用”')
    result.panelName = panelName
    result.status = value['状态'] === '停用' ? '1' : '0'
    result.remark = String(value['备注'] ?? '').slice(0, 500)
  }

  for (const [label, key] of ATTACK_PANEL_JSON_FIELDS) {
    if (!(label in value)) throw new Error(`缺少必填字段“${label}”`)
    const number = Number(value[label])
    if (!Number.isFinite(number) || number < 0) throw new Error(`“${label}”必须是大于或等于 0 的数字`)
    result[key] = number
  }
  return result
}

export function attackPanelToJsonObject(panel = {}, { includeMetadata = true } = {}) {
  const result = {}
  if (includeMetadata) {
    result['面板名称'] = String(panel.panelName || '攻击方面板')
    result['状态'] = panel.status === '1' ? '停用' : '启用'
    result['备注'] = String(panel.remark || '')
  }
  for (const [label, key] of ATTACK_PANEL_JSON_FIELDS) {
    const value = Number(panel[key])
    result[label] = Number.isFinite(value) && value >= 0 ? value : 0
  }
  return result
}

export function formatAttackPanelJson(panel, options) {
  return JSON.stringify(attackPanelToJsonObject(panel, options), null, 2)
}

export function formatAttackPanelJsonExample() {
  return JSON.stringify(ATTACK_PANEL_JSON_EXAMPLE, null, 2)
}
