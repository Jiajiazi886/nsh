const { request } = require('../utils/request')

function getMyStatus() {
  return request({ url: '/guild/join/my-status' })
}

function getDashboardSummary() {
  return request({ url: '/guild/dashboard/summary' })
}

function getGuildInfo() {
  return request({ url: '/guild/member/guild-info' })
}

function getMembers() {
  return request({ url: '/guild/member/list' })
}

function searchGuilds(keyword) {
  return request({
    url: `/guild/join/search?keyword=${encodeURIComponent(keyword)}`,
  })
}

function applyToGuild(data) {
  return request({
    url: '/guild/join/apply',
    method: 'POST',
    data: {
      guild_id: data.guildId,
      player_name: data.playerName,
      player_class: data.playerClass || '',
      secondary_class: data.secondaryClass || '',
      remark: data.remark || '',
    },
  })
}

function quitGuild() {
  return request({ url: '/guild/join/quit', method: 'POST' })
}

module.exports = {
  applyToGuild,
  getDashboardSummary,
  getGuildInfo,
  getMembers,
  getMyStatus,
  quitGuild,
  searchGuilds,
}
