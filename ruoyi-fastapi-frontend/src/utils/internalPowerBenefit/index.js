import {
  ATTACK_FIELDS,
  DEFAULT_ATTACK,
  DEFAULT_TARGET,
  EMPTY_DELTA,
  ENTRY_DEFS,
  FORMULA_SCOPE_INTERNAL_POWER_PVP,
  TARGET_FIELDS,
  computeDamage,
  convertEntries,
  createDefaultFormulaPackage,
  getActiveFormulaPackage,
  getEntryDefinitions,
  normalizeFormulaPackage,
  mergeDeltas,
  parseInputNumber,
  setActiveFormulaPackage
} from './calculator-core'

export {
  ATTACK_FIELDS,
  DEFAULT_ATTACK,
  DEFAULT_TARGET,
  EMPTY_DELTA,
  ENTRY_DEFS,
  FORMULA_SCOPE_INTERNAL_POWER_PVP,
  TARGET_FIELDS,
  convertEntries,
  createDefaultFormulaPackage,
  getActiveFormulaPackage,
  getEntryDefinitions,
  normalizeFormulaPackage,
  setActiveFormulaPackage,
  parseInputNumber
}

const percentFieldKeys = new Set(
  [...TARGET_FIELDS, ...ATTACK_FIELDS]
    .filter(field => field.type === 'percent')
    .map(field => field.key)
)

const ignoredEntryNames = new Set(['灵韵'])

export function createDefaultPanelSetting() {
  const pkg = getActiveFormulaPackage()
  return {
    targetPanel: { ...pkg.defaults.targetPanel },
    attackPanel: { ...pkg.defaults.attackPanel }
  }
}

export function normalizePanelSetting(value = {}) {
  const pkg = getActiveFormulaPackage()
  return {
    targetPanel: normalizePanel(value.targetPanel || value.target_panel || {}, pkg.defaults.targetPanel),
    attackPanel: normalizePanel(value.attackPanel || value.attack_panel || {}, pkg.defaults.attackPanel)
  }
}

export function toPanelDisplayValue(key, value) {
  const n = safeNumber(value)
  return percentFieldKeys.has(key) ? roundTo(n * 100, 5) : n
}

export function fromPanelDisplayValue(key, value) {
  const n = safeNumber(value)
  return percentFieldKeys.has(key) ? n / 100 : n
}

export function calculatePowerBenefit(power = {}, panelSetting = createDefaultPanelSetting()) {
  const panels = normalizePanelSetting(panelSetting)
  const baseDelta = createBaseDelta(power)
  const benefitEntries = normalizeBenefitEntries(power.entries)
  const convertedEntries = convertEntries(benefitEntries)
  const entryDelta = convertedEntries.delta
  const totalDelta = mergeDeltas(baseDelta, entryDelta)
  const baseDamage = computeDamage(panels.targetPanel, panels.attackPanel, EMPTY_DELTA)

  return {
    baseGain: gainForDelta(panels, baseDamage, baseDelta),
    entryGain: gainForDelta(panels, baseDamage, entryDelta),
    totalGain: gainForDelta(panels, baseDamage, totalDelta),
    entryDelta,
    baseDelta,
    totalDelta,
    entries: benefitEntries.map(entry => calculateEntryBenefitWithBase(entry, panels, baseDamage))
  }
}

export function calculateEntryBenefit(entry = {}, panelSetting = createDefaultPanelSetting()) {
  const panels = normalizePanelSetting(panelSetting)
  const baseDamage = computeDamage(panels.targetPanel, panels.attackPanel, EMPTY_DELTA)
  return calculateEntryBenefitWithBase(entry, panels, baseDamage)
}

function calculateEntryBenefitWithBase(entry = {}, panels, baseDamage) {
  const converted = convertEntries([entry])
  const gain = gainForDelta(panels, baseDamage, converted.delta)
  const detail = converted.details[0] || {}
  return {
    id: entry.id,
    name: entry.name || entry.entryName || entry.词条 || '',
    value: entry.value,
    gain,
    note: detail.note || (Math.abs(gain) < 1e-12 ? '不计入当前攻击收益' : '')
  }
}

export function formatBenefitPercent(value, digits = 5) {
  const n = safeNumber(value)
  const sign = n >= 0 ? '+' : ''
  return `${sign}${(n * 100).toFixed(digits)}%`
}

export function getEntryDefinition(name) {
  return getEntryDefinitions().find(item => item.name === name)
}

function normalizePanel(value, defaults) {
  const panel = { ...defaults }
  Object.keys(defaults).forEach(key => {
    panel[key] = safeNumber(value[key], defaults[key])
  })
  return panel
}

function normalizeBenefitEntries(entries = []) {
  return (entries || [])
    .map(entry => ({
      ...entry,
      name: entry.name || entry.entryName || entry.词条 || '',
      value: entry.value ?? entry.entryValue ?? entry.数值 ?? 0
    }))
    .filter(entry => entry.name && !ignoredEntryNames.has(entry.name))
}

function createBaseDelta(power = {}) {
  return {
    ...getActiveFormulaPackage().defaults.emptyDelta,
    internalBonus: safeNumber(power.bonusPercent) / 100
  }
}

function gainForDelta(panels, baseDamage, delta) {
  const changed = computeDamage(panels.targetPanel, panels.attackPanel, delta)
  if (!baseDamage.damage) return 0
  return changed.damage / baseDamage.damage - 1
}

function safeNumber(value, fallback = 0) {
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}

function roundTo(value, precision = 5) {
  const factor = 10 ** precision
  return Math.round(Number(value || 0) * factor) / factor
}
