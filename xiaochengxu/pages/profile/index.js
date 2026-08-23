const authService = require('../../services/auth')
const guildService = require('../../services/guild')
const { getEnvironment } = require('../../config/env')
const { clearSession, getUser } = require('../../utils/storage')
const { selectTab } = require('../../utils/tabbar')

const ROLE_NAMES = {
  admin: '超级管理员',
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
    activeTab: 'account',
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
      let memberProfile = null
      if ((session.permissions || []).includes('*:*:*') || (session.permissions || []).includes('personal:profile:edit')) {
        try {
          const profileResponse = await guildService.getMyProfile()
          memberProfile = profileResponse.data || null
        } catch (error) {
          console.warn('当前账号没有可编辑的帮会成员资料', error)
        }
      }
      this.setData({
        user: session.user,
        roles: session.roles,
        roleNames: session.roles.map((role) => ROLE_NAMES[role] || role),
        avatarText: this.getAvatarText(session.user),
        memberProfile,
        playerClass: memberProfile ? memberProfile.player_class : '',
        secondaryClass: memberProfile ? memberProfile.secondary_class : '',
        remark: memberProfile ? memberProfile.remark : '',
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

  async saveMemberProfile() {
    if (!this.data.memberProfile) return
    this.setData({ saving: true })
    try {
      await guildService.updateMyProfile({
        playerClass: this.data.playerClass.trim(),
        secondaryClass: this.data.secondaryClass.trim(),
        remark: this.data.remark.trim(),
      })
      wx.showToast({ title: '玩家资料已保存', icon: 'success' })
      await this.loadUser()
    } catch (error) {
      wx.showToast({ title: error.message || '保存失败', icon: 'none' })
    } finally {
      this.setData({ saving: false })
    }
  },

  logout() {
    wx.showModal({
      title: '退出登录',
      content: '确认退出当前账号？',
      success: async (result) => {
        if (!result.confirm) return
        try {
          await authService.logout()
        } catch (error) {
          console.warn('后端退出失败，继续清理本地会话', error)
        }
        clearSession()
        wx.reLaunch({ url: '/pages/login/index' })
      },
    })
  },
})
