const { getClient } = require('./activities')
const { clearSession, getToken, getRefreshToken, setToken, setRefreshToken, setUser } = require('../utils/storage')

function getAuthConfig() { return getClient().authConfig() }
function getCaptcha() { return getClient().captcha() }
async function login(data) {
  const response = await getClient().login({
    userName: (data.username || data.userName || '').trim(),
    password: data.password, code: data.code || '', uuid: data.uuid || '',
    clientType: 'wechat-miniapp',
  })
  if (!response || typeof response.accessToken !== 'string' || !response.accessToken) {
    throw new Error('后端未返回有效登录凭证')
  }
  setToken(response.accessToken)
  if (response.refreshToken) setRefreshToken(response.refreshToken)
  return { token: response.accessToken, refreshToken: response.refreshToken || '', expiresIn: response.expiresIn }
}
async function refresh() {
  const token = getRefreshToken()
  if (!token) throw new Error('没有可用的刷新令牌')
  const response = await getClient().refresh({ refreshToken: token, clientType: 'wechat-miniapp' })
  if (!response || typeof response.accessToken !== 'string' || !response.accessToken || typeof response.refreshToken !== 'string' || !response.refreshToken) {
    throw new Error('后端未返回有效刷新凭证')
  }
  setToken(response.accessToken)
  setRefreshToken(response.refreshToken)
  return response
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
async function logout() {
  try { return await getClient().logout() } finally { clearSession() }
}
module.exports = { getAuthConfig, getCaptcha, login, refresh, validateSession, logout }

const { request } = require('../utils/request')
// Existing profile and registration DTOs still use the same SysUser/JWT backend.
module.exports.getInfo = () => request({ url: '/getInfo' })
module.exports.register = data => request({ url: '/register', method: 'POST', auth: false, data })
