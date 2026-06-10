import request from '@/utils/request'

export function getMemberList() {
  return request({
    url: '/guild/member/list',
    method: 'get'
  })
}

export function getGuildInfo() {
  return request({
    url: '/guild/member/guild-info',
    method: 'get'
  })
}

export function updateGuildName(guildName) {
  return request({
    url: '/guild/member/guild-name',
    method: 'put',
    data: { guild_name: guildName }
  })
}

export function getMyMemberProfile() {
  return request({
    url: '/guild/member/my-profile',
    method: 'get'
  })
}

export function updateMyMemberProfile(data) {
  return request({
    url: '/guild/member/my-profile',
    method: 'put',
    data
  })
}

export function addMember(data) {
  return request({
    url: '/guild/member',
    method: 'post',
    data
  })
}

export function editMember(data) {
  return request({
    url: `/guild/member/${data.member_id}`,
    method: 'put',
    data
  })
}

export function batchDeleteMembers(memberIds) {
  return request({
    url: '/guild/member/batch-delete',
    method: 'post',
    data: { member_ids: memberIds }
  })
}

export function importFromBattle(data) {
  return request({
    url: '/guild/member/import-from-battle',
    method: 'post',
    data
  })
}

export function getBattleListForImport() {
  return request({
    url: '/guild/member/battle-list',
    method: 'get'
  })
}

export function getBattleGuilds(battleId) {
  return request({
    url: `/guild/member/battle-guilds/${battleId}`,
    method: 'get'
  })
}

export function updateMemberTeam(memberId, data) {
  return request({
    url: `/guild/member/${memberId}`,
    method: 'put',
    data
  })
}
