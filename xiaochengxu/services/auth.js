const { getClient } = require('./activities')
const { getToken, setUser } = require('../utils/storage')

function getAuthConfig() { return getClient().authConfig() }
function getCaptcha() { return getClient().captcha() }
async function login(data) {
  const response = await getClient().login({
    userName: (data.username || data.userName || '').trim(),
    password: data.password, code: data.code || '', uuid: data.uuid || '',
  })
  if (!response || typeof response.accessToken !== 'string' || !response.accessToken) {
    throw new Error('后端未返回有效登录凭证')
  }
  return { token: response.accessToken, expiresIn: response.expiresIn }
}
async function validateSession() {
  const token = getToken()
  if (!token) return null
  const user = await getClient().me()
  if (getToken() !== token) throw new Error('登录账号已变化，请重试')
  setUser({ user: { userId: user.userId, userName: user.userName, nickName: user.nickName },
    roles: user.roles || [], permissions: user.permissions || [] })
  return user
}
function logout() { return getClient().logout() }
module.exports = { getAuthConfig, getCaptcha, login, validateSession, logout }

const { request } = require('../utils/request')
// Existing profile and registration DTOs still use the same SysUser/JWT backend.
module.exports.getInfo = () => request({ url: '/getInfo' })
module.exports.register = data => request({ url: '/register', method: 'POST', auth: false, data })
