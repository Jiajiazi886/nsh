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

export function recognizeInternalPowerPanelImage(file) {
  const data = new FormData()
  data.append('file', file)
  return request({
    url: '/personal/internal-power-panel-setting/recognize-image',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export function getInternalPowerPanelRecognitionHistory() {
  return request({
    url: '/personal/internal-power-panel-setting/recognition-history',
    method: 'get'
  })
}

export function clearInternalPowerPanelRecognitionHistory() {
  return request({
    url: '/personal/internal-power-panel-setting/recognition-history',
    method: 'delete'
  })
}

export function getInternalPowerPanelTemplates() {
  return request({
    url: '/personal/internal-power-panel-setting/templates',
    method: 'get'
  })
}
