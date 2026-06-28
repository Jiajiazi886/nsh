import request from '@/utils/request'

// 查询当前用户内功词条换算
export function getInternalPowerEntryConversion() {
  return request({
    url: '/personal/internal-power-entry-conversion',
    method: 'get'
  })
}

// 保存当前用户内功词条换算
export function saveInternalPowerEntryConversion(data) {
  return request({
    url: '/personal/internal-power-entry-conversion',
    method: 'put',
    data
  })
}
