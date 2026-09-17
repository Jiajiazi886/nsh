const authService = require('../../services/auth')
const { getEnvironment } = require('../../config/env')
const { clearSession, getToken, setToken } = require('../../utils/storage')

Page({
  data: {
    username: '',
    password: '',
    code: '',
    uuid: '',
    captchaSrc: '',
    captchaEnabled: false,
    registerEnabled: false,
    showPassword: false,
    loading: false,
    environmentName: '',
    backendUrl: '',
    error: '',
  },

  async onLoad(query = {}) {
    this.setData({
      username: query.username ? decodeURIComponent(query.username) : '',
      environmentName: getEnvironment().name,
      backendUrl: getEnvironment().baseUrl,
    })
    await this.retryConnection()
  },

  async retryConnection() {
    if (this.data.loading) return
    this.setData({ loading: true, error: '' })
    try {
      if (getToken()) {
        const user = await authService.validateSession()
        if (user) { wx.switchTab({ url: '/pages/home/index' }); return }
      }
      await this.loadAuthState()
    } catch (error) {
      this.setData({ error: error.message || '无法连接后端，请重试' })
      if (error.status === 401) await this.loadAuthState()
    } finally { this.setData({ loading: false }) }
  },

  async loadAuthState() {
    try {
      const [config, captcha] = await Promise.all([
        authService.getAuthConfig(),
        authService.getCaptcha(),
      ])
      this.setData({
        error: '',
        registerEnabled: Boolean(config.registerEnabled),
        captchaEnabled: Boolean(captcha.captchaEnabled),
        captchaSrc: captcha.img ? `data:image/png;base64,${captcha.img}` : '',
        uuid: captcha.uuid || '',
      })
    } catch (error) {
      this.setData({ error: error.message || '认证服务不可用' })
      wx.showToast({ title: error.message || '认证服务不可用', icon: 'none' })
    }
  },

  onUsernameInput(event) {
    this.setData({ username: event.detail.value })
  },

  onPasswordInput(event) {
    this.setData({ password: event.detail.value })
  },

  onCodeInput(event) {
    this.setData({ code: event.detail.value })
  },

  togglePassword() {
    this.setData({ showPassword: !this.data.showPassword })
  },

  refreshCaptcha() {
    authService.getCaptcha().then((captcha) => {
      this.setData({
        captchaEnabled: Boolean(captcha.captchaEnabled),
        captchaSrc: captcha.img ? `data:image/png;base64,${captcha.img}` : '',
        uuid: captcha.uuid || '',
        code: '',
      })
    }).catch((error) => {
      wx.showToast({ title: error.message, icon: 'none' })
    })
  },

  async submitLogin() {
    if (this.data.loading) return
    const username = this.data.username.trim()
    if (!username || !this.data.password) {
      wx.showToast({ title: '请输入账号和密码', icon: 'none' })
      return
    }
    if (this.data.captchaEnabled && !this.data.code.trim()) {
      wx.showToast({ title: '请输入验证码', icon: 'none' })
      return
    }

    this.setData({ loading: true, error: '' })
    clearSession()
    try {
      const response = await authService.login({
        username,
        password: this.data.password,
        code: this.data.code.trim(),
        uuid: this.data.uuid,
      })
      setToken(response.token)
      const userInfo = await authService.getInfo()
      getApp().updateUser({
        user: userInfo.user,
        roles: userInfo.roles || [],
        permissions: userInfo.permissions || [],
      })
      wx.switchTab({ url: '/pages/home/index' })
    } catch (error) {
      clearSession()
      this.setData({ error: error.message || '登录失败' })
      wx.showToast({ title: error.message || '登录失败', icon: 'none' })
      if (this.data.captchaEnabled) this.refreshCaptcha()
    } finally {
      this.setData({ loading: false, password: '' })
    }
  },

  openRegister() {
    wx.navigateTo({ url: '/pages/register/index' })
  },
})
