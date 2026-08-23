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
    isGuildManager: false,
    canManageMembers: false,
    guild: null,
    memberSummary: null,
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
      const userInfo = await authService.getInfo()
      const user = userInfo.user || {}
      const roles = userInfo.roles || []
      const permissions = userInfo.permissions || []
      const isGuildManager = roles.includes('admin') || roles.includes('common')
      const canManageMembers = permissions.includes('*:*:*') || permissions.includes('guild:member:list')
      const dashboardResponse = await guildService.getDashboardSummary()
      const dashboard = dashboardResponse.data || {}
      let guildStatus = null
      if (!isGuildManager) {
        const statusResponse = await guildService.getMyStatus()
        guildStatus = statusResponse.data || {}
      }

      getApp().updateUser({ user, roles, permissions })
      this.setData({
        userName: user.userName || '',
        nickName: user.nickName || user.userName || '玩家',
        roleNames: roles.map((role) => ROLE_NAMES[role] || role),
        isGuildManager,
        canManageMembers: isGuildManager && canManageMembers,
        guild: dashboard.guild || null,
        memberSummary: dashboard.member_summary || null,
        membership: guildStatus ? guildStatus.current_membership : null,
        application: guildStatus ? guildStatus.current_application : null,
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
