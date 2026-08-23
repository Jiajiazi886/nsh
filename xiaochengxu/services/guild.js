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

function addMember(data) {
  return request({
    url: '/guild/member',
    method: 'POST',
    data: {
      player_name: data.playerName,
      player_class: data.playerClass || '',
      secondary_class: data.secondaryClass || '',
      remark: data.remark || '',
    },
  })
}

function updateGuildName(guildName) {
  return request({
    url: '/guild/member/guild-name',
    method: 'PUT',
    data: { guild_name: guildName },
  })
}

function getPendingApplications() {
  return request({ url: '/guild/join/pending' })
}

function reviewApplication(applicationId, approved) {
  return request({
    url: `/guild/join/${approved ? 'approve' : 'reject'}`,
    method: 'POST',
    data: { application_id: Number(applicationId) },
  })
}

function getMyProfile() {
  return request({ url: '/guild/member/my-profile' })
}

function updateMyProfile(data) {
  return request({
    url: '/guild/member/my-profile',
    method: 'PUT',
    data: {
      player_class: data.playerClass || '',
      secondary_class: data.secondaryClass || '',
      remark: data.remark || '',
    },
  })
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
  addMember,
  applyToGuild,
  getDashboardSummary,
  getGuildInfo,
  getMembers,
  getMyProfile,
  getMyStatus,
  getPendingApplications,
  quitGuild,
  reviewApplication,
  searchGuilds,
  updateGuildName,
  updateMyProfile,
}
