const authService = require('../../services/auth')
const battleService = require('../../services/battle')
const guildService = require('../../services/guild')
const { selectTab } = require('../../utils/tabbar')

function can(permissions, permission) {
  return permissions.includes('*:*:*') || permissions.includes(permission)
}

Page({
  data: {
    activeTab: 'overview',
    loading: true,
    canViewHistory: false,
    dashboard: {
      guild: {},
      battle_summary: {},
      member_summary: {},
      latest_battles: [],
      top_records: [],
    },
    battles: [],
    selectedBattle: null,
    battleRecords: [],
    detailLoading: false,
    errorMessage: '',
  },

  onShow() {
    selectTab(this, 3)
    this.loadPage()
  },

  onPullDownRefresh() {
    this.loadPage().finally(() => wx.stopPullDownRefresh())
  },

  switchSection(event) {
    this.setData({ activeTab: event.currentTarget.dataset.tab })
  },

  async loadPage() {
    this.setData({ loading: true, errorMessage: '' })
    try {
      const userInfo = await authService.getInfo()
      const permissions = userInfo.permissions || []
      const canViewHistory = can(permissions, 'guild:battle:list')
      const dashboardResponse = await guildService.getDashboardSummary()
      let battles = []
      if (canViewHistory) {
        const historyResponse = await battleService.listHistory(1, 30)
        battles = historyResponse.data ? (historyResponse.data.rows || []) : []
      }
      const dashboard = dashboardResponse.data || this.data.dashboard
      dashboard.latest_battles = (dashboard.latest_battles || []).map((item) => ({
        ...item,
        resultClass: item.battle_result && item.battle_result.includes('胜') ? 'result-win' : '',
      }))
      this.setData({
        canViewHistory,
        dashboard,
        battles,
      })
    } catch (error) {
      this.setData({ errorMessage: error.message || '战绩数据加载失败' })
    } finally {
      this.setData({ loading: false })
    }
  },

  async openBattle(event) {
    const battleId = Number(event.currentTarget.dataset.id)
    const selectedBattle = this.data.battles.find((item) => Number(item.battle_id) === battleId)
    this.setData({ selectedBattle: selectedBattle || null, battleRecords: [], detailLoading: true })
    try {
      const response = await battleService.getBattleRecords(battleId)
      this.setData({ battleRecords: response.data || [] })
    } catch (error) {
      wx.showToast({ title: error.message || '明细加载失败', icon: 'none' })
    } finally {
      this.setData({ detailLoading: false })
    }
  },

  closeBattle() {
    this.setData({ selectedBattle: null, battleRecords: [] })
  },

  noop() {},
})
