export const DEFENDER_FIELDS = [
  { key: 'defense', label: '防御', step: 1 },
  { key: 'resist', label: '抵御', step: 1 },
  { key: 'critResist', label: '会心抵抗', step: 1 },
  { key: 'resistPct', label: '抵御百分比', step: 1, precision: 1, suffix: '%' },
  { key: 'hp', label: '血量', step: 100 },
  { key: 'critDefense', label: '会心防御', step: 0.1, suffix: '%' },
  { key: 'techniqueResist', label: '技巧克制', step: 1 }
]

export const INNER_POWER_FIELDS = [
  { key: 'rootBone', label: '根骨', step: 1 },
  { key: 'agility', label: '身法', step: 1 },
  { key: 'endurance', label: '耐力', step: 1 },
  ...DEFENDER_FIELDS.filter(field => field.key !== 'resist')
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

export function createDefaultDefender() {
  return {
    defense: 2550,
    resist: 0,
    critResist: 0,
    resistPct: 0,
    hp: 100000,
    critDefense: 0,
    techniqueResist: 0
  }
}

export function createEmptyInnerPowerEntries() {
  return Object.fromEntries(INNER_POWER_FIELDS.map(field => [field.key, 0]))
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

export function calculateInnerPowerComparison(defenderInput, attackPanelInput, entriesA, entriesB) {
  const base = calculateDefense(defenderInput, attackPanelInput)
  const buildA = calculateDefense(addEntries(base.defender, entriesA), base.attackPanel)
  const buildB = calculateDefense(addEntries(base.defender, entriesB), base.attackPanel)
  return {
    base,
    buildA: comparisonItem('方案 A', buildA, base),
    buildB: comparisonItem('方案 B', buildB, base)
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
  const bonusFactor = (1 + asRate(attackPanel.internalBonus))
    * (1 + asRate(attackPanel.gearBonus))
    * (1 + asRate(attackPanel.martialBonus))
    * (1 + asRate(attackPanel.otherBonus))
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
  return Array.from({ length: 41 }, (_, index) => {
    const remainingDefense = index * 250
    return [remainingDefense, round(remainingDefense / (remainingDefense + 1714), 6)]
  })
}

function buildDefenseDerivativeCurve() {
  return Array.from({ length: 41 }, (_, index) => {
    const remainingDefense = index * 250
    // 将单点导数换算为每增加 100 点剩余防御的减免增量，便于在 0-1 纵轴中观察。
    return [remainingDefense, round(100 * 1714 / ((remainingDefense + 1714) ** 2), 6)]
  })
}

function buildCritCurve() {
  return Array.from({ length: 41 }, (_, index) => {
    const netCrit = -1000 + index * 75
    return [netCrit, round(logisticCritRate(netCrit), 6)]
  })
}

function buildCritDerivativeCurve() {
  return Array.from({ length: 41 }, (_, index) => {
    const netCrit = -1000 + index * 75
    const critRate = logisticCritRate(netCrit)
    // 将单点导数换算为每增加 100 点净会心的会心率增量，便于在 0-1 纵轴中观察。
    return [netCrit, round(100 * critRate * (1 - critRate) / 686, 6)]
  })
}

function logisticCritRate(netCrit) {
  return clamp(1 / (1 + Math.exp(1 - netCrit / 686)), 0, 1)
}

function recommendationItem(label, base, changes) {
  const upgraded = calculateDefense(addEntries(base.defender, changes), base.attackPanel)
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

function addEntries(defender, entries) {
  const normalized = normalizeEntries(entries)
  const result = Object.fromEntries(DEFENDER_FIELDS.map(field => [
    field.key,
    defender[field.key] + (normalized[field.key] ?? 0)
  ]))
  result.hp += normalized.rootBone * 102
  result.critResist += normalized.agility * 2
  result.defense += normalized.endurance * 2.75
  return result
}

function normalizeDefender(value = {}) {
  const defaults = createDefaultDefender()
  return Object.fromEntries(DEFENDER_FIELDS.map(field => [field.key, number(value[field.key], defaults[field.key])]))
}

function normalizeEntries(value = {}) {
  return Object.fromEntries(INNER_POWER_FIELDS.map(field => [field.key, number(value?.[field.key], 0)]))
}

function normalizeAttackPanel(value = {}) {
  return Object.fromEntries(Object.entries(DEFAULT_ATTACK_PANEL).map(([key, fallback]) => [key, key === 'panelName' ? String(value[key] || fallback) : number(value[key], fallback)]))
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
