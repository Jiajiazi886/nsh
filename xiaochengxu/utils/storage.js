const { getEnvironment } = require('../config/env')
const { loginPath } = require('../config/auth')
const TOKEN_KEY = 'nsh-mini-token'
const REFRESH_TOKEN_KEY = 'nsh-mini-refresh-token'
const USER_KEY = 'nsh-mini-user'
const ROOT_KEY = 'nsh-mini-auth-root'
let redirecting = false
function clearSession() {
  require('./profession-styles').clear()
  wx.removeStorageSync(TOKEN_KEY)
  wx.removeStorageSync(REFRESH_TOKEN_KEY)
  wx.removeStorageSync(USER_KEY)
  wx.removeStorageSync(ROOT_KEY)
  if (typeof getApp === 'function') {
    const app = getApp()
    if (app && app.globalData) app.globalData.user = null
  }
}
function getToken() {
  const root = wx.getStorageSync(ROOT_KEY)
  if (root && root !== getEnvironment().baseUrl) { clearSession(); return '' }
  return wx.getStorageSync(TOKEN_KEY) || ''
}
function setToken(token) {
  if (typeof token !== 'string' || !token) throw new Error('后端未返回有效登录凭证')
  wx.setStorageSync(TOKEN_KEY, token)
  wx.setStorageSync(ROOT_KEY, getEnvironment().baseUrl)
}
function getRefreshToken() { getToken(); return wx.getStorageSync(REFRESH_TOKEN_KEY) || '' }
function setRefreshToken(token) {
  if (typeof token !== 'string' || !token) throw new Error('后端未返回有效刷新令牌')
  wx.setStorageSync(REFRESH_TOKEN_KEY, token)
  wx.setStorageSync(ROOT_KEY, getEnvironment().baseUrl)
}
function getUser() { getToken(); return wx.getStorageSync(USER_KEY) || null }
function setUser(user) {
  wx.setStorageSync(USER_KEY, user)
  if (typeof getApp === 'function') {
    const app = getApp()
    if (app && app.globalData) app.globalData.user = user
  }
}
function invalidateSession(expectedToken) {
  // A late 401 from another account must not erase the current login.
  if (expectedToken !== getToken()) return false
  clearSession()
  if (!redirecting) {
    redirecting = true
    wx.reLaunch({ url: loginPath, complete() { redirecting = false } })
  }
  return true
}
module.exports = { clearSession, getToken, getRefreshToken, getUser, setToken, setRefreshToken, setUser, invalidateSession }
