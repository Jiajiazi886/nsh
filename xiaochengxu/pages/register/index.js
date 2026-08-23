const authService = require('../../services/auth')

Page({
  data: {
    username: '',
    password: '',
    confirmPassword: '',
    code: '',
    uuid: '',
    captchaSrc: '',
    captchaEnabled: false,
    registerEnabled: true,
    showPassword: false,
    loading: false,
  },

  onLoad() {
    this.loadAuthState()
  },

  async loadAuthState() {
    try {
      const [config, captcha] = await Promise.all([
        authService.getAuthConfig(),
        authService.getCaptcha(),
      ])
      this.setData({
        registerEnabled: Boolean(config.registerEnabled),
        captchaEnabled: Boolean(captcha.captchaEnabled),
        captchaSrc: captcha.img ? `data:image/png;base64,${captcha.img}` : '',
        uuid: captcha.uuid || '',
      })
    } catch (error) {
      wx.showToast({ title: error.message || '认证服务不可用', icon: 'none' })
    }
  },

  updateField(event) {
    this.setData({ [event.currentTarget.dataset.field]: event.detail.value })
  },

  togglePassword() {
    this.setData({ showPassword: !this.data.showPassword })
  },

  async submitRegister() {
    const username = this.data.username.trim()
    if (!this.data.registerEnabled) {
      wx.showToast({ title: '系统暂未开放注册', icon: 'none' })
      return
    }
    if (username.length < 2 || username.length > 30) {
      wx.showToast({ title: '账号长度应为 2 至 30 位', icon: 'none' })
      return
    }
    if (this.data.password.length < 6) {
      wx.showToast({ title: '密码至少 6 位', icon: 'none' })
      return
    }
    if (this.data.password !== this.data.confirmPassword) {
      wx.showToast({ title: '两次密码输入不一致', icon: 'none' })
      return
    }
    if (this.data.captchaEnabled && !this.data.code.trim()) {
      wx.showToast({ title: '请输入验证码', icon: 'none' })
      return
    }

    this.setData({ loading: true })
    try {
      await authService.register({
        username,
        password: this.data.password,
        confirmPassword: this.data.confirmPassword,
        code: this.data.code.trim(),
        uuid: this.data.uuid,
      })
      wx.showToast({ title: '注册成功', icon: 'success' })
      setTimeout(() => {
        wx.redirectTo({ url: `/pages/login/index?username=${encodeURIComponent(username)}` })
      }, 500)
    } catch (error) {
      wx.showToast({ title: error.message || '注册失败', icon: 'none' })
      if (this.data.captchaEnabled) this.loadAuthState()
    } finally {
      this.setData({ loading: false })
    }
  },
})
