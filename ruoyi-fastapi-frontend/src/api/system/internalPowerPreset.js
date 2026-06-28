import request from '@/utils/request'

export function listInternalPowerPreset(query) {
  return request({
    url: '/system/internal-power-preset/list',
    method: 'get',
    params: query
  })
}

export function getInternalPowerPreset(presetId) {
  return request({
    url: `/system/internal-power-preset/${presetId}`,
    method: 'get'
  })
}

export function addInternalPowerPreset(data) {
  return request({
    url: '/system/internal-power-preset',
    method: 'post',
    data
  })
}

export function updateInternalPowerPreset(data) {
  return request({
    url: '/system/internal-power-preset',
    method: 'put',
    data
  })
}

export function delInternalPowerPreset(presetIds) {
  return request({
    url: `/system/internal-power-preset/${presetIds}`,
    method: 'delete'
  })
}
