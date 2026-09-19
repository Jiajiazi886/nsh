const authService = require('../../services/auth')
const { getEnvironment } = require('../../config/env')
const { clearSession, getUser, getToken } = require('../../utils/storage')
const { selectTab } = require('../../utils/tabbar')

const ROLE_NAMES = {
  cptbtptp: '超级管理员',
  admin: '超级管理员（旧）',
  common: '帮会管理',
  user: '帮会成员',
  guild_assistant: '帮会助理',
}

Page({
  data: {
    user: {},
    avatarText: '玩',
    roles: [],
    roleNames: [],
    activeTab: 'player',
    memberProfile: null,
    playerClass: '',
    secondaryClass: '',
    remark: '',
    environment: getEnvironment(),
    saving: false,
    loading: true,
  },

  onLoad() {
    const session = getUser() || {}
    const user = session.user || {}
    this.setData({
      user,
      roles: session.roles || [],
      roleNames: (session.roles || []).map((role) => ROLE_NAMES[role] || role),
      avatarText: this.getAvatarText(user),
    })
    this.loadUser()
  },

  onShow() {
    selectTab(this, 4)
  },

  switchSection(event) {
    this.setData({ activeTab: event.currentTarget.dataset.tab })
  },

  async loadUser() {
    try {
      const response = await authService.getInfo()
      const session = {
        user: response.user || {},
        roles: response.roles || [],
        permissions: response.permissions || [],
      }
      getApp().updateUser(session)
      this.setData({
        user: session.user,
        roles: session.roles,
        roleNames: session.roles.map((role) => ROLE_NAMES[role] || role),
        avatarText: this.getAvatarText(session.user),
      })
    } catch (error) {
      wx.showToast({ title: error.message || '用户信息加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  getAvatarText(user) {
    const name = user.nickName || user.userName || '玩'
    return name.slice(0, 1)
  },

  updateField(event) {
    this.setData({ [event.currentTarget.dataset.field]: event.detail.value })
  },

  logout() {
    wx.showModal({
      title: '退出登录',
      content: '确认退出当前账号？',
      success: async (result) => {
        if (!result.confirm) return
        const token = getToken()
        try {
          await authService.logout()
        } catch (error) {
          console.warn('后端退出失败，继续清理本地会话', error)
          wx.showToast({ title: '仅退出本机，后端退出未确认', icon: 'none' })
        }
        if (getToken() && getToken() !== token) return
        clearSession()
        wx.reLaunch({ url: '/pages/login/index' })
      },
    })
  },
})
