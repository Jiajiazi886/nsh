import request from '@/utils/request'

// 查询当前用户内功列表和额度
export function listInternalPowers() {
  return request({
    url: '/personal/internal-power/list',
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

// 内功图片识别占位
export function recognizeInternalPowerImages(files) {
  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })
  return request({
    url: '/personal/internal-power/recognize-images',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
      encrypt: false
    }
  })
}
