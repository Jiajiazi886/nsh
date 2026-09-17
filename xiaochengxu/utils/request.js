const { getEnvironment } = require('../config/env')
const { invalidateSession, getToken } = require('./storage')

function encodeForm(data) {
  return Object.keys(data || {})
    .filter((key) => data[key] !== undefined && data[key] !== null)
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(data[key])}`)
    .join('&')
}

function request(options) {
  const environment = getEnvironment()
  const token = getToken()
  const headers = Object.assign(
    { 'Content-Type': 'application/json;charset=utf-8' },
    options.headers || {},
  )

  if (options.auth !== false && token) {
    headers.Authorization = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: `${environment.baseUrl}${options.url}`,
      method: options.method || 'GET',
      data: options.form ? encodeForm(options.data) : options.data,
      header: headers,
      timeout: options.timeout || 12000,
      success(response) {
        const payload = response.data || {}
        if (response.statusCode === 401 || payload.code === 401) {
          if (options.auth !== false) invalidateSession(token)
          reject(new Error(payload.msg || '登录状态已过期'))
          return
        }
        if (response.statusCode < 200 || response.statusCode >= 300) {
          reject(new Error(payload.msg || `接口请求失败（${response.statusCode}）`))
          return
        }
        if (payload.code !== undefined && payload.code !== 200) {
          reject(new Error(payload.msg || '业务请求失败'))
          return
        }
        resolve(payload)
      },
      fail(error) {
        const detail = error.errMsg || '无法连接后端服务'
        reject(new Error(detail.includes('timeout') ? '接口请求超时' : detail))
      },
    })
  })
}

module.exports = {
  encodeForm,
  request,
}
