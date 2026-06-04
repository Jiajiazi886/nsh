import request from '@/utils/request'

export function listProfession(query) {
  return request({
    url: '/guild/profession/list',
    method: 'get',
    params: query
  })
}

export function getProfession(professionId) {
  return request({
    url: '/guild/profession/' + professionId,
    method: 'get'
  })
}

export function getProfessionOptions() {
  return request({
    url: '/guild/profession/options',
    method: 'get'
  })
}

export function addProfession(data) {
  return request({
    url: '/guild/profession',
    method: 'post',
    data
  })
}

export function updateProfession(data) {
  return request({
    url: '/guild/profession',
    method: 'put',
    data
  })
}

export function delProfession(professionId) {
  return request({
    url: '/guild/profession/' + professionId,
    method: 'delete'
  })
}
