import request from '@/utils/request'

export function searchGuilds(keyword) {
  return request({
    url: '/guild/join/search',
    method: 'get',
    params: { keyword }
  })
}

export function submitJoinApplication(data) {
  return request({
    url: '/guild/join/apply',
    method: 'post',
    data
  })
}

export function getMyJoinStatus() {
  return request({
    url: '/guild/join/my-status',
    method: 'get'
  })
}

export function quitGuild() {
  return request({
    url: '/guild/join/quit',
    method: 'post'
  })
}

export function getPendingJoinApplications() {
  return request({
    url: '/guild/join/pending',
    method: 'get'
  })
}

export function approveJoinApplication(applicationId) {
  return request({
    url: '/guild/join/approve',
    method: 'post',
    data: { application_id: applicationId }
  })
}

export function rejectJoinApplication(applicationId) {
  return request({
    url: '/guild/join/reject',
    method: 'post',
    data: { application_id: applicationId }
  })
}
