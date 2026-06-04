import request from '@/utils/request'

export function getClassColors() {
  return request({
    url: '/guild/class-color/list',
    method: 'get'
  })
}

export function saveClassColors(data) {
  return request({
    url: '/guild/class-color/save',
    method: 'post',
    data
  })
}