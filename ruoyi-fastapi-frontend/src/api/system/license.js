import request from '@/utils/request'

export function listLicenseAccounts(params) {
  return request({ url: '/api/v1/license-admin/accounts', method: 'get', params })
}

export function grantLicense(data) {
  return request({ url: '/api/v1/license-admin/grants', method: 'post', data })
}

export function revokeLicense(data) {
  return request({ url: '/api/v1/license-admin/revocations', method: 'post', data })
}

export function updateLicenseRemark(userId, data) {
  return request({ url: '/api/v1/license-admin/accounts/' + userId + '/remark', method: 'put', data })
}

export function listLicenseAudit(params) {
  return request({ url: '/api/v1/license-admin/audit', method: 'get', params })
}
