const { store: S, formatNumber, metricValue, metricSortValue } = require('../../utils/store')
const { store: Demo } = require('../../utils/demo-store')

Page({
  data: {
    keyword: '',
    metrics: [],
    activeMetric: '',
    list: [],
    analysisActivity: {}
  },

  onShow() {
    const demoState = Demo.getState()
    const activity = Demo.getActivity(demoState.selectedAnalysisActivityId) || demoState.activities[0]
    this.setData({ analysisActivity: activity ? { title: activity.title, meta: activity.orgName + ' · 玩家指标排行' } : {} })
    if (!this.data.activeMetric) {
      const mm = S.metricMap()
      this.setData({ activeMetric: mm['player_damage'] ? 'player_damage' : (S.getState().metrics[0] || {}).id })
    }
    this.renderList()
  },

  renderList() {
    const st = S.getState()
    const mm = S.metricMap()
    const q = this.data.keyword.trim().toLowerCase()
    const set = S.datasetPlayerSet()

    let players = st.players.filter(p => set.has(p.id))
    if (q) {
      players = players.filter(p =>
        (p.name + ' ' + p.role + ' ' + (p.aliases || []).join(' ')).toLowerCase().includes(q)
      )
    }

    let mid = this.data.activeMetric
    if (!mm[mid]) mid = mm['player_damage'] ? 'player_damage' : ((st.metrics[0] || {}).id || '')
    const metric = mm[mid]
    const rows = metric ? players.map(p => {
      const raw = S.getState().dataset.stats[p.id] || {}
      return {
        pid: p.id,
        name: p.name,
        role: p.role,
        value: metricValue(raw, metric),
        text: metric.kind === 'pair'
          ? formatNumber((raw[metric.id] && raw[metric.id].a) || 0) + '/' + formatNumber((raw[metric.id] && raw[metric.id].b) || 0)
          : formatNumber(raw[metric.id])
      }
    }) : []

    rows.sort((a, b) => {
      const va = metricSortValue(a.value, metric)
      const vb = metricSortValue(b.value, metric)
      if (Array.isArray(va)) return (vb[0] - va[0]) || (vb[1] - va[1])
      return vb - va
    })

    const maxVal = rows.length ? Math.max(1, (() => { const v = metricSortValue(rows[0].value, metric); return Array.isArray(v) ? v[0] : v })()) : 1
    const list = rows.map((r, i) => ({
      ...r,
      no: i + 1,
      pct: Math.round(((() => { const v = metricSortValue(r.value, metric); return Array.isArray(v) ? v[0] : v })()) / maxVal * 100)
    }))

    this.setData({
      metrics: st.metrics.map(m => ({ id: m.id, label: m.label })),
      activeMetric: mid,
      list
    })
  },

  onSearch(e) {
    this.setData({ keyword: e.detail.value }, () => this.renderList())
  },

  onPickMetric(e) {
    this.setData({ activeMetric: e.currentTarget.dataset.id }, () => this.renderList())
  },

  onTapPlayer(e) {
    wx.navigateTo({ url: '/pages/player/player?id=' + e.currentTarget.dataset.id })
  },

  goAnalysisSection(e) {
    const route = e.currentTarget.dataset.route
    if (route === 'index') wx.switchTab({ url: '/pages/index/index' })
    else if (route && route !== 'players') wx.redirectTo({ url: '/pages/' + route + '/' + route })
  }
})
