const { store: S } = require('../../utils/store')
const { derivePlayerOverrides, buildRoleTree } = require('../../utils/box-selection')

Page({
  data: {
    boxId: '',
    mode: 'full',
    saveLabel: '保存盒子',
    name: '',
    teamGroups: [],
    metricList: [],
    players: [],
    roleGroups: [],
    playerKeyword: '',
    checkedCount: 0,
    manualEditCount: 0
  },

  onLoad(options) {
    const st = S.getState()
    const id = options.id || ''
    const mode = options.mode === 'teams' || options.mode === 'metrics' ? options.mode : 'full'
    const pageTitle = mode === 'teams' ? '编辑队伍与玩家' : (mode === 'metrics' ? '勾选指标' : '编辑盒子')
    wx.setNavigationBarTitle({ title: pageTitle })
    const box = st.boxes.find(b => b.id === id)
    if (!box) {
      wx.showToast({ title: '盒子不存在', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 800)
      return
    }
    this.boxId = id
    this.mode = mode

    this.addedSet = new Set(box.manualAddIds || [])
    this.removedSet = new Set(box.manualRemoveIds || [])
    this.roleExpanded = Object.create(null)

    const effective = new Set(S.effectivePlayerIds(box))
    const set = S.datasetPlayerSet()

    const groupNames = []
    st.teams.forEach(t => { if (!groupNames.includes(t.group)) groupNames.push(t.group) })
    const teamGroups = groupNames.map(g => ({
      group: g,
      teams: st.teams.filter(t => t.group === g).map(t => ({
        id: t.id,
        name: t.name,
        count: (t.playerIds || []).length,
        checked: (box.teamIds || []).includes(t.id)
      }))
    }))

    const metricList = st.metrics.map(m => ({ id: m.id, label: m.label, checked: (box.metricIds || []).includes(m.id) }))

    const players = st.players.filter(p => set.has(p.id)).map(p => ({
      pid: p.id,
      name: p.name,
      role: p.role,
      checked: effective.has(p.id)
    }))
    players.forEach(p => { this.roleExpanded[p.role || '未分类职业'] = true })

    this.setData({
      boxId: id,
      mode,
      saveLabel: mode === 'teams' ? '保存队伍与玩家' : (mode === 'metrics' ? '保存指标' : '保存盒子'),
      name: box.name,
      teamGroups,
      metricList,
      players
    }, () => this.applyPlayerFilter())
  },

  currentBase() {
    const tm = S.teamMap()
    const dataSet = S.datasetPlayerSet()
    const out = []
    this.data.teamGroups.forEach(g => g.teams.forEach(t => {
      if (!t.checked) return
      const tt = tm[t.id]
      if (!tt) return
      tt.playerIds.forEach(pid => {
        if (dataSet.has(pid) && !out.includes(pid)) out.push(pid)
      })
    }))
    return out
  },

  applyPlayerFilter() {
    const roleGroups = buildRoleTree(this.data.players, this.data.playerKeyword, this.roleExpanded)
    const checkedIds = this.data.players.filter(p => p.checked).map(p => p.pid)
    const overrides = derivePlayerOverrides(this.currentBase(), checkedIds)
    const manualEditCount = overrides.manualAddIds.length + overrides.manualRemoveIds.length
    this.setData({ roleGroups, checkedCount: checkedIds.length, manualEditCount })
  },

  onNameInput(e) { this.setData({ name: e.detail.value }) },

  onSearchPlayer(e) {
    const keyword = e.detail.value
    if (String(keyword || '').trim()) {
      buildRoleTree(this.data.players, keyword, this.roleExpanded).forEach(group => {
        this.roleExpanded[group.role] = true
      })
    }
    this.setData({ playerKeyword: keyword }, () => this.applyPlayerFilter())
  },

  onToggleRole(e) {
    const role = e.currentTarget.dataset.role
    if (!role) return
    this.roleExpanded[role] = !(this.roleExpanded[role] !== false)
    this.applyPlayerFilter()
  },

  onToggleTeam(e) {
    const { gid, tid } = e.currentTarget.dataset
    const cur = this.data.teamGroups[gid].teams[tid].checked
    this.setData({ ['teamGroups[' + gid + '].teams[' + tid + '].checked']: !cur }, () => {
      const base = new Set(this.currentBase())
      const players = this.data.players.map(p => ({
        ...p,
        checked: base.has(p.pid) ? !this.removedSet.has(p.pid) : this.addedSet.has(p.pid)
      }))
      this.setData({ players }, () => this.applyPlayerFilter())
    })
  },

  onToggleMetric(e) {
    const idx = e.currentTarget.dataset.idx
    const key = 'metricList[' + idx + '].checked'
    this.setData({ [key]: !this.data.metricList[idx].checked })
  },

  metricAll() { this.setAllMetrics(true) },
  metricNone() { this.setAllMetrics(false) },
  setAllMetrics(val) {
    const metricList = this.data.metricList.map(m => ({ ...m, checked: val }))
    this.setData({ metricList })
  },

  onTogglePlayer(e) {
    const pid = e.currentTarget.dataset.pid
    const idx = this.data.players.findIndex(p => p.pid === pid)
    if (idx < 0) return
    const next = !this.data.players[idx].checked
    const base = new Set(this.currentBase())

    if (next) {
      if (base.has(pid)) this.removedSet.delete(pid)
      else this.addedSet.add(pid)
    } else {
      if (base.has(pid)) { this.removedSet.add(pid); this.addedSet.delete(pid) }
      else this.addedSet.delete(pid)
    }

    this.setData({ ['players[' + idx + '].checked']: next }, () => this.applyPlayerFilter())
  },

  checkVisibleAll() { this.setVisibleAll(true) },
  uncheckVisibleAll() { this.setVisibleAll(false) },
  resetPlayersToTeams() {
    this.addedSet.clear()
    this.removedSet.clear()
    const base = new Set(this.currentBase())
    const players = this.data.players.map(p => ({ ...p, checked: base.has(p.pid) }))
    this.setData({ players }, () => this.applyPlayerFilter())
  },
  setVisibleAll(checked) {
    const q = this.data.playerKeyword.trim().toLowerCase()
    const base = new Set(this.currentBase())
    const updates = {}
    this.data.players.forEach((p, i) => {
      const visible = !q || (p.name + ' ' + p.role).toLowerCase().includes(q)
      if (!visible || p.checked === checked) return
      if (checked) {
        if (base.has(p.pid)) this.removedSet.delete(p.pid)
        else this.addedSet.add(p.pid)
      } else {
        if (base.has(p.pid)) this.removedSet.add(p.pid)
        else this.addedSet.delete(p.pid)
      }
      updates['players[' + i + '].checked'] = checked
    })
    this.setData(updates, () => this.applyPlayerFilter())
  },

  save() {
    const st = S.getState()
    const box = st.boxes.find(b => b.id === this.data.boxId)
    if (!box) return

    if (this.mode === 'teams') {
      box.teamIds = []
      this.data.teamGroups.forEach(g => g.teams.forEach(t => { if (t.checked) box.teamIds.push(t.id) }))
      const overrides = derivePlayerOverrides(
        this.currentBase(),
        this.data.players.filter(p => p.checked).map(p => p.pid)
      )
      box.manualAddIds = overrides.manualAddIds
      box.manualRemoveIds = overrides.manualRemoveIds
    } else if (this.mode === 'metrics') {
      box.metricIds = this.data.metricList.filter(m => m.checked).map(m => m.id)
    } else {
      box.name = this.data.name.trim() || box.name
      box.teamIds = []
      this.data.teamGroups.forEach(g => g.teams.forEach(t => { if (t.checked) box.teamIds.push(t.id) }))
      box.metricIds = this.data.metricList.filter(m => m.checked).map(m => m.id)

      const checkedPids = this.data.players.filter(p => p.checked).map(p => p.pid)
      const overrides = derivePlayerOverrides(this.currentBase(), checkedPids)
      box.manualAddIds = overrides.manualAddIds
      box.manualRemoveIds = overrides.manualRemoveIds
    }

    S.save()
    wx.showToast({ title: '已保存', icon: 'success' })
    setTimeout(() => wx.navigateBack(), 400)
  }
})
