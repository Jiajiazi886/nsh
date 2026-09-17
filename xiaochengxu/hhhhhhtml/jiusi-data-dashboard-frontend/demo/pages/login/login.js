const auth = require('../../services/auth')
const { getToken, setToken, clearSession } = require('../../utils/storage')
const { getEnvironment } = require('../../config/env')
Page({
  data: { userName: '', password: '', code: '', uuid: '', captchaEnabled: false,
    captchaImage: '', loading: false, error: '', backendUrl: '' },
  onLoad() { this.setData({ backendUrl: getEnvironment().baseUrl }); return this.retryConnection() },
  input(e) { this.setData({ [e.currentTarget.dataset.field]: e.detail.value }) },
  async retryConnection() {
    if (this.data.loading) return
    this.setData({ loading: true, error: '' })
    try {
      if (getToken()) {
        const user = await auth.validateSession()
        if (user) { wx.switchTab({ url: '/pages/activities/activities' }); return }
      }
      await this.captcha()
    } catch (e) {
      this.setData({ error: e.message })
      if (e.status === 401) await this.captcha()
    } finally { this.setData({ loading: false }) }
  },
  async captcha() {
    try {
      const c = await auth.getCaptcha()
      this.setData({ captchaEnabled: !!c.captchaEnabled,
        captchaImage: c.img ? 'data:image/png;base64,' + c.img : '', uuid: c.uuid || '', code: '' })
    } catch (e) { this.setData({ error: e.message }) }
  },
  async handleLogin() {
    if (this.data.loading) return
    if (!this.data.userName.trim() || !this.data.password) {
      this.setData({ error: '请输入网页版账号和密码' }); return
    }
    if (this.data.captchaEnabled && !this.data.code.trim()) {
      this.setData({ error: '请输入验证码' }); return
    }
    this.setData({ loading: true, error: '' })
    clearSession()
    try {
      const response = await auth.login({ userName: this.data.userName, password: this.data.password,
        code: this.data.code.trim(), uuid: this.data.uuid })
      setToken(response.token)
      await auth.validateSession()
      wx.switchTab({ url: '/pages/activities/activities' })
    } catch (e) {
      clearSession()
      if (this.data.captchaEnabled) await this.captcha()
      this.setData({ error: e.message })
    } finally { this.setData({ loading: false, password: '' }) }
  },
})
