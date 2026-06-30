import request from '@/utils/request'

export function getInternalPowerImageDisplayStatus() {
  return request({
    url: '/system/internal-power-image-display/status',
    method: 'get'
  })
}

export function updateInternalPowerImageDisplayStatus(enabled) {
  return request({
    url: '/system/internal-power-image-display/status',
    method: 'put',
    data: {
      enabled
    }
  })
}
