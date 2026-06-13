import request from '@/utils/request'

export function importBattle(data) {
  return request({
    url: '/guild/battle/import',
    method: 'post',
    data: data
  })
}

export function getBattleList(params) {
  return request({
    url: '/guild/battle/list',
    method: 'get',
    params
  })
}

export function getBattleRecords(battleId) {
  return request({
    url: `/guild/battle/records/${battleId}`,
    method: 'get'
  })
}

export function deleteBattle(battleId) {
  return request({
    url: `/guild/battle/${battleId}`,
    method: 'delete'
  })
}

export function checkFilename(filename) {
  return request({
    url: '/guild/battle/check-filename',
    method: 'get',
    params: { filename }
  })
}

export function createBattleInvite(data) {
  return request({
    url: '/guild/battle-registration/invite',
    method: 'post',
    data
  })
}

export function getBattleInvites() {
  return request({
    url: '/guild/battle-registration/invite/list',
    method: 'get'
  })
}

export function disableBattleInvite(inviteId) {
  return request({
    url: `/guild/battle-registration/invite/${inviteId}/disable`,
    method: 'post'
  })
}

export function deleteBattleInvite(inviteId) {
  return request({
    url: `/guild/battle-registration/invite/${inviteId}`,
    method: 'delete'
  })
}

export function getBattleRegistrations(params) {
  return request({
    url: '/guild/battle-registration/list',
    method: 'get',
    params
  })
}

export function getApprovedBattleRegistrationsForSchedule() {
  return request({
    url: '/guild/battle-registration/approved-schedule-list',
    method: 'get'
  })
}

export function getBattleLeaveRegistrationsForSchedule() {
  return request({
    url: '/guild/battle-registration/leave-schedule-list',
    method: 'get'
  })
}

export function approveBattleRegistration(registrationId, approvalComment = '') {
  return request({
    url: '/guild/battle-registration/approve',
    method: 'post',
    data: { registration_id: registrationId, approval_comment: approvalComment }
  })
}

export function rejectBattleRegistration(registrationId, approvalComment = '') {
  return request({
    url: '/guild/battle-registration/reject',
    method: 'post',
    data: { registration_id: registrationId, approval_comment: approvalComment }
  })
}

export function getPublicBattleInvite(inviteCode) {
  return request({
    url: `/public/battle/${inviteCode}`,
    method: 'get',
    headers: { isToken: false }
  })
}

export function searchPublicBattleMembers(inviteCode, keyword) {
  return request({
    url: `/public/battle/${inviteCode}/members`,
    method: 'get',
    params: { keyword },
    headers: { isToken: false }
  })
}

export function getPublicBattleProfessions(inviteCode) {
  return request({
    url: `/public/battle/${inviteCode}/professions`,
    method: 'get',
    headers: { isToken: false }
  })
}

export function submitPublicBattleSignup(inviteCode, data) {
  return request({
    url: `/public/battle/${inviteCode}/signup`,
    method: 'post',
    data,
    headers: { isToken: false }
  })
}

export function submitPublicBattleJoin(inviteCode, data) {
  return request({
    url: `/public/battle/${inviteCode}/join`,
    method: 'post',
    data,
    headers: { isToken: false }
  })
}

export function submitPublicBattleLeave(inviteCode, data) {
  return request({
    url: `/public/battle/${inviteCode}/leave`,
    method: 'post',
    data,
    headers: { isToken: false }
  })
}
