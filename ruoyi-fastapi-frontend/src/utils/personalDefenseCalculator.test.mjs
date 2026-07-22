import assert from 'node:assert/strict'

import {
  DEFAULT_ATTACK_PANEL,
  INNER_POWER_FIELDS,
  calculateDefense,
  calculateInnerPowerComparison,
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
assert.equal(Number(base.defenseCurve[4][1].toFixed(6)), 0.36846)
assert.equal(Number(base.defenseDerivativeCurve[0][1].toFixed(6)), 0.058343)
assert.ok(base.defenseDerivativeCurve[0][1] > base.defenseDerivativeCurve.at(-1)[1])
assert.equal(base.critCurve.at(-1)[0], 2000)
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
assert.equal(entriesA.resist, undefined)
assert.ok(INNER_POWER_FIELDS.every(field => field.key !== 'resist'))
const comparison = calculateInnerPowerComparison(createDefaultDefender(), DEFAULT_ATTACK_PANEL, entriesA, {})
assert.ok(comparison.buildA.gainPct > 0)
assert.equal(comparison.buildB.gainPct, 0)
