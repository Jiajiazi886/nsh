const { request } = require('../utils/request')

function getInvite(inviteCode) {
  return request({
    url: `/public/battle/${encodeURIComponent(inviteCode)}`,
    auth: false,
  })
}

function submitJoin(inviteCode, data) {
  return request({
    url: `/guild/battle-registration/invite/${encodeURIComponent(inviteCode)}/join`,
    method: 'POST',
    data: {
      player_name: data.playerName,
      player_class: data.playerClass || '',
      secondary_class: data.secondaryClass || '',
      applicant_name: data.applicantName || '',
      applicant_contact: data.applicantContact || '',
      remark: data.remark || '',
    },
  })
}

function listInvites() {
  return request({ url: '/guild/battle-registration/invite/list' })
}

function createInvite(data) {
  return request({
    url: '/guild/battle-registration/invite',
    method: 'POST',
    data: {
      battle_name: data.battleName,
      battle_time: data.battleTime || null,
      expire_hours: Number(data.expireHours || 24),
      remark: data.remark || '',
    },
  })
}

function disableInvite(inviteId) {
  return request({
    url: `/guild/battle-registration/invite/${inviteId}/disable`,
    method: 'POST',
  })
}

function listRegistrations(registrationType, status) {
  const query = [`registration_type=${encodeURIComponent(registrationType || 'signup')}`]
  if (status !== undefined && status !== null && status !== '') {
    query.push(`status=${encodeURIComponent(status)}`)
  }
  return request({ url: `/guild/battle-registration/list?${query.join('&')}` })
}

function reviewRegistration(registrationId, approved) {
  return request({
    url: `/guild/battle-registration/${approved ? 'approve' : 'reject'}`,
    method: 'POST',
    data: {
      registration_id: Number(registrationId),
      approval_comment: '',
    },
  })
}

function listHistory(page, size) {
  return request({ url: `/guild/battle/list?page=${page || 1}&size=${size || 20}` })
}

function getBattleRecords(battleId) {
  return request({ url: `/guild/battle/records/${battleId}` })
}

module.exports = {
  createInvite,
  disableInvite,
  getBattleRecords,
  getInvite,
  listHistory,
  listInvites,
  listRegistrations,
  reviewRegistration,
  submitJoin,
}
