const guildService = require('../../services/guild')

Page({
  data: {
    loading: true,
    searching: false,
    submitting: false,
    keyword: '',
    results: [],
    membership: null,
    application: null,
    selectedGuild: null,
    playerName: '',
    playerClass: '',
    secondaryClass: '',
    remark: '',
  },

  onLoad() {
    this.loadStatus()
  },

  onPullDownRefresh() {
    this.loadStatus().finally(() => wx.stopPullDownRefresh())
  },

  async loadStatus() {
    this.setData({ loading: true })
    try {
      const response = await guildService.getMyStatus()
      const status = response.data || {}
      this.setData({
        membership: status.current_membership || null,
        application: status.current_application || null,
      })
    } catch (error) {
      wx.showToast({ title: error.message || '状态加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  updateField(event) {
    this.setData({ [event.currentTarget.dataset.field]: event.detail.value })
  },

  async searchGuilds() {
    const keyword = this.data.keyword.trim()
    if (!keyword) {
      wx.showToast({ title: '请输入帮会名称', icon: 'none' })
      return
    }
    this.setData({ searching: true, selectedGuild: null })
    try {
      const response = await guildService.searchGuilds(keyword)
      this.setData({ results: response.data || [] })
    } catch (error) {
      wx.showToast({ title: error.message || '搜索失败', icon: 'none' })
    } finally {
      this.setData({ searching: false })
    }
  },

  selectGuild(event) {
    const guildId = Number(event.currentTarget.dataset.id)
    const selectedGuild = this.data.results.find((item) => Number(item.guild_id) === guildId)
    this.setData({ selectedGuild: selectedGuild || null })
  },

  cancelSelection() {
    this.setData({ selectedGuild: null })
  },

  async submitApplication() {
    if (!this.data.selectedGuild || !this.data.playerName.trim()) {
      wx.showToast({ title: '请选择帮会并填写玩家名', icon: 'none' })
      return
    }
    this.setData({ submitting: true })
    try {
      await guildService.applyToGuild({
        guildId: this.data.selectedGuild.guild_id,
        playerName: this.data.playerName.trim(),
        playerClass: this.data.playerClass.trim(),
        secondaryClass: this.data.secondaryClass.trim(),
        remark: this.data.remark.trim(),
      })
      wx.showToast({ title: '申请已提交', icon: 'success' })
      this.setData({ selectedGuild: null, results: [] })
      await this.loadStatus()
    } catch (error) {
      wx.showToast({ title: error.message || '提交失败', icon: 'none' })
    } finally {
      this.setData({ submitting: false })
    }
  },

  quitGuild() {
    wx.showModal({
      title: '确认退出帮会',
      content: '退出后需要重新申请并由管理员审核。',
      success: async (result) => {
        if (!result.confirm) return
        try {
          await guildService.quitGuild()
          wx.showToast({ title: '已退出帮会', icon: 'success' })
          await this.loadStatus()
        } catch (error) {
          wx.showToast({ title: error.message || '退会失败', icon: 'none' })
        }
      },
    })
  },
})
