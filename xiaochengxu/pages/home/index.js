const authService = require('../../services/auth')
const guildService = require('../../services/guild')
const { getEnvironment } = require('../../config/env')
const { getToken } = require('../../utils/storage')

const ROLE_NAMES = {
  admin: '超级管理员',
  common: '帮会管理',
  user: '帮会成员',
  guild_assistant: '帮会助理',
}

Page({
  data: {
    loading: true,
    userName: '',
    nickName: '',
    roleNames: [],
    environmentName: '',
    membership: null,
    application: null,
    statusError: '',
  },

  onLoad() {
    if (!getToken()) {
      wx.reLaunch({ url: '/pages/login/index' })
      return
    }
    this.setData({ environmentName: getEnvironment().name })
  },

  onShow() {
    if (getToken()) this.loadDashboard()
  },

  onPullDownRefresh() {
    this.loadDashboard().finally(() => wx.stopPullDownRefresh())
  },

  async loadDashboard() {
    this.setData({ loading: true, statusError: '' })
    try {
      const [userInfo, guildStatus] = await Promise.all([
        authService.getInfo(),
        guildService.getMyStatus(),
      ])
      const user = userInfo.user || {}
      const roles = userInfo.roles || []
      getApp().updateUser({ user, roles, permissions: userInfo.permissions || [] })
      this.setData({
        userName: user.userName || '',
        nickName: user.nickName || user.userName || '玩家',
        roleNames: roles.map((role) => ROLE_NAMES[role] || role),
        membership: guildStatus.data ? guildStatus.data.current_membership : null,
        application: guildStatus.data ? guildStatus.data.current_application : null,
      })
    } catch (error) {
      this.setData({ statusError: error.message || '工作台加载失败' })
    } finally {
      this.setData({ loading: false })
    }
  },

  openPage(event) {
    wx.navigateTo({ url: event.currentTarget.dataset.url })
  },
})
