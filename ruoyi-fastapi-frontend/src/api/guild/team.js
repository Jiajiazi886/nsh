import request from '@/utils/request'

export function getTeams() {
  return request({
    url: '/guild/team/list',
    method: 'get'
  })
}

export function addTeam(data) {
  return request({
    url: '/guild/team/create',
    method: 'post',
    data
  })
}

export function deleteTeam(teamId) {
  return request({
    url: `/guild/team/${teamId}`,
    method: 'delete'
  })
}