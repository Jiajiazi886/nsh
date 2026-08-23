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

module.exports = {
  getInvite,
  submitJoin,
}
