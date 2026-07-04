import request from '@/utils/request'

export function listFormulaVersion(query) {
  return request({
    url: '/system/formula-design/list',
    method: 'get',
    params: query
  })
}

export function getFormulaVersion(versionId) {
  return request({
    url: `/system/formula-design/${versionId}`,
    method: 'get'
  })
}

export function getActiveFormulaVersion(scope = 'internal_power_pvp_damage') {
  return request({
    url: '/system/formula-design/active',
    method: 'get',
    params: { scope }
  })
}

export function addFormulaVersion(data) {
  return request({
    url: '/system/formula-design',
    method: 'post',
    data
  })
}

export function updateFormulaVersion(data) {
  return request({
    url: '/system/formula-design',
    method: 'put',
    data
  })
}

export function copyFormulaVersion(versionId) {
  return request({
    url: `/system/formula-design/${versionId}/copy`,
    method: 'post'
  })
}

export function publishFormulaVersion(versionId) {
  return request({
    url: `/system/formula-design/${versionId}/publish`,
    method: 'post'
  })
}

export function rollbackFormulaVersion(versionId) {
  return request({
    url: `/system/formula-design/${versionId}/rollback`,
    method: 'post'
  })
}
