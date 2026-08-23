const authService = require('../../services/auth')
const battleService = require('../../services/battle')
const guildService = require('../../services/guild')
const scheduleService = require('../../services/schedule')
const { selectTab } = require('../../utils/tabbar')

function can(permissions, permission) {
  return permissions.includes('*:*:*') || permissions.includes(permission)
}

Page({
  data: {
    activeTab: 'overview',
    loading: true,
    isManager: false,
    canReview: false,
    canViewSchedule: false,
    dashboard: {
      guild: {},
      review_summary: {},
      schedule_summary: {},
      battle_summary: {},
      active_invite_summary: null,
    },
    invites: [],
    registrations: [],
    leaves: [],
    schedule: null,
    inviteCode: '',
    showCreateForm: false,
    battleName: '',
    battleDate: '',
    battleTime: '20:00',
    expireHours: 24,
    remark: '',
    submitting: false,
    errorMessage: '',
  },

  onShow() {
    selectTab(this, 1)
    this.loadPage()
  },

  onPullDownRefresh() {
    this.loadPage().finally(() => wx.stopPullDownRefresh())
  },

  switchSection(event) {
    this.setData({ activeTab: event.currentTarget.dataset.tab })
  },

  updateField(event) {
    this.setData({ [event.currentTarget.dataset.field]: event.detail.value })
  },

  async loadPage() {
    this.setData({ loading: true, errorMessage: '' })
    try {
      const userInfo = await authService.getInfo()
      const roles = userInfo.roles || []
      const permissions = userInfo.permissions || []
      const isManager = roles.includes('admin') || roles.includes('common')
      const canReview = isManager && can(permissions, 'guild:review:battle:list')
      const canViewSchedule = can(permissions, 'guild:schedule:list')
      const requests = [guildService.getDashboardSummary()]
      if (canReview) {
        requests.push(battleService.listInvites())
        requests.push(battleService.listRegistrations('signup'))
        requests.push(battleService.listRegistrations('leave'))
      }
      if (canViewSchedule) requests.push(scheduleService.getCurrentSchedule())
      const results = await Promise.all(requests)
      let cursor = 1
      this.setData({
        isManager,
        canReview,
        canViewSchedule,
        dashboard: results[0].data || {},
        invites: canReview ? (results[cursor++].data || []) : [],
        registrations: canReview ? (results[cursor++].data || []) : [],
        leaves: canReview ? (results[cursor++].data || []) : [],
        schedule: canViewSchedule ? (results[cursor].data || null) : null,
      })
    } catch (error) {
      this.setData({ errorMessage: error.message || '活动数据加载失败' })
    } finally {
      this.setData({ loading: false })
    }
  },

  openInvite() {
    const inviteCode = this.data.inviteCode.trim()
    if (!inviteCode) {
      wx.showToast({ title: '请输入邀请码', icon: 'none' })
      return
    }
    wx.navigateTo({ url: `/pages/battle-invite/index?inviteCode=${encodeURIComponent(inviteCode)}` })
  },

  openSchedule() {
    wx.navigateTo({ url: '/pages/schedule/index' })
  },

  toggleCreateForm() {
    this.setData({ showCreateForm: !this.data.showCreateForm })
  },

  async createInvite() {
    const battleName = this.data.battleName.trim()
    if (!battleName) {
      wx.showToast({ title: '请输入活动名称', icon: 'none' })
      return
    }
    const battleTime = this.data.battleDate
      ? `${this.data.battleDate} ${this.data.battleTime || '20:00'}:00`
      : null
    this.setData({ submitting: true })
    try {
      await battleService.createInvite({
        battleName,
        battleTime,
        expireHours: this.data.expireHours,
        remark: this.data.remark.trim(),
      })
      wx.showToast({ title: '活动已创建', icon: 'success' })
      this.setData({ showCreateForm: false, battleName: '', battleDate: '', remark: '' })
      await this.loadPage()
    } catch (error) {
      wx.showToast({ title: error.message || '创建失败', icon: 'none' })
    } finally {
      this.setData({ submitting: false })
    }
  },

  reviewRegistration(event) {
    const registrationId = event.currentTarget.dataset.id
    const approved = event.currentTarget.dataset.action === 'approve'
    wx.showModal({
      title: approved ? '通过申请' : '拒绝申请',
      content: `确认${approved ? '通过' : '拒绝'}这条活动申请？`,
      success: async (result) => {
        if (!result.confirm) return
        try {
          await battleService.reviewRegistration(registrationId, approved)
          wx.showToast({ title: '处理成功', icon: 'success' })
          await this.loadPage()
        } catch (error) {
          wx.showToast({ title: error.message || '处理失败', icon: 'none' })
        }
      },
    })
  },
})
