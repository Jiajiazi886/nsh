import assert from 'node:assert/strict'

import {
  ATTACK_PANEL_JSON_EXAMPLE,
  attackPanelToJsonObject,
  formatAttackPanelJson,
  parseAttackPanelJson
} from './pvpAttackPanelJson.js'

const parsed = parseAttackPanelJson(JSON.stringify(ATTACK_PANEL_JSON_EXAMPLE))
assert.equal(parsed.panelName, '联赛标准面板')
assert.equal(parsed.status, '0')
assert.equal(parsed.attack, 1750)
assert.equal(parsed.crit, 2100)
assert.equal(parsed.critDmg, 0.575)

const personal = parseAttackPanelJson(JSON.stringify({
  ...ATTACK_PANEL_JSON_EXAMPLE,
  面板名称: '',
  状态: '不是有效状态'
}), { requireMetadata: false })
assert.equal(personal.attack, 1750)
assert.equal(personal.panelName, undefined)

const roundTripSource = { ...parsed, panelName: '测试面板', status: '1', remark: '备注', internalBonus: 1.25 }
assert.deepEqual(parseAttackPanelJson(formatAttackPanelJson(roundTripSource)), roundTripSource)
assert.equal(attackPanelToJsonObject(roundTripSource)['内功增伤'], 1.25)

assert.throws(() => parseAttackPanelJson('[]'), /单个面板对象/)
assert.throws(() => parseAttackPanelJson('{'), /JSON 格式不正确/)
assert.throws(() => parseAttackPanelJson(JSON.stringify({ ...ATTACK_PANEL_JSON_EXAMPLE, 攻击: -1 })), /攻击/)
const missing = { ...ATTACK_PANEL_JSON_EXAMPLE }
delete missing['破防']
assert.throws(() => parseAttackPanelJson(JSON.stringify(missing)), /缺少必填字段“破防”/)
