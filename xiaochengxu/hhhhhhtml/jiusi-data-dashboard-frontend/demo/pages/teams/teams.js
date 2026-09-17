const { store: S, formatNumber } = require('../../utils/store')
const { store: Demo } = require('../../utils/demo-store')

Page({
  data: {
    groups: [],
    analysisActivity: {}
  },

  onShow() {
    const demoState = Demo.getState()
    const activity = Demo.getActivity(demoState.selectedAnalysisActivityId) || demoState.activities[0]
    this.setData({ analysisActivity: activity ? { title: activity.title, meta: activity.orgName + ' · 团队战术编制' } : {} })
    this.renderTeams()
  },

  renderTeams() {
    const st = S.getState()
    const pm = S.playerMap()
    const dataSet = S.datasetPlayerSet()

    const keyMetrics = ['kills_spring', 'player_damage', 'healing', 'deaths']
    const mm = S.metricMap()
    const mids = keyMetrics.filter(id => mm[id])

    const groupNames = []
    st.teams.forEach(t => { if (!groupNames.includes(t.group)) groupNames.push(t.group) })

    const groups = groupNames.map(g => {
      const teams = st.teams.filter(t => t.group === g).map(t => {
        const matchedIds = (t.playerIds || []).filter(pid => dataSet.has(pid))
        const agg = S.aggregate(matchedIds, mids)
        const members = (t.playerIds || []).map(pid => ({
          pid,
          name: pm[pid] ? pm[pid].name : '未知',
          role: pm[pid] ? pm[pid].role : '',
          hasData: dataSet.has(pid)
        }))
        return {
          id: t.id,
          name: t.name,
          configuredCount: members.length,
          matchedCount: matchedIds.length,
          memberChips: members.map(m => m.name + '·' + m.role),
          members,
          kills: formatNumber(agg['kills_spring'] && typeof agg['kills_spring'] === 'object'
            ? (agg['kills_spring'].a || 0) + (agg['kills_spring'].b || 0)
            : agg['kills_spring']),
          damage: formatNumber(agg['player_damage'], true),
          healing: formatNumber(agg['healing'], true)
        }
      })
      return { group: g, teams }
    })

    this.setData({ groups })
  },

  onTapMember(e) {
    wx.navigateTo({ url: '/pages/player/player?id=' + e.currentTarget.dataset.id })
  },

  goAnalysisSection(e) {
    const route = e.currentTarget.dataset.route
    if (route === 'index') wx.switchTab({ url: '/pages/index/index' })
    else if (route && route !== 'teams') wx.redirectTo({ url: '/pages/' + route + '/' + route })
  }
})
