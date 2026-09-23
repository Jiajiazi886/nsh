import request from '@/utils/request'

export function getInternalPowerAiKeyStatus() {
  return request({
    url: '/system/ai-key/internal-power',
    method: 'get'
  })
}

export function updateInternalPowerAiKey(data) {
  return request({
    url: '/system/ai-key/internal-power',
    method: 'put',
    data
  })
}

export function listAiConnections() {
  return request({
    url: '/system/ai-key/connections',
    method: 'get'
  })
}

export function createAiConnection(data) {
  return request({
    url: '/system/ai-key/connections',
    method: 'post',
    data
  })
}

export function updateAiConnection(id, data) {
  return request({
    url: `/system/ai-key/connections/${id}`,
    method: 'put',
    data
  })
}

export function deleteAiConnection(id) {
  return request({
    url: `/system/ai-key/connections/${id}`,
    method: 'delete'
  })
}

export function activateAiConnection(id) {
  return request({
    url: `/system/ai-key/connections/${id}/activate`,
    method: 'put'
  })
}

export function discoverAiModels(data) {
  return request({
    url: '/system/ai-key/connections/discover-models',
    method: 'post',
    data
  })
}

export function testAiConnection(data) {
  return request({
    url: '/system/ai-key/connections/test-chat',
    method: 'post',
    data
  })
}

export function listAiUsageRecords(params) {
  return request({ url: '/system/ai-key/usage-records', method: 'get', params })
}

export function getAiUsageSummary(params) {
  return request({ url: '/system/ai-key/usage-summary', method: 'get', params })
}

export function searchAiUsageUsers(keyword) {
  return request({ url: '/system/ai-key/usage-users', method: 'get', params: { keyword } })
}
