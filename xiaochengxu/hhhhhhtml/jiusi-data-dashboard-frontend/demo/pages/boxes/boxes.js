const { store: S, uid, formatMetric, metricValue, metricSortValue } = require('../../utils/store')
const { store: Demo } = require('../../utils/demo-store')

const DEFAULT_VIEW = 'teams'
const METRIC_COLORS = [
  'rgba(124, 92, 255, 0.45)', 'rgba(32, 201, 151, 0.45)', 'rgba(78, 140, 255, 0.45)',
  'rgba(247, 185, 85, 0.45)', 'rgba(255, 93, 115, 0.45)', 'rgba(123, 216, 143, 0.45)',
  'rgba(56, 189, 248, 0.45)', 'rgba(217, 70, 239, 0.45)', 'rgba(251, 146, 60, 0.45)',
  'rgba(167, 139, 250, 0.45)', 'rgba(45, 212, 191, 0.45)', 'rgba(244, 114, 182, 0.45)'
]

function compareTableValue(left, right, metric, direction) {
  const a = metric ? metricSortValue(left, metric) : left
  const b = metric ? metricSortValue(right, metric) : right
  let result = 0
  if (Array.isArray(a) || Array.isArray(b)) {
    const av = Array.isArray(a) ? a : [Number(a) || 0, 0]
    const bv = Array.isArray(b) ? b : [Number(b) || 0, 0]
    result = (av[0] - bv[0]) || (av[1] - bv[1])
  } else if (typeof a === 'number' && typeof b === 'number') {
    result = a - b
  } else {
    result = String(a == null ? '' : a).localeCompare(String(b == null ? '' : b), 'zh-CN', {
      numeric: true,
      sensitivity: 'base'
    })
  }
  return direction === 'asc' ? result : -result
}

function textWidthRpx(value, fontSize) {
  return Array.from(String(value == null ? '' : value)).reduce((width, char) => {
    if (/\s/.test(char)) return width + fontSize * 0.35
    return width + (/[^\x00-\xff]/.test(char) ? fontSize : fontSize * 0.58)
  }, 0)
}

function columnWidthRpx(label, values, fontSize, maxWidth) {
  const headerWidth = textWidthRpx(label, 19) + 54
  const contentWidth = (values || []).reduce((width, value) => {
    return Math.max(width, textWidthRpx(value, fontSize) + 30)
  }, 0)
  return Math.ceil(Math.min(maxWidth || 360, Math.max(headerWidth, contentWidth)))
}

function buildTable(box, ids, mids, metricMap, teamMap, playerMap, state) {
  const view = box.view === 'players' ? 'players' : 'teams'
  const firstKey = view === 'teams' ? 'team' : 'player'
  const secondKey = view === 'teams' ? 'count' : 'role'
  const activeSort = box.tableSort && box.tableSort.view === view ? box.tableSort : null
  let rows = []

  if (view === 'players') {
    rows = ids.map(pid => {
      const player = playerMap[pid]
      const values = {}
      mids.forEach(mid => { values[mid] = metricValue(state.dataset.stats[pid], metricMap[mid]) })
      return {
        id: pid,
        first: player ? player.name : '未知玩家',
        firstSub: '',
        second: player ? player.role : '未知',
        values
      }
    })
  } else {
    rows = (box.teamIds || []).map(teamId => {
      const team = teamMap[teamId]
      if (!team) return null
      const playerIds = (team.playerIds || []).filter(pid => ids.includes(pid))
      return {
        id: team.id,
        first: team.group + team.name,
        firstSub: '',
        second: playerIds.length,
        values: S.aggregate(playerIds, mids)
      }
    }).filter(Boolean)

    const extras = (box.manualAddIds || []).filter(pid => {
      if (!ids.includes(pid)) return false
      return !(box.teamIds || []).some(teamId => (teamMap[teamId] && teamMap[teamId].playerIds || []).includes(pid))
    })
    if (extras.length) {
      rows.push({
        id: '__extra__',
        first: '额外玩家',
        firstSub: '',
        second: extras.length,
        values: S.aggregate(extras, mids)
      })
    }
  }

  if (activeSort) {
    rows.sort((left, right) => {
      if (activeSort.key === firstKey) return compareTableValue(left.first, right.first, null, activeSort.dir)
      if (activeSort.key === secondKey) return compareTableValue(left.second, right.second, null, activeSort.dir)
      if (activeSort.key.indexOf('metric:') === 0) {
        const mid = activeSort.key.slice(7)
        return compareTableValue(left.values[mid], right.values[mid], metricMap[mid], activeSort.dir)
      }
      return 0
    })
  }

  const header = (key, label) => ({
    key,
    label,
    active: !!(activeSort && activeSort.key === key),
    arrow: activeSort && activeSort.key === key ? (activeSort.dir === 'asc' ? '▲' : '▼') : '↕'
  })

  const formattedRows = rows.map(row => ({
    ...row,
    cells: mids.map(mid => ({ id: mid, text: formatMetric(row.values[mid], metricMap[mid], false) }))
  }))
  const firstLabel = view === 'teams' ? '队伍' : '玩家'
  const secondLabel = view === 'teams' ? '人数' : '职业'
  const firstWidth = columnWidthRpx(firstLabel, formattedRows.map(row => row.first), 22, 360)
  const secondWidth = columnWidthRpx(secondLabel, formattedRows.map(row => row.second), 21, 220)
  const metricWidths = mids.map((mid, index) => columnWidthRpx(
    metricMap[mid].label,
    formattedRows.map(row => row.cells[index].text),
    21,
    360
  ))

  return {
    view,
    width: firstWidth + secondWidth + metricWidths.reduce((sum, width) => sum + width, 0),
    height: Math.min(580, Math.max(150, 62 + rows.length * 62)),
    firstWidth,
    secondWidth,
    firstHeader: header(firstKey, firstLabel),
    secondHeader: header(secondKey, secondLabel),
    metricHeaders: mids.map((mid, index) => ({
      ...header('metric:' + mid, metricMap[mid].label),
      width: metricWidths[index]
    })),
    rows: formattedRows.map(row => ({
      ...row,
      cells: row.cells.map((cell, index) => ({ ...cell, width: metricWidths[index] }))
    }))
  }
}

function buildBoxModel(box) {
  const st = S.getState()
  const mm = S.metricMap()
  const tm = S.teamMap()
  const pm = S.playerMap()
  const ids = S.effectivePlayerIds(box)
  const mids = (box.metricIds || []).filter(id => mm[id] && mm[id].id !== 'resource')
  const agg = S.aggregate(ids, mids)

  const statCards = mids.map(mid => {
    const metricIndex = st.metrics.findIndex(metric => metric.id === mid)
    return {
      id: mid,
      label: mm[mid].label,
      text: formatMetric(agg[mid], mm[mid], true),
      color: METRIC_COLORS[(metricIndex < 0 ? 0 : metricIndex) % METRIC_COLORS.length]
    }
  })

  return { ids, statCards, table: buildTable(box, ids, mids, mm, tm, pm, st) }
}

Page({
  data: {
    boxes: [],
    summary: {},
    lastReport: null,
    importing: false,
    sampleExpanded: false,
    sampleText: '',
    analysisActivity: {}
  },

  onShow() {
    const demoState = Demo.getState()
    const activity = Demo.getActivity(demoState.selectedAnalysisActivityId) || demoState.activities[0]
    this.setData({ analysisActivity: activity ? { title: activity.title, meta: activity.orgName + ' · 自定义复盘盒子' } : {} })
    this.renderBoxes()
  },

  renderBoxes() {
    const st = S.getState()
    const tm = S.teamMap()
    const pm = S.playerMap()

    const boxes = st.boxes.map((b, idx) => {
      let built = { ids: [], statCards: [], table: null }
      try {
        built = buildBoxModel(b)
      } catch (e) {
        built = { ids: [], statCards: [], table: null }
      }
      return {
        ...b,
        count: built.ids.length,
        teamChips: (b.teamIds || []).map(id => tm[id] ? tm[id].group + ' · ' + tm[id].name : '').filter(Boolean),
        playerChips: built.ids.slice(0, 12).map(pid => (pm[pid] ? pm[pid].name : '未知')),
        extraCount: Math.max(0, built.ids.length - 12),
        statCards: built.statCards,
        view: built.table ? built.table.view : DEFAULT_VIEW,
        table: built.table,
        _i: idx
      }
    })

    this.setData({
      boxes,
      summary: S.matchSummary(),
      lastReport: st.lastImportReport || null
    })
  },

  pickTextFile(extension, maxBytes, onText) {
    if (this.data.importing) return
    this.setData({ importing: true })
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: [extension],
      success: res => {
        const file = res.tempFiles && res.tempFiles[0]
        if (!file) {
          this.setData({ importing: false })
          return
        }
        const name = file.name || ('导入文件.' + extension)
        if (file.size && file.size > maxBytes) {
          this.setData({ importing: false })
          this.showImportError('文件过大，请选择小于 ' + Math.round(maxBytes / 1024 / 1024) + 'MB 的文件')
          return
        }
        const filePath = file.path || file.tempFilePath
        wx.getFileSystemManager().readFile({
          filePath,
          encoding: 'utf8',
          success: readRes => {
            this.setData({ importing: false })
            onText(String(readRes.data || ''), name)
          },
          fail: error => {
            this.setData({ importing: false })
            this.showImportError('无法读取“' + name + '”：' + (error.errMsg || '未知错误'))
          }
        })
      },
      fail: error => {
        this.setData({ importing: false })
        if (!String(error.errMsg || '').includes('cancel')) {
          this.showImportError(error.errMsg || '没有选择文件')
        }
      }
    })
  },

  importTeamConfig() {
    this.pickTextFile('json', 1024 * 1024, (text, name) => {
      let preview
      try {
        preview = S.previewTeamConfig(text)
      } catch (error) {
        this.showImportError(error.message)
        return
      }
      wx.showModal({
        title: '应用团队配置',
        content: '识别到 ' + preview.groupCount + ' 个团、' + preview.teamCount + ' 支队伍、' + preview.playerCount + ' 名玩家。导入会删除旧盒子并重建“全部队员”，是否继续？',
        confirmText: '导入',
        confirmColor: '#7c5cff',
        success: res => {
          if (!res.confirm) return
          try {
            S.importTeamConfig(text, name)
            this.renderBoxes()
            wx.showToast({ title: '团队已导入', icon: 'success' })
          } catch (error) {
            this.showImportError(error.message)
          }
        }
      })
    })
  },

  importCsv() {
    this.pickTextFile('csv', 5 * 1024 * 1024, (text, name) => {
      try {
        const report = S.importCsv(text, name)
        this.renderBoxes()
        wx.showToast({ title: report.tone === 'warning' ? '已导入，请看报告' : '数据已导入', icon: 'none' })
      } catch (error) {
        this.showImportError(error.message)
      }
    })
  },

  showImportError(message) {
    wx.showModal({
      title: '导入失败',
      content: String(message || '文件无法处理'),
      showCancel: false,
      confirmColor: '#7c5cff'
    })
  },

  toggleSample() {
    const expanded = !this.data.sampleExpanded
    this.setData({
      sampleExpanded: expanded,
      sampleText: expanded && !this.data.sampleText
        ? JSON.stringify(S.getSampleTeamConfig(), null, 2)
        : this.data.sampleText
    })
  },

  copySample() {
    const text = this.data.sampleText || JSON.stringify(S.getSampleTeamConfig(), null, 2)
    wx.setClipboardData({ data: text })
  },

  createBox() {
    const st = S.getState()
    const n = st.boxes.length + 1
    st.boxes.push({
      id: uid('box'),
      name: '分析盒子 ' + n,
      teamIds: st.teams.slice(0, 2).map(team => team.id),
      manualAddIds: [],
      manualRemoveIds: [],
      metricIds: st.metrics.filter(m => m.label !== '资源').map(m => m.id),
      view: DEFAULT_VIEW,
      tableSort: null,
      sortMetricId: 'player_damage',
      collapsed: false,
      tableCollapsed: false
    })
    S.save()
    this.renderBoxes()
    wx.showToast({ title: '已创建', icon: 'success' })
  },

  renameBox(e) {
    const id = e.currentTarget.dataset.id
    const box = S.getState().boxes.find(b => b.id === id)
    if (!box) return
    wx.showModal({
      title: '重命名盒子',
      editable: true,
      placeholderText: box.name,
      success: res => {
        if (res.confirm && res.content && res.content.trim()) {
          box.name = res.content.trim()
          S.save()
          this.renderBoxes()
        }
      }
    })
  },

  delBox(e) {
    const id = e.currentTarget.dataset.id
    const box = S.getState().boxes.find(item => item.id === id)
    wx.showModal({
      title: '删除盒子',
      content: '确定删除「' + (box ? box.name : '这个分析盒子') + '」？',
      confirmColor: '#ff5d73',
      success: res => {
        if (!res.confirm) return
        const st = S.getState()
        st.boxes = st.boxes.filter(x => x.id !== id)
        S.save()
        this.renderBoxes()
      }
    })
  },

  toggleCollapse(e) {
    const id = e.currentTarget.dataset.id
    const box = S.getState().boxes.find(b => b.id === id)
    if (!box) return
    box.collapsed = !box.collapsed
    S.save()
    this.renderBoxes()
  },

  toggleTableCollapse(e) {
    const id = e.currentTarget.dataset.id
    const box = S.getState().boxes.find(item => item.id === id)
    if (!box) return
    box.tableCollapsed = !box.tableCollapsed
    S.save()
    this.renderBoxes()
  },

  editTeams(e) {
    wx.navigateTo({ url: '/pages/box-edit/box-edit?mode=teams&id=' + e.currentTarget.dataset.id })
  },

  editStats(e) {
    wx.navigateTo({ url: '/pages/box-edit/box-edit?mode=metrics&id=' + e.currentTarget.dataset.id })
  },

  setBoxView(e) {
    const id = e.currentTarget.dataset.id
    const view = e.currentTarget.dataset.view === 'players' ? 'players' : 'teams'
    const box = S.getState().boxes.find(item => item.id === id)
    if (!box || box.view === view) return
    box.view = view
    S.save()
    this.renderBoxes()
  },

  sortBoxTable(e) {
    const id = e.currentTarget.dataset.id
    const key = String(e.currentTarget.dataset.key || '')
    const box = S.getState().boxes.find(item => item.id === id)
    if (!box || !key) return
    const view = box.view === 'players' ? 'players' : 'teams'
    const current = box.tableSort && box.tableSort.view === view && box.tableSort.key === key
      ? box.tableSort
      : null
    const textKey = key === 'player' || key === 'role' || key === 'team'
    box.tableSort = {
      view,
      key,
      dir: current ? (current.dir === 'asc' ? 'desc' : 'asc') : (textKey ? 'asc' : 'desc')
    }
    S.save()
    this.renderBoxes()
  },

  goAnalysisSection(e) {
    const route = e.currentTarget.dataset.route
    if (route === 'index') wx.switchTab({ url: '/pages/index/index' })
    else if (route && route !== 'boxes') wx.redirectTo({ url: '/pages/' + route + '/' + route })
  },

  resetAll() {
    wx.showModal({
      title: '恢复默认',
      content: '恢复默认九肆数据、默认队伍和默认盒子？本地修改会被清空。',
      confirmColor: '#ff5d73',
      success: res => {
        if (!res.confirm) return
        S.reset()
        this.renderBoxes()
        wx.showToast({ title: '已恢复默认', icon: 'success' })
      }
    })
  }
})
