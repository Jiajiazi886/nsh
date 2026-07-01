import request from '@/utils/request'

// 查询当前用户内功列表和额度
export function listInternalPowers() {
  return request({
    url: '/personal/internal-power/list',
    method: 'get'
  })
}

// 查询启用内功预设
export function listInternalPowerPresets() {
  return request({
    url: '/personal/internal-power/presets',
    method: 'get'
  })
}

// 查询启用内功词条
export function listInternalPowerEntries() {
  return request({
    url: '/personal/internal-power/entries',
    method: 'get'
  })
}

// 新增内功
export function addInternalPower(data) {
  return request({
    url: '/personal/internal-power',
    method: 'post',
    data
  })
}

// 修改内功
export function updateInternalPower(powerId, data) {
  return request({
    url: `/personal/internal-power/${powerId}`,
    method: 'put',
    data
  })
}

// 删除内功
export function deleteInternalPower(powerId) {
  return request({
    url: `/personal/internal-power/${powerId}`,
    method: 'delete'
  })
}

// 首次导入本地内功
export function importLocalInternalPowers(powers) {
  return request({
    url: '/personal/internal-power/import-local',
    method: 'post',
    data: {
      powers
    }
  })
}

// 内功图片AI识别
export function recognizeInternalPowerImages(files, prompt = '') {
  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })
  formData.append('prompt', prompt)
  return request({
    url: '/personal/internal-power/recognize-images',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
      encrypt: false,
      repeatSubmit: false
    },
    timeout: 120000
  })
}

// 单张内功图片AI识别
export function recognizeInternalPowerImage(file, prompt = '') {
  return recognizeInternalPowerImages([file], prompt)
}

// 查询内功图片AI识别历史
export function listInternalPowerRecognitionHistory() {
  return request({
    url: '/personal/internal-power/recognition-history',
    method: 'get'
  })
}

// 清空内功图片AI识别历史
export function clearInternalPowerRecognitionHistory() {
  return request({
    url: '/personal/internal-power/recognition-history',
    method: 'delete'
  })
}

// 标记内功图片AI识别历史已保存
export function markInternalPowerRecognitionHistorySaved(recordId, savedPowerId) {
  return request({
    url: `/personal/internal-power/recognition-history/${recordId}/saved`,
    method: 'put',
    data: {
      savedPowerId
    }
  })
}
