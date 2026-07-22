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
