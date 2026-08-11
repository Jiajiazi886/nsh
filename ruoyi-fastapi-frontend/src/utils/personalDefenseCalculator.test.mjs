import assert from 'node:assert/strict'

import {
  DEFAULT_ATTACK_PANEL,
  INNER_POWER_FIELDS,
  calculateDefense,
  calculateInternalPowerDefenseBenefit,
  calculateInternalPowerDefenseBenefits,
  calculateInnerPowerComparisons,
  calculateRecommendation,
  createDefaultDefender,
  createEmptyInnerPowerEntries
} from './personalDefenseCalculator.js'

const base = calculateDefense(createDefaultDefender(), DEFAULT_ATTACK_PANEL)

assert.equal(base.remainingDefense, 1450)
assert.equal(Number(base.defenseMitigation.toFixed(6)), 0.458281)
assert.equal(Number(base.critRate.toFixed(6)), 0.646456)
assert.ok(base.expectedDamage > 0)
assert.ok(base.durability > 0)
const withResistPct = calculateDefense({ ...createDefaultDefender(), resistPct: 1.2 }, DEFAULT_ATTACK_PANEL)
assert.ok(withResistPct.expectedDamage < base.expectedDamage)
assert.ok(withResistPct.durability > base.durability)
assert.equal(base.defenseCurve.at(-1)[0], 10000)
assert.equal(base.defenseCurve[0][1], 0)
assert.equal(base.defenseCurve[1][0], 10)
assert.equal(Number(base.defenseCurve.find(([x]) => x === 1000)[1].toFixed(6)), 0.36846)
assert.equal(Number(base.defenseDerivativeCurve[0][1].toFixed(6)), 0.019253)
assert.ok(base.defenseDerivativeCurve[0][1] > base.defenseDerivativeCurve.at(-1)[1])
assert.equal(base.critCurve.at(-1)[0], 2000)
assert.equal(base.critCurve[1][0] - base.critCurve[0][0], 10)
assert.equal(base.critDerivativeCurve[0][0], -1000)
assert.ok(base.critDerivativeCurve.some(([, value]) => value > 0))

const recommendations = calculateRecommendation(createDefaultDefender(), DEFAULT_ATTACK_PANEL)
assert.equal(recommendations.length, 2)
assert.equal(recommendations[0].label, '防御词条（+33 防御）')
assert.equal(recommendations[1].label, '会心抵抗词条（+66 会心抵抗）')
assert.ok(recommendations[0].gainPct > 0)
assert.ok(recommendations[1].gainPct > 0)

const entriesA = createEmptyInnerPowerEntries()
entriesA.defense = 100
entriesA.rootBone = 1
entriesA.agility = 1
entriesA.endurance = 1
entriesA.internalDefense = 80
entriesA.externalDefense = 20
entriesA.internalCritResist = 90
entriesA.externalCritResist = 30
assert.equal(entriesA.resist, undefined)
assert.ok(INNER_POWER_FIELDS.every(field => field.key !== 'resist'))
const comparison = calculateInnerPowerComparisons(createDefaultDefender(), DEFAULT_ATTACK_PANEL, [
  { id: 'internal', name: '内功方案', entries: entriesA },
  { id: 'empty', name: '空方案', entries: {} }
])
assert.ok(comparison.plans[0].gainPct > 0)
assert.equal(comparison.plans[1].gainPct, 0)

const internalOnly = createEmptyInnerPowerEntries()
internalOnly.internalDefense = 100
internalOnly.internalCritResist = 100
const externalOnly = createEmptyInnerPowerEntries()
externalOnly.externalDefense = 100
externalOnly.externalCritResist = 100
const byNoAttackType = calculateInnerPowerComparisons(createDefaultDefender(), DEFAULT_ATTACK_PANEL, [
  { id: 'internal-only', name: '内功防御', entries: internalOnly },
  { id: 'external-only', name: '外功防御', entries: externalOnly }
])
assert.equal(byNoAttackType.plans[0].gainPct, byNoAttackType.plans[1].gainPct)
const genericHalf = createEmptyInnerPowerEntries()
genericHalf.defense = 50
genericHalf.critResist = 50
const halfSpecialComparison = calculateInnerPowerComparisons(createDefaultDefender(), DEFAULT_ATTACK_PANEL, [
  { id: 'special', name: '专属词条', entries: internalOnly },
  { id: 'generic', name: '通用词条', entries: genericHalf }
])
assert.equal(halfSpecialComparison.plans[0].gainPct, halfSpecialComparison.plans[1].gainPct)

const bonusAttackPanel = { ...DEFAULT_ATTACK_PANEL, internalBonus: 10, gearBonus: 5, martialBonus: 3, otherBonus: 2 }
const withMatchingReductions = calculateDefense({
  ...createDefaultDefender(),
  internalReduction: 10,
  gearReduction: 5,
  martialReduction: 3,
  otherReduction: 2
}, bonusAttackPanel)
assert.equal(Number(withMatchingReductions.expectedDamage.toFixed(6)), Number(base.expectedDamage.toFixed(6)))
const withOverReduction = calculateDefense({ ...createDefaultDefender(), internalReduction: 200 }, bonusAttackPanel)
assert.ok(withOverReduction.expectedDamage >= 0)

const attackEntryBenefit = calculateInternalPowerDefenseBenefit(
  { name: '攻击', value: 33 },
  createDefaultDefender(),
  DEFAULT_ATTACK_PANEL
)
assert.equal(attackEntryBenefit.gain, 0)
assert.match(attackEntryBenefit.note, /不计入坦度收益/)
const defenseEntryBenefit = calculateInternalPowerDefenseBenefit(
  { name: '防御', value: 33 },
  createDefaultDefender(),
  DEFAULT_ATTACK_PANEL
)
assert.ok(defenseEntryBenefit.gain > 0)
const powerDefenseBenefit = calculateInternalPowerDefenseBenefits({
  bonusPercent: 15,
  entries: [{ name: '攻击', value: 33 }, { name: '根骨', value: 10 }, { name: '抗会心', value: 66 }]
}, createDefaultDefender(), DEFAULT_ATTACK_PANEL)
assert.equal(powerDefenseBenefit.baseGain, 0)
assert.ok(powerDefenseBenefit.entryGain > 0)
