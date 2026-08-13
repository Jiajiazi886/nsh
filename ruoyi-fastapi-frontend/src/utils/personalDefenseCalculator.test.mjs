import assert from 'node:assert/strict'

import {
  DEFAULT_ATTACK_PANEL,
  INNER_POWER_FIELDS,
  calculateDefense,
  calculateInternalPowerDefenseBenefit,
  calculateInternalPowerDefenseBenefits,
  calculateInternalPowerUpgrade,
  calculateInnerPowerComparisons,
  calculateRecommendation,
  areDefenderPanelsEqual,
  createDefaultDefender,
  createEmptyInnerPowerEntries,
  resolveAfterDefender
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
assert.equal(recommendations.length, 11)
assert.equal(recommendations.find(item => item.key === 'defense').inputValue, 33)
assert.equal(recommendations.find(item => item.key === 'critResist').inputValue, 66)
assert.ok(recommendations.find(item => item.key === 'defense').gainPct > 0)
assert.ok(recommendations.find(item => item.key === 'critResist').gainPct > 0)
assert.equal(recommendations.find(item => item.key === 'endurance').inputValue, 0)

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

const ironcladBonus = { defenseBonusPct: 20, hpBonusPct: 40 }
const ironcladDefense = calculateInternalPowerUpgrade(
  createDefaultDefender(),
  DEFAULT_ATTACK_PANEL,
  [{ id: 1, name: '测试内功', entries: [
    { name: '防御', value: 10 },
    { name: '耐力', value: 10 },
    { name: '内功防御', value: 10 },
    { name: '外功防御', value: 10 },
    { name: '根骨', value: 10 },
    { name: '气血上限', value: 1000 },
    { name: '身法', value: 10 },
    { name: '抗会心', value: 20 },
    { name: '抗内功会心', value: 10 },
    { name: '抗外功会心', value: 10 },
    { name: '流派抵御', value: '1.2%' },
    { name: '攻击', value: 999 }
  ] }],
  ironcladBonus
)
assert.equal(ironcladDefense.total.rawDefense, 47.5)
assert.equal(ironcladDefense.total.defense, 57)
assert.equal(ironcladDefense.total.rawHp, 2020)
assert.equal(ironcladDefense.total.hp, 2828)
assert.equal(ironcladDefense.total.critResist, 50)
assert.equal(ironcladDefense.total.resistPct, 1.2)
assert.equal(ironcladDefense.afterDefender.defense, createDefaultDefender().defense + 57)
assert.equal(ironcladDefense.afterDefender.hp, createDefaultDefender().hp + 2828)
assert.ok(ironcladDefense.gainPct > 0)
assert.equal(ironcladDefense.powers.length, 1)
assert.equal(ironcladDefense.powers[0].ignoredEntries[0].name, '攻击')

const manualAfter = { ...ironcladDefense.afterDefender, defense: 3200, internalReduction: 1.25 }
assert.equal(resolveAfterDefender(ironcladDefense.afterDefender, manualAfter, ironcladDefense.afterDefender).defense, 3200)
assert.equal(resolveAfterDefender(ironcladDefense.afterDefender, manualAfter, ironcladDefense.afterDefender).internalReduction, 1.25)
assert.equal(resolveAfterDefender({ ...ironcladDefense.afterDefender, defense: 3100 }, manualAfter, ironcladDefense.afterDefender).defense, 3100)
assert.equal(areDefenderPanelsEqual(ironcladDefense.afterDefender, { ...ironcladDefense.afterDefender }), true)

const manualRecommendations = calculateRecommendation(
  createDefaultDefender(),
  DEFAULT_ATTACK_PANEL,
  {
    defense: 10,
    endurance: 10,
    internalDefense: 10,
    hp: 1000
  },
  ironcladBonus
)
assert.equal(manualRecommendations.find(item => item.key === 'defense').actualValue, 12)
assert.equal(manualRecommendations.find(item => item.key === 'endurance').actualValue, 33)
assert.equal(manualRecommendations.find(item => item.key === 'internalDefense').actualValue, 6)
assert.equal(manualRecommendations.find(item => item.key === 'hp').actualValue, 1400)
assert.ok(manualRecommendations.every(item => item.gainPct >= 0))
