const battleService = require('../../services/battle')

Page({
  data: {
    inviteCode: '',
    invite: null,
    loading: false,
    submitting: false,
    playerName: '',
    playerClass: '',
    secondaryClass: '',
    applicantName: '',
    applicantContact: '',
    remark: '',
  },

  onLoad(query) {
    if (query.inviteCode) {
      this.setData({ inviteCode: decodeURIComponent(query.inviteCode) })
      this.loadInvite()
    }
  },

  updateField(event) {
    this.setData({ [event.currentTarget.dataset.field]: event.detail.value })
  },

  async loadInvite() {
    const inviteCode = this.data.inviteCode.trim()
    if (!inviteCode) {
      wx.showToast({ title: '请输入邀请码', icon: 'none' })
      return
    }
    this.setData({ loading: true, invite: null })
    try {
      const response = await battleService.getInvite(inviteCode)
      this.setData({ invite: response.data || null })
    } catch (error) {
      wx.showToast({ title: error.message || '邀请链接无效', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  async submitJoin() {
    if (!this.data.invite || !this.data.playerName.trim()) {
      wx.showToast({ title: '请先读取邀请并填写玩家名', icon: 'none' })
      return
    }
    this.setData({ submitting: true })
    try {
      await battleService.submitJoin(this.data.inviteCode.trim(), {
        playerName: this.data.playerName.trim(),
        playerClass: this.data.playerClass.trim(),
        secondaryClass: this.data.secondaryClass.trim(),
        applicantName: this.data.applicantName.trim(),
        applicantContact: this.data.applicantContact.trim(),
        remark: this.data.remark.trim(),
      })
      wx.showToast({ title: '入会申请已提交', icon: 'success' })
    } catch (error) {
      wx.showToast({ title: error.message || '申请提交失败', icon: 'none' })
    } finally {
      this.setData({ submitting: false })
    }
  },
})
