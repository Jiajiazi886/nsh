const { store: S, formatMetric } = require('../../utils/store')

Page({
  data: {
    player: null,
    teamText: '',
    statRows: []
  },

  onLoad(options) {
    const st = S.getState()
    const pm = S.playerMap()
    const p = pm[options.id]
    if (!p) {
      wx.showToast({ title: '未找到该玩家', icon: 'none' })
      return
    }

    const teams = st.teams.filter(t => (t.playerIds || []).includes(p.id))
    const teamText = teams.map(t => t.group + ' · ' + t.name).join('、') || '未编队'

    const raw = st.dataset.stats[p.id] || {}
    const maxOf = mid => {
      let max = 0
      st.dataset.playerIds.forEach(pid => {
        const v = (st.dataset.stats[pid] || {})[mid]
        const n = typeof v === 'object' && v !== null ? (v.a || 0) + (v.b || 0) : Number(v) || 0
        if (n > max) max = n
      })
      return max || 1
    }

    const statRows = st.metrics.map(m => {
      const v = raw[m.id]
      const num = typeof v === 'object' && v !== null ? (v.a || 0) + (v.b || 0) : Number(v) || 0
      return {
        id: m.id,
        label: m.label,
        text: formatMetric(v, m, false),
        pct: Math.round(num / maxOf(m.id) * 100)
      }
    })

    this.setData({ player: p, teamText, statRows })
  },

  copyName() {
    if (!this.data.player) return
    wx.setClipboardData({ data: this.data.player.name })
  }
})
