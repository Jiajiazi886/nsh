import assert from 'node:assert/strict'

import {
  DEFENSE_CALCULATOR_EXAMPLE,
  calculatePersonalDefense,
  isSpiritEntryField,
  normalizeDefenseInput
} from './personalDefenseCalculator.js'

function nearlyEqual(actual, expected, message) {
  assert.equal(Number(actual).toFixed(4), Number(expected).toFixed(4), message)
}

const result = calculatePersonalDefense(DEFENSE_CALCULATOR_EXAMPLE)

nearlyEqual(result.summary['词条分'], 31.0287, 'example entry score')
nearlyEqual(result.summary['特性分'], 36.95, 'example trait score')
nearlyEqual(result.summary['总分'], 67.9787, 'example total score')
nearlyEqual(result.summary['周天加成'], 2.7, 'example zhou tian bonus')

const attackEntry = result['词条明细'].find(item => item['名称'] === '攻击')
assert.deepEqual(attackEntry, { '名称': '攻击', '输入': 120, '评分': 5.46, '满词条输入': 33, '满词条评分': 1.5015 })

const qiHaiEntry = result['词条明细'].find(item => item['名称'] === '力量/气海')
assert.equal(qiHaiEntry['满词条输入'], 10)
nearlyEqual(qiHaiEntry['满词条评分'], 1.5625, 'full strength/qihai score')

const restraintEntry = result['词条明细'].find(item => item['名称'] === '流派克制')
assert.equal(restraintEntry['满词条输入'], 1.2)
nearlyEqual(restraintEntry['满词条评分'], 1.2, 'full restraint score')

assert.equal(isSpiritEntryField('灼星贯日-灵'), true)
assert.equal(isSpiritEntryField('力量/气海'), false)

const zhuoxingTrait = result['特性明细'].find(item => item['名称'] === '灼星贯日')
assert.deepEqual(zhuoxingTrait, { '名称': '灼星贯日', '携带': true, '收益': 7.1, '计数': 1 })

const normalized = normalizeDefenseInput({
  '周天': '不存在',
  '词条': { '攻击': 'abc', '破防': '12.5' },
  '特性': { '灼星贯日': '是', '承影锋镝': '否' }
})

assert.equal(normalized['周天'], '火木')
assert.equal(normalized['词条']['攻击'], 0)
assert.equal(normalized['词条']['破防'], 12.5)
assert.equal(normalized['特性']['灼星贯日'], true)
assert.equal(normalized['特性']['承影锋镝'], false)

const defaults = calculatePersonalDefense()
nearlyEqual(defaults.summary['词条分'], 0, 'default entry score')
nearlyEqual(defaults.summary['特性分'], 36.1, 'default trait score')
nearlyEqual(defaults.summary['总分'], 36.1, 'default total score')
