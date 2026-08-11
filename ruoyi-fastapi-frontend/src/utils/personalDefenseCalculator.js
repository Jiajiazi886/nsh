export const DEFENDER_FIELDS = [
  { key: 'defense', label: '防御', step: 1 },
  { key: 'resist', label: '抵御', step: 1 },
  { key: 'critResist', label: '会心抵抗', step: 1 },
  { key: 'resistPct', label: '抵御百分比', step: 1, precision: 1, suffix: '%' },
  { key: 'hp', label: '血量', step: 100 },
  { key: 'critDefense', label: '会心防御', step: 0.1, suffix: '%' },
  { key: 'techniqueResist', label: '技巧克制', step: 1 },
  { key: 'internalReduction', label: '内功减伤', step: 0.001, precision: 3, suffix: '%' },
  { key: 'gearReduction', label: '装备减伤', step: 0.001, precision: 3, suffix: '%' },
  { key: 'martialReduction', label: '武蕴减伤', step: 0.001, precision: 3, suffix: '%' },
  { key: 'otherReduction', label: '其他减伤', step: 0.001, precision: 3, suffix: '%' }
]

export const INNER_POWER_FIELDS = [
  { key: 'rootBone', label: '根骨', step: 1 },
  { key: 'agility', label: '身法', step: 1 },
  { key: 'endurance', label: '耐力', step: 1 },
  { key: 'internalDefense', label: '内功防御', step: 1 },
  { key: 'externalDefense', label: '外功防御', step: 1 },
  { key: 'defense', label: '防御', step: 1 },
  { key: 'hp', label: '气血上限', step: 100 },
  { key: 'critResist', label: '抗会心', step: 1 },
  { key: 'internalCritResist', label: '抗内功会心', step: 1 },
  { key: 'externalCritResist', label: '抗外功会心', step: 1 },
  { key: 'resistPct', label: '流派抵御', step: 1, precision: 1, suffix: '%' },
  { key: 'critDefense', label: '会心防御', step: 0.1, suffix: '%' },
  { key: 'techniqueResist', label: '技巧克制', step: 1 }
]

export const DEFAULT_ATTACK_PANEL = {
  panelId: 0,
  panelName: '默认参考进攻面板',
  attack: 1750,
  breakDefense: 1100,
  restraintValue: 285,
  crit: 1100,
  critDmg: 0.575,
  extraCritRate: 0,
  restraintPct: 0,
  skillBonus: 0,
  skillBonusPct: 0,
  internalBonus: 0,
  gearBonus: 0,
  martialBonus: 0,
  otherBonus: 0,
  techniqueRestraint: 0
}

export const CUSTOM_ATTACK_PANEL_ID = -1

const DEFENSE_CALCULATOR_PANEL_STORAGE_KEY = 'personal-defense-calculator:panel-setting:v1'

const INTERNAL_POWER_DEFENSE_ENTRY_MAP = {
  '耐力': 'endurance',
  '根骨': 'rootBone',
  '身法': 'agility',
  '内功防御': 'internalDefense',
  '外功防御': 'externalDefense',
  '防御': 'defense',
  '气血上限': 'hp',
  '抗会心': 'critResist',
  '抗内功会心': 'internalCritResist',
  '抗外功会心': 'externalCritResist',
  '流派抵御': 'resistPct'
}

export function createDefaultDefender() {
  return {
    defense: 2550,
    resist: 0,
    critResist: 0,
    resistPct: 0,
    hp: 100000,
    critDefense: 0,
    techniqueResist: 0,
    internalReduction: 0,
    gearReduction: 0,
    martialReduction: 0,
    otherReduction: 0
  }
}

export function createEmptyInnerPowerEntries() {
  return Object.fromEntries(INNER_POWER_FIELDS.map(field => [field.key, 0]))
}

export function loadDefenseCalculatorPanelSetting() {
  try {
    const value = JSON.parse(window.localStorage.getItem(DEFENSE_CALCULATOR_PANEL_STORAGE_KEY) || '{}')
    return {
      defender: normalizeDefender(value.defender),
      selectedPanelId: number(value.selectedPanelId, 0),
      customAttackPanel: normalizeAttackPanel(value.customAttackPanel)
    }
  } catch {
    return {
      defender: createDefaultDefender(),
      selectedPanelId: 0,
      customAttackPanel: normalizeAttackPanel()
    }
  }
}

export function saveDefenseCalculatorPanelSetting(value = {}) {
  const previous = loadDefenseCalculatorPanelSetting()
  const setting = {
    defender: normalizeDefender(value.defender),
    selectedPanelId: number(value.selectedPanelId, 0),
    customAttackPanel: normalizeAttackPanel(value.customAttackPanel ?? previous.customAttackPanel)
  }
  try {
    window.localStorage.setItem(DEFENSE_CALCULATOR_PANEL_STORAGE_KEY, JSON.stringify(setting))
  } catch {
    // 本地存储不可用时仍允许防守计算器在当前页面继续使用。
  }
  return setting
}

export function calculateDefense(defenderInput, attackPanelInput) {
  const defender = normalizeDefender(defenderInput)
  const attackPanel = normalizeAttackPanel(attackPanelInput)
  const result = calculateSnapshot(defender, attackPanel)
  return {
    defender,
    attackPanel,
    ...result,
    defenseCurve: buildDefenseCurve(),
    defenseDerivativeCurve: buildDefenseDerivativeCurve(),
    critCurve: buildCritCurve(),
    critDerivativeCurve: buildCritDerivativeCurve()
  }
}

export function calculateInnerPowerComparisons(defenderInput, attackPanelInput, plans = []) {
  const base = calculateDefense(defenderInput, attackPanelInput)
  return {
    base,
    plans: plans.map(plan => {
      const build = calculateDefense(addEntries(base.defender, plan.entries, base.attackPanel), base.attackPanel)
      return { id: plan.id, ...comparisonItem(plan.name, build, base) }
    })
  }
}

export function calculateInternalPowerDefenseBenefit(entryInput = {}, defenderInput, attackPanelInput) {
  const entry = normalizeInternalPowerDefenseEntry(entryInput)
  if (!entry.supported) {
    return { id: entryInput.id, name: entry.name, value: entryInput.value, gain: 0, note: entry.note }
  }
  const base = calculateDefense(defenderInput, attackPanelInput)
  const upgraded = calculateDefense(addEntries(base.defender, entry.delta, base.attackPanel), base.attackPanel)
  return {
    id: entryInput.id,
    name: entry.name,
    value: entryInput.value,
    gain: percentGain(upgraded.durability, base.durability) / 100,
    note: ''
  }
}

export function calculateInternalPowerDefenseBenefits(power = {}, defenderInput, attackPanelInput) {
  const base = calculateDefense(defenderInput, attackPanelInput)
  const entries = Array.isArray(power.entries) ? power.entries : []
  const totalDelta = entries.reduce((delta, entry) => addInternalPowerDefenseEntry(delta, entry), createEmptyInnerPowerEntries())
  const upgraded = calculateDefense(addEntries(base.defender, totalDelta, base.attackPanel), base.attackPanel)
  const entryGain = percentGain(upgraded.durability, base.durability) / 100
  return {
    baseGain: 0,
    entryGain,
    totalGain: entryGain,
    entries: entries.map(entry => calculateInternalPowerDefenseBenefit(entry, base.defender, base.attackPanel)),
    note: '基础增伤与攻击词条不计入坦度收益'
  }
}

export function calculateRecommendation(defenderInput, attackPanelInput) {
  const base = calculateDefense(defenderInput, attackPanelInput)
  return [
    recommendationItem('防御词条（+33 防御）', base, { defense: 33 }),
    recommendationItem('会心抵抗词条（+66 会心抵抗）', base, { critResist: 66 })
  ]
}

function calculateSnapshot(defender, attackPanel) {
  const remainingDefense = Math.max(defender.defense - attackPanel.breakDefense, 0)
  const defenseMitigation = remainingDefense / (remainingDefense + 1714)
  const netCrit = attackPanel.crit - defender.critResist
  const critRate = clamp(1 / (1 + Math.exp(1 - netCrit / 686)) + asRate(attackPanel.extraCritRate), 0, 1)
  const techniqueDifference = Math.max(attackPanel.techniqueRestraint - defender.techniqueResist, 0)
  const attackPool = Math.max(
    attackPanel.attack + attackPanel.restraintValue - defender.resist + attackPanel.skillBonus + techniqueDifference,
    0
  )
  const restraintFactor = Math.max(1 + asRate(attackPanel.restraintPct) - asPercentPoints(defender.resistPct), 0)
  const bonusFactor = categoryFactor(attackPanel.internalBonus, defender.internalReduction)
    * categoryFactor(attackPanel.gearBonus, defender.gearReduction)
    * categoryFactor(attackPanel.martialBonus, defender.martialReduction)
    * categoryFactor(attackPanel.otherBonus, defender.otherReduction)
    * (1 + asRate(attackPanel.skillBonusPct))
  const nonCritDamage = 0.5 * attackPool * (1 - defenseMitigation) * restraintFactor * bonusFactor
  const critExtra = Math.max(asRate(attackPanel.critDmg) - asRate(defender.critDefense), 0)
  const expectedDamage = Math.max(nonCritDamage * (1 + critRate * critExtra), 0.0001)
  const durability = defender.hp / expectedDamage
  return {
    remainingDefense,
    defenseMitigation,
    netCrit,
    critRate,
    techniqueDifference,
    nonCritDamage,
    expectedDamage,
    durability
  }
}

function buildDefenseCurve() {
  return Array.from({ length: 1001 }, (_, index) => {
    const remainingDefense = index * 10
    return [remainingDefense, round(remainingDefense / (remainingDefense + 1714), 6)]
  })
}

function buildDefenseDerivativeCurve() {
  return Array.from({ length: 1001 }, (_, index) => {
    const remainingDefense = index * 10
    // 换算为一条防御内功词条（+33 防御）带来的减免增量。
    return [remainingDefense, round(33 * 1714 / ((remainingDefense + 1714) ** 2), 6)]
  })
}

function buildCritCurve() {
  return Array.from({ length: 301 }, (_, index) => {
    const netCrit = -1000 + index * 10
    return [netCrit, round(logisticCritRate(netCrit), 6)]
  })
}

function buildCritDerivativeCurve() {
  return Array.from({ length: 301 }, (_, index) => {
    const netCrit = -1000 + index * 10
    const critRate = logisticCritRate(netCrit)
    // 换算为一条抗会心内功词条（+66 会心抵抗）对应的会心率变化量。
    return [netCrit, round(66 * critRate * (1 - critRate) / 686, 6)]
  })
}

function logisticCritRate(netCrit) {
  return clamp(1 / (1 + Math.exp(1 - netCrit / 686)), 0, 1)
}

function recommendationItem(label, base, changes) {
  const upgraded = calculateDefense(addEntries(base.defender, changes, base.attackPanel), base.attackPanel)
  return {
    label,
    durability: upgraded.durability,
    gainPct: percentGain(upgraded.durability, base.durability)
  }
}

function comparisonItem(name, current, base) {
  return {
    name,
    expectedDamage: current.expectedDamage,
    durability: current.durability,
    gainPct: percentGain(current.durability, base.durability)
  }
}

function addEntries(defender, entries, attackPanel = DEFAULT_ATTACK_PANEL) {
  const normalized = normalizeEntries(entries)
  const result = Object.fromEntries(DEFENDER_FIELDS.map(field => [
    field.key,
    defender[field.key]
  ]))
  result.resistPct += normalized.resistPct
  result.critDefense += normalized.critDefense
  result.techniqueResist += normalized.techniqueResist
  result.hp += normalized.rootBone * 102 + normalized.hp
  result.defense += normalized.endurance * 2.75 + normalized.defense
    + (normalized.internalDefense + normalized.externalDefense) * 0.5
  result.critResist += normalized.agility * 2 + normalized.critResist
    + (normalized.internalCritResist + normalized.externalCritResist) * 0.5
  return result
}

function normalizeInternalPowerDefenseEntry(entry = {}) {
  const name = String(entry.name || entry.entryName || entry.词条 || '').trim()
  const key = INTERNAL_POWER_DEFENSE_ENTRY_MAP[name]
  if (!key) {
    const note = name === '首领抵御'
      ? '首领抵御不参与当前 PVP 坦度公式'
      : '攻击词条不计入坦度收益'
    return { name, supported: false, note, delta: createEmptyInnerPowerEntries() }
  }
  const delta = createEmptyInnerPowerEntries()
  delta[key] = parseEntryNumber(entry.value ?? entry.entryValue ?? entry.数值)
  return { name, supported: true, note: '', delta }
}

function addInternalPowerDefenseEntry(total, entry) {
  const normalized = normalizeInternalPowerDefenseEntry(entry)
  if (!normalized.supported) return total
  Object.entries(normalized.delta).forEach(([key, value]) => {
    total[key] += value
  })
  return total
}

function normalizeDefender(value = {}) {
  const defaults = createDefaultDefender()
  return Object.fromEntries(DEFENDER_FIELDS.map(field => [field.key, number(value[field.key], defaults[field.key])]))
}

function normalizeEntries(value = {}) {
  return Object.fromEntries(INNER_POWER_FIELDS.map(field => [field.key, number(value?.[field.key], 0)]))
}

function normalizeAttackPanel(value = {}) {
  return Object.fromEntries(Object.entries(DEFAULT_ATTACK_PANEL).map(([key, fallback]) => {
    if (key === 'panelName') return [key, String(value[key] || fallback)]
    return [key, number(value[key], fallback)]
  }))
}

function categoryFactor(attackBonus, defenderReduction) {
  return Math.max(1 + asRate(attackBonus) - asPercentPoints(defenderReduction), 0)
}

function asRate(value) {
  const normalized = number(value, 0)
  return Math.abs(normalized) > 1 ? normalized / 100 : normalized
}

function asPercentPoints(value) {
  return number(value, 0) / 100
}

function number(value, fallback = 0) {
  const result = Number(value)
  return Number.isFinite(result) ? result : fallback
}

function parseEntryNumber(value) {
  if (typeof value === 'string') return number(value.replace('%', '').trim(), 0)
  return number(value, 0)
}

function percentGain(value, base) {
  return base > 0 ? (value / base - 1) * 100 : 0
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

function round(value, precision = 6) {
  const factor = 10 ** precision
  return Math.round(value * factor) / factor
}
