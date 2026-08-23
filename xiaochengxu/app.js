const { getEnvironment } = require('./config/env')
const { getToken, getUser, setUser } = require('./utils/storage')

App({
  globalData: {
    environment: null,
    user: null,
  },

  onLaunch() {
    this.globalData.environment = getEnvironment()
    this.globalData.user = getUser()
  },

  hasSession() {
    return Boolean(getToken())
  },

  updateUser(user) {
    this.globalData.user = user
    setUser(user)
  },
})
