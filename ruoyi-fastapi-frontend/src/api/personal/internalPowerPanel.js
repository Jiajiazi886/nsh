import request from '@/utils/request'

// 查询当前用户内功收益面板设置
export function getInternalPowerPanelSetting() {
  return request({
    url: '/personal/internal-power-panel-setting',
    method: 'get',
    headers: { silentError: true }
  })
}

// 保存当前用户内功收益面板设置
export function saveInternalPowerPanelSetting(data) {
  return request({
    url: '/personal/internal-power-panel-setting',
    method: 'put',
    data
  })
}
