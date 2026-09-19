const authService = require('../../services/auth')
const guildService = require('../../services/guild')
const { selectTab } = require('../../utils/tabbar')

function can(permissions, permission) {
  return permissions.includes('*:*:*') || permissions.includes(permission)
}

Page({
  data: {
    activeTab: 'overview',
    loading: true,
    isManager: false,
    canViewMembers: false,
    canAddMember: false,
    canReview: false,
    canApprove: false,
    canReject: false,
    canEditGuild: false,
    dashboard: {
      guild: {},
      member_summary: {},
      review_summary: {},
      schedule_summary: {},
      class_distribution: [],
    },
    guildInitial: '会',
    guildInfo: null,
    members: [],
    visibleMembers: [],
    applications: [],
    membership: null,
    application: null,
    keyword: '',
    showAddForm: false,
    playerName: '',
    playerClass: '',
    secondaryClass: '',
    remark: '',
    guildName: '',
    submitting: false,
    errorMessage: '',
  },

  onShow() {
    selectTab(this, 2)
    this.loadPage()
  },

  onPullDownRefresh() {
    this.loadPage().finally(() => wx.stopPullDownRefresh())
  },

  switchSection(event) {
    this.setData({ activeTab: event.currentTarget.dataset.tab })
  },

  updateField(event) {
    const field = event.currentTarget.dataset.field
    const value = event.detail.value
    this.setData({ [field]: value })
    if (field === 'keyword') this.applyMemberFilter(value)
  },

  applyMemberFilter(keyword) {
    const normalized = (keyword || '').trim().toLowerCase()
    const visibleMembers = normalized
      ? this.data.members.filter((member) => [member.player_name, member.player_class, member.secondary_class]
        .some((value) => String(value || '').toLowerCase().includes(normalized)))
      : this.data.members
    this.setData({ visibleMembers })
  },

  async loadPage() {
    this.setData({ loading: true, errorMessage: '' })
    try {
      const userInfo = await authService.getInfo()
      const roles = userInfo.roles || []
      const permissions = userInfo.permissions || []
      const isManager = roles.includes('cptbtptp') || roles.includes('common')
      const canViewMembers = isManager && can(permissions, 'guild:member:list')
      const canAddMember = isManager && can(permissions, 'guild:member:add')
      const canReview = isManager && can(permissions, 'guild:review:member:list')
      const canApprove = isManager && can(permissions, 'guild:review:member:approve')
      const canReject = isManager && can(permissions, 'guild:review:member:reject')
      const canEditGuild = isManager && can(permissions, 'guild:member:edit')
      const dashboardResponse = await guildService.getDashboardSummary()
      const dashboard = dashboardResponse.data || this.data.dashboard
      let guildInfo = null
      let members = []
      let applications = []
      let membership = null
      let application = null
      if (isManager) {
        if (canViewMembers) {
          const [guildResponse, memberResponse] = await Promise.all([
            guildService.getGuildInfo(),
            guildService.getMembers(),
          ])
          guildInfo = guildResponse.data || null
          members = memberResponse.data || []
        }
        if (canReview) {
          const pendingResponse = await guildService.getPendingApplications()
          applications = pendingResponse.data || []
        }
      } else {
        const statusResponse = await guildService.getMyStatus()
        const status = statusResponse.data || {}
        membership = status.current_membership || null
        application = status.current_application || null
      }
      this.setData({
        isManager,
        canViewMembers,
        canAddMember,
        canReview,
        canApprove,
        canReject,
        canEditGuild,
        dashboard,
        guildInitial: dashboard.guild && dashboard.guild.guild_name
          ? dashboard.guild.guild_name.slice(0, 1)
          : '会',
        guildInfo,
        members,
        visibleMembers: members,
        applications,
        membership,
        application,
        guildName: guildInfo ? guildInfo.guild_name : '',
      })
    } catch (error) {
      this.setData({ errorMessage: error.message || '帮会数据加载失败' })
    } finally {
      this.setData({ loading: false })
    }
  },

  openJoinGuild() {
    wx.navigateTo({ url: '/pages/guild-join/index' })
  },

  toggleAddForm() {
    this.setData({ showAddForm: !this.data.showAddForm })
  },

  async addMember() {
    if (!this.data.playerName.trim()) {
      wx.showToast({ title: '请输入玩家名', icon: 'none' })
      return
    }
    this.setData({ submitting: true })
    try {
      await guildService.addMember({
        playerName: this.data.playerName.trim(),
        playerClass: this.data.playerClass.trim(),
        secondaryClass: this.data.secondaryClass.trim(),
        remark: this.data.remark.trim(),
      })
      wx.showToast({ title: '成员已添加', icon: 'success' })
      this.setData({ showAddForm: false, playerName: '', playerClass: '', secondaryClass: '', remark: '' })
      await this.loadPage()
    } catch (error) {
      wx.showToast({ title: error.message || '添加失败', icon: 'none' })
    } finally {
      this.setData({ submitting: false })
    }
  },

  reviewApplication(event) {
    const applicationId = event.currentTarget.dataset.id
    const approved = event.currentTarget.dataset.action === 'approve'
    wx.showModal({
      title: approved ? '同意入会' : '拒绝入会',
      content: `确认${approved ? '同意' : '拒绝'}这条入会申请？`,
      success: async (result) => {
        if (!result.confirm) return
        try {
          await guildService.reviewApplication(applicationId, approved)
          wx.showToast({ title: '处理成功', icon: 'success' })
          await this.loadPage()
        } catch (error) {
          wx.showToast({ title: error.message || '处理失败', icon: 'none' })
        }
      },
    })
  },

  async saveGuildName() {
    const guildName = this.data.guildName.trim()
    if (!guildName) {
      wx.showToast({ title: '帮会名称不能为空', icon: 'none' })
      return
    }
    this.setData({ submitting: true })
    try {
      await guildService.updateGuildName(guildName)
      wx.showToast({ title: '帮会名称已保存', icon: 'success' })
      await this.loadPage()
    } catch (error) {
      wx.showToast({ title: error.message || '保存失败', icon: 'none' })
    } finally {
      this.setData({ submitting: false })
    }
  },
})
