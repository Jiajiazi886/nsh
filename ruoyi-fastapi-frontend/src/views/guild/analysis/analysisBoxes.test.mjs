import test from 'node:test'
import assert from 'node:assert/strict'
import { buildBoxAnalysis, normalizePlayerName } from './analysisBoxes.mjs'

const seats = names => Array.from({ length: 6 }, (_, index) => ({
  position: index + 1,
  player: names[index] ? { name: names[index], profession: index ? '铁衣' : '玄机' } : null,
}))

const teams = [{ id: 'team-1', name: '一团', squads: [{ id: 'squad-1', name: '一队', seats: seats(['玩家 甲。', '玩家乙']) }] }]

test('CSV guild is selected by the most normalized lineup-name matches', () => {
  const records = [
    { guild_name: '对手', player_name: '路人', player_class: '素问', kills: '99', qingquan_kills: '0', assists: '0', dmg_to_players: '1' },
    { guild_name: '九肆', player_name: '玩家甲', player_class: '玄机', kills: '2', qingquan_kills: '1', assists: '3', dmg_to_players: '9007199254740993' },
    { guild_name: '九肆', player_name: '玩家 乙', player_class: '铁衣', kills: '4', qingquan_kills: '0', assists: '5', dmg_to_players: '7' },
  ]
  const result = buildBoxAnalysis(teams, records)
  assert.equal(result.selectedGuild, '九肆')
  assert.equal(result.matchedPlayers, 2)
  assert.equal(result.boxes[0].metrics.kills, '6')
  assert.equal(result.boxes[0].metrics.dmg_to_players, '9007199254741000')
  assert.deepEqual(result.boxes[0].squads[0].players.map(player => player.name), ['玩家 甲。', '玩家乙'])
})

test('name matching ignores spaces and trailing punctuation', () => {
  assert.equal(normalizePlayerName(' 玩家 甲．． '), normalizePlayerName('玩家甲'))
})
