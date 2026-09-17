const test = require('node:test')
const assert = require('node:assert/strict')

const {
  createInitialDemoState,
  loginState,
  filterActivities,
  signupSeatState,
  vacateSeatState,
  publishActivityState
} = require('../utils/demo-store')

test('初始 Demo 覆盖组织、活动和 60 人椅子数据', () => {
  const state = createInitialDemoState()
  assert.equal(state.organizations.length >= 2, true)
  assert.equal(state.activities.length >= 3, true)
  const league = state.activities.find(item => item.totalSeats === 60)
  assert.ok(league)
  assert.equal(league.seats.length, 60)
  assert.equal(league.filled, league.seats.filter(item => item.status !== 0).length)
})

test('登录资料写入纯前端状态', () => {
  const state = createInitialDemoState()
  const next = loginState(state, {
    name: '测试指挥',
    profession: '铁衣',
    subProfession: '素问',
    hasOrangeWeapon: true
  })
  assert.equal(next.session.loggedIn, true)
  assert.equal(next.user.name, '测试指挥')
  assert.equal(next.user.profession, '铁衣')
  assert.equal(next.user.hasOrangeWeapon, true)
})

test('活动可以按帮会、俱乐部和公开分类筛选', () => {
  const state = createInitialDemoState()
  assert.ok(filterActivities(state, 'guild').every(item => item.orgType === 'guild'))
  assert.ok(filterActivities(state, 'club').every(item => item.orgType === 'club'))
  assert.ok(filterActivities(state, 'public').every(item => item.isPublic))
})

test('空椅子支持代理报名并可撤离', () => {
  const state = createInitialDemoState()
  const activity = state.activities[0]
  const emptySeat = activity.seats.find(item => item.status === 0)
  const before = activity.filled

  const signed = signupSeatState(state, activity.id, emptySeat.no, {
    mode: 'PROXY',
    name: '代报名玩家',
    profession: '神相'
  })
  const signedActivity = signed.activities.find(item => item.id === activity.id)
  const signedSeat = signedActivity.seats.find(item => item.no === emptySeat.no)
  assert.equal(signedSeat.status, 1)
  assert.equal(signedSeat.isProxy, true)
  assert.equal(signedActivity.filled, before + 1)

  const vacated = vacateSeatState(signed, activity.id, emptySeat.no)
  const vacatedActivity = vacated.activities.find(item => item.id === activity.id)
  assert.equal(vacatedActivity.seats.find(item => item.no === emptySeat.no).status, 0)
  assert.equal(vacatedActivity.filled, before)
})

test('发布活动会生成对应数量的空椅子', () => {
  const state = createInitialDemoState()
  const next = publishActivityState(state, {
    title: '新建120人演练',
    orgType: 'club',
    orgName: '九肆联赛训练营',
    totalSeats: 120,
    startTime: '2026-09-12 19:00',
    endTime: '2026-09-12 21:00'
  })
  const activity = next.activities[0]
  assert.equal(activity.title, '新建120人演练')
  assert.equal(activity.seats.length, 120)
  assert.equal(activity.filled, 0)
})
