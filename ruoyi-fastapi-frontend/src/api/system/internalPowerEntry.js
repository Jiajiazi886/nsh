import request from '@/utils/request'

// 查询内功词条列表
export function listInternalPowerEntry(query) {
  return request({
    url: '/system/internal-power-entry/list',
    method: 'get',
    params: query
  })
}

// 查询内功词条详细
export function getInternalPowerEntry(entryId) {
  return request({
    url: `/system/internal-power-entry/${entryId}`,
    method: 'get'
  })
}

// 新增内功词条
export function addInternalPowerEntry(data) {
  return request({
    url: '/system/internal-power-entry',
    method: 'post',
    data
  })
}

// 修改内功词条
export function updateInternalPowerEntry(data) {
  return request({
    url: '/system/internal-power-entry',
    method: 'put',
    data
  })
}

// 删除内功词条
export function delInternalPowerEntry(entryIds) {
  return request({
    url: `/system/internal-power-entry/${entryIds}`,
    method: 'delete'
  })
}
