const { store: S, formatNumber, formatMetric, metricValue, metricSortValue } = require('../../utils/store')
const { store: Demo } = require('../../utils/demo-store')

Page({
  data: {
    datasetName: '',
    playerCount: 0,
    teamCount: 0,
    groupCards: [],
    compareMetrics: [],
    rankMetrics: [],
    activeRankMetric: '',
    rankList: [],
    updatedText: '',
    analysisActivity: {}
  },

  onShow() {
    this.renderAll()
  },

  renderAll() {
    const st = S.getState()
    const demoState = Demo.getState()
    const selectedActivity = Demo.getActivity(demoState.selectedAnalysisActivityId) || demoState.activities.find(item => item.csv) || demoState.activities[0]
    const dataSet = S.datasetPlayerSet()

    const groups = []
    st.teams.forEach(t => {
      if (!groups.includes(t.group)) groups.push(t.group)
    })

    const compareIds = ['kills_spring', 'assists', 'player_damage', 'healing', 'damage_taken', 'deaths']
    const mm = S.metricMap()
    const compareMetrics = compareIds.filter(id => mm[id])

    const groupRows = groups.map(g => {
      const pids = []
      st.teams.filter(t => t.group === g).forEach(t => {
        t.playerIds.forEach(pid => { if (dataSet.has(pid) && !pids.includes(pid)) pids.push(pid) })
      })
      const agg = S.aggregate(pids, compareMetrics)
      return { group: g, count: pids.length, values: agg }
    })

    const groupCards = groupRows.map(r => ({
      group: r.group,
      count: r.count,
      kills: mm['kills_spring'] ? formatMetric(r.values['kills_spring'], mm['kills_spring'], true) : '—',
      damage: mm['player_damage'] ? formatNumber(r.values['player_damage'], true) : '—',
      healing: mm['healing'] ? formatNumber(r.values['healing'], true) : '—',
      assists: mm['assists'] ? formatNumber(r.values['assists']) : '—'
    }))

    const maxOf = mid => Math.max.apply(null, [1].concat(groupRows.map(r => {
      const m = mm[mid]
      const v = metricSortValue(r.values[mid], m)
      return Array.isArray(v) ? v[0] : v
    })))

    const compareBars = compareMetrics.map(mid => {
      const m = mm[mid]
      const max = maxOf(mid)
      return {
        id: mid,
        label: m.label,
        kind: m.kind,
        rows: groupRows.map((r, idx) => {
          const raw = metricSortValue(r.values[mid], m)
          const num = Array.isArray(raw) ? raw[0] : raw
          return {
            group: r.group,
            text: formatMetric(r.values[mid], m, false),
            pct: Math.round(num / max * 100),
            first: idx === 0
          }
        })
      }
    })

    const rankMetrics = st.metrics.map(m => ({ id: m.id, label: m.label }))
    let active = this.data.activeRankMetric
    if (!mm[active]) active = mm['player_damage'] ? 'player_damage' : ((st.metrics[0] || {}).id || '')

    const set = S.datasetPlayerSet()
    const players = st.players.filter(p => set.has(p.id))
    const metric = mm[active]
    const ranked = metric
      ? players.map(p => ({ pid: p.id, name: p.name, role: p.role, value: metricValue(st.dataset.stats[p.id], metric) }))
      : []
    ranked.sort((a, b) => {
      const va = metricSortValue(a.value, metric)
      const vb = metricSortValue(b.value, metric)
      if (Array.isArray(va)) return (vb[0] - va[0]) || (vb[1] - va[1])
      return vb - va
    })
    const maxVal = (() => {
      if (!ranked.length) return 1
      const v = metricSortValue(ranked[0].value, metric)
      const n = Array.isArray(v) ? v[0] : v
      return n || 1
    })()

    const rankList = ranked.slice(0, 10).map((r, i) => ({
      pid: r.pid,
      no: i + 1,
      name: r.name,
      role: r.role,
      text: formatMetric(r.value, metric, false),
      pct: Math.round((Array.isArray(metricSortValue(r.value, metric)) ? metricSortValue(r.value, metric)[0] : Number(metricSortValue(r.value, metric))) / maxVal * 100)
    }))

    this.setData({
      datasetName: st.dataset.name,
      playerCount: st.dataset.playerIds.length,
      teamCount: st.teams.length,
      groupCards,
      compareBars,
      rankMetrics,
      activeRankMetric: active,
      rankList,
      analysisActivity: selectedActivity ? {
        title: selectedActivity.title,
        meta: selectedActivity.orgName + ' · ' + String(selectedActivity.startTime || '').slice(0, 10) + ' · 已归档'
      } : { title: '演示联赛数据', meta: '纯前端假数据' }
    })
  },

  onTapGroupBar(e) {
    // 预留交互
  },

  onPickRankMetric(e) {
    const id = e.currentTarget.dataset.id
    this.setData({ activeRankMetric: id }, () => this.renderAll())
  },

  onTapPlayer(e) {
    wx.navigateTo({ url: '/pages/player/player?id=' + e.currentTarget.dataset.id })
  },

  goBoxes() {
    wx.navigateTo({ url: '/pages/boxes/boxes' })
  },

  goAnalysisSection(e) {
    const route = e.currentTarget.dataset.route
    if (!route || route === 'index') return
    wx.navigateTo({ url: '/pages/' + route + '/' + route })
  }
})
