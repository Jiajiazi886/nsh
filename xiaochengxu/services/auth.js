const { request } = require('../utils/request')

function getAuthConfig() {
  return request({ url: '/authConfig', auth: false })
}

function getCaptcha() {
  return request({ url: '/captchaImage', auth: false })
}

function login(data) {
  return request({
    url: '/login',
    method: 'POST',
    auth: false,
    form: true,
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    data: {
      username: data.username,
      password: data.password,
      code: data.code || '',
      uuid: data.uuid || '',
    },
  })
}

function register(data) {
  return request({
    url: '/register',
    method: 'POST',
    auth: false,
    data: {
      username: data.username,
      password: data.password,
      confirmPassword: data.confirmPassword,
      code: data.code || '',
      uuid: data.uuid || '',
    },
  })
}

function getInfo() {
  return request({ url: '/getInfo' })
}

function logout() {
  return request({ url: '/logout', method: 'POST' })
}

module.exports = {
  getAuthConfig,
  getCaptcha,
  getInfo,
  login,
  logout,
  register,
}
