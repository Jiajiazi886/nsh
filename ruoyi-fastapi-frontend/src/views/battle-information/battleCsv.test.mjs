import test from 'node:test'
import assert from 'node:assert/strict'
import { parseBattleCsv, inferBattleFileInfo } from './battleCsv.mjs'

const HEADER = '玩家名字,职业,击败/清泉,助攻,资源,对玩家伤害,人伤卸甲,对建筑伤害,破塔卸甲,治疗值,承受伤害,重伤,复活/清泉,焚骨'

test('fixed battle CSV parses quoted names and multiple guild sections', () => {
  const csv = [
    '九肆,2', HEADER,
    '"玩家,甲",铁衣,7/2,19,100,9007199254740993,8,9,10,11,12,3,4,5',
    '玩家乙,素问,0/0,20,0,1,2,3,4,500,6,1,2,0',
    '扶摇,1', HEADER,
    '玩家丙,龙吟,3/1,8,9,10,11,12,13,14,15,2,1,0',
  ].join('\r\n')

  const result = parseBattleCsv(csv)
  assert.deepEqual(result.guilds, [
    { name: '九肆', declaredCount: 2, actualCount: 2 },
    { name: '扶摇', declaredCount: 1, actualCount: 1 },
  ])
  assert.equal(result.records.length, 3)
  assert.equal(result.records[0].player_name, '玩家,甲')
  assert.equal(result.records[0].kills, '7')
  assert.equal(result.records[0].qingquan_kills, '2')
  assert.equal(result.records[0].revives, '4')
  assert.equal('qingquan_revives' in result.records[0], false)
  assert.equal(result.records[0].dmg_to_players, '9007199254740993')
})

test('CSV parser rejects missing columns, invalid numbers and duplicate players', () => {
  assert.throws(() => parseBattleCsv('九肆,1\n玩家名字,职业\n玩家甲,铁衣'), /缺少固定字段/)
  assert.throws(() => parseBattleCsv(['九肆,1', HEADER, '玩家甲,铁衣,1\/0,坏数据,0,0,0,0,0,0,0,0,0,0'].join('\n')), /非法数值/)
  assert.throws(() => parseBattleCsv(['九肆,1', HEADER, '玩家甲,铁衣,1\/0,0,0,0,0,0,0,0,0,0,0\/0,0'].join('\n')), /复活\/清泉.*非法数值/)
  assert.throws(() => parseBattleCsv(['九肆,2', HEADER, '玩家甲,铁衣,1\/0,0,0,0,0,0,0,0,0,0,0,0', '玩家甲,铁衣,1\/0,0,0,0,0,0,0,0,0,0,0,0'].join('\n')), /重复玩家/)
})

test('filename information is only a convenience and keeps activity date fallback', () => {
  assert.deepEqual(inferBattleFileInfo('20260915_九肆_扶摇.csv', '2026-09-15'), {
    battleDate: '2026-09-15', myGuildName: '九肆', opponentName: '扶摇'
  })
  assert.equal(inferBattleFileInfo('比赛数据.csv', '2026-09-15').battleDate, '2026-09-15')
})
