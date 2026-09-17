const DemoData = require('../data/demo-app')

const KEY = 'nsh_integrated_frontend_demo_v1'
const store = { state: null }

function clone(value) {
  return DemoData.clone(value)
}

function normalizeState(state) {
  const fallback = DemoData.createDemoData()
  if (!state || typeof state !== 'object') return fallback
  if (!state.session) state.session = { loggedIn: false }
  if (!state.user) state.user = fallback.user
  if (!Array.isArray(state.professions)) state.professions = fallback.professions
  if (!Array.isArray(state.organizations)) state.organizations = fallback.organizations
  if (!Array.isArray(state.activities)) state.activities = fallback.activities
  if (!Array.isArray(state.notices)) state.notices = fallback.notices
  state.activities.forEach(item => {
    if (!Array.isArray(item.seats)) item.seats = DemoData.buildSeats(item.totalSeats || 60, item.filled || 0)
    item.filled = item.seats.filter(seat => seat.status !== 0).length
  })
  return state
}

function createInitialDemoState() {
  return normalizeState(DemoData.createDemoData())
}

function loginState(state, profile) {
  const next = clone(normalizeState(clone(state)))
  const name = String(profile && profile.name || '').trim()
  if (!name) throw new Error('请输入玩家名字')
  next.user.name = name
  next.user.profession = String(profile.profession || next.user.profession || '铁衣')
  next.user.subProfession = String(profile.subProfession || '')
  next.user.hasOrangeWeapon = !!profile.hasOrangeWeapon
  next.session.loggedIn = true
  return next
}

function filterActivities(state, type) {
  const list = normalizeState(clone(state)).activities
  if (type === 'public') return list.filter(item => item.isPublic)
  if (type === 'club') return list.filter(item => item.orgType === 'club' && !item.isPublic)
  if (type === 'history') return list.filter(item => item.status === '已结束')
  return list.filter(item => item.orgType === 'guild' && !item.isPublic)
}

function requireActivity(state, activityId) {
  const activity = state.activities.find(item => item.id === activityId)
  if (!activity) throw new Error('活动不存在')
  return activity
}

function signupSeatState(state, activityId, seatNo, payload) {
  const next = normalizeState(clone(state))
  const activity = requireActivity(next, activityId)
  if (activity.status !== '报名中') throw new Error('活动已经结束')
  const seat = activity.seats.find(item => item.no === Number(seatNo))
  if (!seat) throw new Error('椅子不存在')
  if (seat.status !== 0) throw new Error('这个位置已经有人了')
  const mode = payload && payload.mode === 'PROXY' ? 'PROXY' : 'SELF'
  const name = mode === 'SELF' ? next.user.name : String(payload && payload.name || '').trim()
  if (!name) throw new Error('请输入被代理玩家名字')
  seat.status = 1
  seat.name = name
  seat.profession = String(payload && payload.profession || next.user.profession || '铁衣')
  seat.hasOrangeWeapon = mode === 'SELF' ? !!next.user.hasOrangeWeapon : false
  seat.isProxy = mode === 'PROXY'
  seat.proxyBy = mode === 'PROXY' ? next.user.name : ''
  seat.canVacate = true
  activity.filled = activity.seats.filter(item => item.status !== 0).length
  return next
}

function vacateSeatState(state, activityId, seatNo) {
  const next = normalizeState(clone(state))
  const activity = requireActivity(next, activityId)
  const seat = activity.seats.find(item => item.no === Number(seatNo))
  if (!seat) throw new Error('椅子不存在')
  seat.status = 0
  seat.name = ''
  seat.profession = ''
  seat.hasOrangeWeapon = false
  seat.isProxy = false
  seat.proxyBy = ''
  seat.canVacate = false
  activity.filled = activity.seats.filter(item => item.status !== 0).length
  return next
}

function publishActivityState(state, input) {
  const next = normalizeState(clone(state))
  const title = String(input && input.title || '').trim()
  if (!title) throw new Error('请输入活动名称')
  const totalSeats = Number(input.totalSeats) === 120 ? 120 : 60
  const activity = {
    id: 'act_' + Date.now().toString(36),
    title,
    orgType: input.orgType === 'club' ? 'club' : 'guild',
    orgName: String(input.orgName || '༺九肆✈'),
    isPublic: false,
    publicRemark: '',
    status: '报名中',
    startTime: String(input.startTime || ''),
    endTime: String(input.endTime || ''),
    totalSeats,
    seats: DemoData.buildSeats(totalSeats, 0),
    filled: 0,
    canManage: true,
    csv: null
  }
  next.activities.unshift(activity)
  return next
}

function updateProfileState(state, profile) {
  const next = normalizeState(clone(state))
  next.user.name = String(profile.name || next.user.name).trim() || next.user.name
  next.user.server = String(profile.server || '').trim()
  next.user.profession = String(profile.profession || next.user.profession)
  next.user.subProfession = String(profile.subProfession || '').trim()
  next.user.hasOrangeWeapon = !!profile.hasOrangeWeapon
  return next
}

function joinOrganizationState(state, input) {
  const next = normalizeState(clone(state))
  const code = String(input && input.code || '').trim()
  if (!code) throw new Error('请输入邀请码')
  const type = input.type === 'club' ? 'club' : 'guild'
  const already = next.organizations.some(item => item.type === type && item.inviteCode === code)
  if (already) return next
  next.organizations.push({
    id: 'org_joined_' + Date.now().toString(36),
    type,
    name: type === 'guild' ? '新加入帮会' : '新加入俱乐部',
    role: 0,
    roleText: '成员',
    memberCount: 36,
    limit: type === 'guild' ? 80 : 800,
    inviteCode: code,
    inviteExpire: '2026-09-12 23:59',
    members: [],
    teams: []
  })
  return next
}

function persist() {
  if (typeof wx === 'undefined' || !wx.setStorageSync) return
  wx.setStorageSync(KEY, JSON.stringify(store.state))
}

function commit(next) {
  store.state = normalizeState(next)
  persist()
  return store.state
}

store.load = function () {
  if (store.state) return store.state
  let state = null
  if (typeof wx !== 'undefined' && wx.getStorageSync) {
    try {
      const raw = wx.getStorageSync(KEY)
      if (raw) state = JSON.parse(raw)
    } catch (error) { state = null }
  }
  store.state = normalizeState(state || createInitialDemoState())
  return store.state
}

store.getState = function () { return store.state || store.load() }
store.save = function () { persist(); return true }
store.reset = function () { return commit(createInitialDemoState()) }
store.login = function (profile) { return commit(loginState(store.getState(), profile)) }
store.logout = function () {
  const next = clone(store.getState())
  next.session.loggedIn = false
  return commit(next)
}
store.updateProfile = function (profile) { return commit(updateProfileState(store.getState(), profile)) }
store.filterActivities = function (type) { return filterActivities(store.getState(), type) }
store.getActivity = function (id) { return store.getState().activities.find(item => item.id === id) || null }
store.signupSeat = function (activityId, seatNo, payload) { return commit(signupSeatState(store.getState(), activityId, seatNo, payload)) }
store.vacateSeat = function (activityId, seatNo) { return commit(vacateSeatState(store.getState(), activityId, seatNo)) }
store.publishActivity = function (input) { return commit(publishActivityState(store.getState(), input)) }
store.joinOrganization = function (input) { return commit(joinOrganizationState(store.getState(), input)) }
store.setAnalysisActivity = function (activityId) {
  const next = clone(store.getState())
  next.selectedAnalysisActivityId = activityId
  return commit(next)
}
store.markCsvUploaded = function (activityId) {
  const next = clone(store.getState())
  const activity = requireActivity(next, activityId)
  activity.csv = { fileName: '演示联赛数据.csv', size: 18426, uploadedAt: '2026-09-09 12:00', parsed: true }
  activity.status = '已结束'
  return commit(next)
}

module.exports = {
  KEY,
  store,
  createInitialDemoState,
  loginState,
  filterActivities,
  signupSeatState,
  vacateSeatState,
  publishActivityState,
  updateProfileState,
  joinOrganizationState
}
