const TOKEN_KEY = 'nsh-mini-token'
const USER_KEY = 'nsh-mini-user'

function getToken() {
  return wx.getStorageSync(TOKEN_KEY) || ''
}

function setToken(token) {
  wx.setStorageSync(TOKEN_KEY, token)
}

function getUser() {
  return wx.getStorageSync(USER_KEY) || null
}

function setUser(user) {
  wx.setStorageSync(USER_KEY, user)
}

function clearSession() {
  wx.removeStorageSync(TOKEN_KEY)
  wx.removeStorageSync(USER_KEY)
}

module.exports = {
  clearSession,
  getToken,
  getUser,
  setToken,
  setUser,
}
