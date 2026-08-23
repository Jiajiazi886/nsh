const authService = require('../../services/auth')
const { clearSession, getUser } = require('../../utils/storage')

Page({
  data: {
    user: {},
    avatarText: '玩',
    roles: [],
    loading: true,
  },

  onLoad() {
    const session = getUser() || {}
    const user = session.user || {}
    this.setData({
      user,
      roles: session.roles || [],
      avatarText: this.getAvatarText(user),
    })
    this.loadUser()
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
