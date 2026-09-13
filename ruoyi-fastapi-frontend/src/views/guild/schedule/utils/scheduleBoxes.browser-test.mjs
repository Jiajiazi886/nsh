// Isolated headless UI regression: every API request is mocked; no real DB writes.
// PLAYWRIGHT_MODULE_PATH can point to a bundled playwright/index.js.
import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import { pathToFileURL } from 'node:url'
const require = createRequire(import.meta.url)
const playwrightPath = process.env.PLAYWRIGHT_MODULE_PATH || require.resolve('playwright')
const playwrightModule = await import(pathToFileURL(playwrightPath).href)
const { chromium } = playwrightModule.default || playwrightModule
const clone = value => JSON.parse(JSON.stringify(value))
const members = [
  { member_id: 7, player_name: '测试铁衣', player_class: '铁衣', secondary_class: '' },
  { member_id: 8, player_name: '测试素问', player_class: '素问', secondary_class: '' },
  { member_id: 9, player_name: '测试神相', player_class: '神相', secondary_class: '' }
]
let schedule = { schedule_id: 1, teams: [] }
let workbook = { custom: { keepMe: '旧数据保留' }, sheets: { oldSheet: { name: '旧表', cellData: { 1: { 1: { v: '测试神相', custom: { ...members[2] } } } } } } }
let nextTeam = 10, nextSquad = 20, nextHistory = 100
const histories = []
const requests = []
let failWorkbookSave = false
const errors = []
const browser = await chromium.launch({ headless: true, channel: process.env.SCHEDULE_BROWSER_CHANNEL || undefined })
const context = await browser.newContext({ viewport: { width: 1280, height: 900 } })
await context.addCookies([{ name: 'Admin-Token', value: 'isolated-mock-only', url: 'http://127.0.0.1' }])
const page = await context.newPage()
page.on('pageerror', error => errors.push(error.message))
const reply = (route, data = {}) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ code: 200, msg: 'mock', ...data }) })
await page.route('**/*', async route => {
  const req = route.request(), url = new URL(req.url())
  if (url.hostname !== '127.0.0.1' && url.hostname !== 'localhost') return route.abort()
  if (!url.pathname.startsWith('/dev-api/')) return route.continue()
  const path = url.pathname.slice('/dev-api'.length), method = req.method()
  const body = req.postData() ? JSON.parse(req.postData()) : {}
  requests.push({ path, method, body })
  // No request in this branch falls through to the real backend.
  if (path === '/getInfo') return reply(route, { user: { userId: 999999, userName: '隔离测试', nickName: '隔离测试' }, roles: ['admin'], permissions: ['*:*:*'] })
  if (path === '/getRouters') return reply(route, { data: [{ path: '/guild', name: 'Guild', component: 'Layout', meta: { title: '帮会管理' }, children: [{ path: 'group', name: 'Group', component: 'ParentView', meta: { title: '分团管理' }, children: [{ path: 'schedule', name: 'Schedule', component: 'guild/schedule/index', meta: { title: '约战排表' } }] }] }] })
  if (path === '/transport/crypto/frontend-config') return reply(route, { data: { enabled: false, mode: 'off', policy: {} } })
  if (path === '/guild/member/list') return reply(route, { data: members })
  if (path === '/guild/class-color/list') return reply(route, { data: [] })
  if (path.endsWith('/approved-schedule-list')) return reply(route, { data: members.map(member => ({ member_id: member.member_id })) })
  if (path.endsWith('/leave-schedule-list')) return reply(route, { data: [] })
  if (path === '/guild/schedule/current') return reply(route, { data: schedule })
  if (path === '/guild/schedule/current/workbook') {
    if (method === 'PUT') {
      if (failWorkbookSave) return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ code: 500, msg: '模拟保存失败' }) })
      workbook = clone(body.workbook)
    }
    return reply(route, { data: { schedule_id: 1, workbook } })
  }
  if (path === '/guild/schedule/team' && method === 'POST') {
    schedule.teams.push({ team_id: nextTeam++, team_name: body.team_name, order_num: schedule.teams.length + 1, squads: [] })
    return reply(route)
  }
  const squadCreate = path.match(/^\/guild\/schedule\/team\/(\d+)\/squad$/)
  if (squadCreate && method === 'POST') {
    const team = schedule.teams.find(team => team.team_id === Number(squadCreate[1]))
    team.squads.push({ squad_id: nextSquad++, squad_name: body.squad_name, max_members: 6, order_num: team.squads.length + 1, members: [] })
    return reply(route)
  }
  const squadDelete = path.match(/^\/guild\/schedule\/team\/(\d+)\/squad\/(\d+)$/)
  if (squadDelete && method === 'DELETE') { const team = schedule.teams.find(team => team.team_id === Number(squadDelete[1])); team.squads = team.squads.filter(squad => squad.squad_id !== Number(squadDelete[2])); return reply(route) }
  const teamDelete = path.match(/^\/guild\/schedule\/team\/(\d+)$/)
  if (teamDelete && method === 'DELETE') { schedule.teams = schedule.teams.filter(team => team.team_id !== Number(teamDelete[1])); return reply(route) }
  const squadBulk = path.match(/^\/guild\/schedule\/region\/squad\/(\d+)\/assignments$/)
  if (squadBulk && method === 'PUT') {
    const id = Number(squadBulk[1]), ids = new Set(body.members.map(member => member.member_id))
    const squads = schedule.teams.flatMap(team => team.squads)
    assert.ok(body.members.every(member => Number.isInteger(member.member_id)), '临时 ID 不能写正式分配接口')
    squads.forEach(squad => { squad.members = squad.squad_id === id ? [] : squad.members.filter(member => !ids.has(member.member_id)) })
    squads.find(squad => squad.squad_id === id).members = body.members.map(member => ({ ...members.find(m => m.member_id === member.member_id), order_num: member.order_num }))
    return reply(route)
  }
  const squadResize = path.match(/^\/guild\/schedule\/region\/squad\/(\d+)$/)
  if (squadResize && method === 'PUT') { Object.assign(schedule.teams.flatMap(t => t.squads).find(s => s.squad_id === Number(squadResize[1])), body); return reply(route) }
  if (path === '/guild/schedule/assignment' && method === 'PUT') {
    const squad = schedule.teams.flatMap(team => team.squads).find(squad => squad.squad_id === body.squad_id)
    const oldSquad = schedule.teams.flatMap(team => team.squads).find(squad => squad.members.some(member => member.member_id === body.member_id))
    const previous = oldSquad?.members.find(member => member.member_id === body.member_id)
    const target = squad.members.find(member => member.order_num === body.order_num)
    if (target && !previous) return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ code: 500, msg: '目标位置已有成员' }) })
    if (oldSquad) oldSquad.members = oldSquad.members.filter(member => member.member_id !== body.member_id)
    if (target) { squad.members = squad.members.filter(member => member.member_id !== target.member_id); oldSquad.members.push({ ...target, order_num: previous.order_num }) }
    squad.members.push({ ...members.find(member => member.member_id === body.member_id), order_num: body.order_num })
    return reply(route)
  }
  const clear = path.match(/^\/guild\/schedule\/assignment\/(\d+)$/)
  if (clear && method === 'DELETE') { schedule.teams.forEach(team => team.squads.forEach(squad => { squad.members = squad.members.filter(member => member.member_id !== Number(clear[1])) })); return reply(route) }
  if (path === '/guild/schedule/snapshot') { histories.unshift({ schedule_id: nextHistory++, schedule_name: body.schedule_name, create_time: '2026-09-13', detail: clone(schedule), workbook: clone(workbook) }); return reply(route) }
  if (path === '/guild/schedule/history') return reply(route, { data: histories.map(({ detail, workbook, ...row }) => row) })
  const historyApply = path.match(/^\/guild\/schedule\/history\/(\d+)\/apply$/)
  if (historyApply) {
    const history = histories.find(row => row.schedule_id === Number(historyApply[1]))
    schedule = clone(history.detail)
    schedule.teams.forEach(team => { team.team_id = nextTeam++; team.squads.forEach(squad => { squad.squad_id = nextSquad++ }) })
    workbook = clone(history.workbook)
    return reply(route)
  }
  const detail = path.match(/^\/guild\/schedule\/(\d+)(\/workbook)?$/)
  if (detail) { const history = histories.find(row => row.schedule_id === Number(detail[1])); return reply(route, { data: detail[2] ? { workbook: history.workbook } : { ...history.detail, schedule_id: history.schedule_id } }) }
  return reply(route, { data: [], rows: [], total: 0 })
})

const button = name => page.getByRole('button', { name, exact: true })
async function prompt(name) {
  await page.locator('.el-message-box input').fill(name)
  await page.locator('.el-message-box').getByRole('button', { name: '创建', exact: true }).click()
}
async function drop(source, target) {
  const transfer = await page.evaluateHandle(() => new DataTransfer())
  await source.dispatchEvent('dragstart', { dataTransfer: transfer })
  await target.dispatchEvent('dragover', { dataTransfer: transfer })
  await target.dispatchEvent('drop', { dataTransfer: transfer })
  await source.dispatchEvent('dragend', { dataTransfer: transfer })
}
async function assertSixSeatsInOneRow(root = '.schedule-panel') {
  const rows = await page.locator(`${root} .seat-grid`).evaluateAll(grids => grids.map(grid => {
    const seats = [...grid.children].map(seat => {
      const rect = seat.getBoundingClientRect()
      return { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
    })
    const rect = grid.getBoundingClientRect()
    const squad = grid.closest('.squad-box')
    return {
      columns: getComputedStyle(grid).gridTemplateColumns.split(' ').length,
      width: rect.width, right: rect.right, seats,
      scrollable: squad.scrollWidth > squad.clientWidth && getComputedStyle(squad).overflowX === 'auto'
    }
  }))
  assert.ok(rows.length > 0, '必须存在可验证的小队')
  for (const row of rows) {
    assert.equal(row.columns, 6, '电脑端小队必须是六列')
    assert.equal(row.seats.length, 6)
    assert.ok(Math.max(...row.seats.map(seat => seat.y)) - Math.min(...row.seats.map(seat => seat.y)) < 1, '六个位置必须在同一行')
    assert.ok(row.seats.every((seat, index) => !index || seat.x > row.seats[index - 1].x), '位置必须从左到右排列')
    assert.ok(row.seats.every(seat => seat.height <= 70), '位置卡片进一步收紧，高度不能超过70像素')
    // Preserve a readable minimum width in narrow windows, without making a second row.
    if (row.width >= 510) assert.ok(row.seats.at(-1).x + row.seats.at(-1).width <= row.right + 1, '空间足够时六个位置应全部显示')
    else assert.ok(row.scrollable, '窄窗口必须可横向滚动到第六个位置，不能换行或丢失位置')
  }
}
try {
  await page.goto('http://127.0.0.1/guild/group/schedule', { waitUntil: 'domcontentloaded' })
  await page.locator('.schedule-panel h3').waitFor({ timeout: 60000 })
  await page.evaluate(() => {
    window.__testMessages = []
    new MutationObserver(() => document.querySelectorAll('.el-message').forEach(node => {
      if (!window.__testMessages.includes(node.textContent)) window.__testMessages.push(node.textContent)
    })).observe(document.body, { childList: true, subtree: true })
  })
  await page.locator('.legacy-panel').filter({ hasText: '测试神相' }).waitFor()
  assert.match(await page.locator('.member-panel .folder-member-row').filter({ hasText: '测试神相' }).textContent(), /未排表/, '旧表格归档内容不是新盒子中的已排位置')
  const scheduleRequests = () => requests.filter(req => req.path.startsWith('/guild/schedule'))
  const backendWrites = () => scheduleRequests().filter(req => req.method !== 'GET')
  const initialReads = scheduleRequests().length
  await button('创建团队').waitFor()
  await button('创建团队').click()
  await prompt('测试进攻团')
  await page.locator('.team-title strong').filter({ hasText: '测试进攻团' }).waitFor()
  await button('＋ 在该团队创建小队').click()
  await prompt('测试一队')
  await page.locator('.seat').first().waitFor()
  assert.equal(await page.locator('.seat').count(), 6)
  await button('＋ 在该团队创建小队').click()
  await prompt('测试二队')
  await page.locator('.squad-header strong').filter({ hasText: '测试二队' }).waitFor()
  assert.equal(await page.locator('.seat').count(), 12)
  const squadsLayout = await page.locator('.schedule-panel .squad-box').evaluateAll(squads => squads.map(squad => {
    const r = squad.getBoundingClientRect(); return { x: r.x, y: r.y, bottom: r.bottom, height: r.height }
  }))
  assert.ok(Math.abs(squadsLayout[0].x - squadsLayout[1].x) < 1 && squadsLayout[1].y >= squadsLayout[0].bottom, '小队必须竖向排序')
  assert.ok(squadsLayout.every(squad => squad.height <= 115), '整个小队保持紧凑')
  for (const width of [1024, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: 900 })
    await assertSixSeatsInOneRow()
    const layout = await page.locator('.schedule-panel .team-list').evaluate(list => ({
      width: list.getBoundingClientRect().width,
      teamWidth: list.querySelector('.team-box').getBoundingClientRect().width
    }))
    assert.ok(Math.abs(layout.width - layout.teamWidth) < 1, `${width}px 下团队应占满右侧，不能把六个位置挤进半宽盒子`)
  }
  await page.setViewportSize({ width: 1280, height: 900 })
  assert.equal(await page.locator('.univer-host').count(), 0)
  assert.equal(await page.getByText('全部合并', { exact: true }).count(), 0)
  const seat = number => page.locator(`.schedule-panel .squad-box`).first().locator(`[data-seat="${number}"]`)
  const candidate = name => page.locator('.member-panel .folder-member-row').filter({ hasText: name })
  await drop(candidate('测试铁衣'), seat(3))
  await seat(3).locator('strong').filter({ hasText: '测试铁衣' }).waitFor()
  await seat(1).locator('.seat-main').click()
  assert.ok((await page.locator('.picker-tree details').evaluateAll(folders => folders.map(f => f.open))).every(open => !open), '选人职业默认全部收起')
  await page.locator('.picker-tree details').filter({ hasText: '素问' }).locator('summary').click()
  await page.locator('.picker-player').filter({ hasText: '测试素问' }).click()
  await seat(1).locator('strong').filter({ hasText: '测试素问' }).waitFor()
  await drop(seat(3).locator('.seat-main'), seat(1))
  await seat(1).locator('strong').filter({ hasText: '测试铁衣' }).waitFor()
  await seat(3).locator('strong').filter({ hasText: '测试素问' }).waitFor()
  await seat(4).locator('.seat-main').click()
  assert.ok((await page.locator('.picker-tree details').evaluateAll(folders => folders.map(f => f.open))).every(open => !open), '再次打开仍默认收起')
  await page.keyboard.press('Escape')
  await page.locator('.picker-tree').waitFor({ state: 'hidden' })
  await page.locator('.team-title').click()
  assert.equal(await seat(1).isVisible(), true, '点击盒子标题不能折叠')
  await button('收起 ▴').click()
  assert.equal(await seat(1).isVisible(), false)
  await button('展开 ▾').click()
  assert.equal(await seat(1).isVisible(), true)
  await button('临时补人').click()
  await page.locator('.el-dialog').filter({ hasText: '临时补人' }).locator('input').first().fill('测试临时替补')
  await button('加入临时列表').click()
  await candidate('测试临时替补').waitFor()
  await drop(candidate('测试临时替补'), seat(2))
  await seat(2).locator('strong').filter({ hasText: '测试临时替补' }).waitFor()
  assert.equal(scheduleRequests().length, initialReads, '普通编辑不应读/写后端排表或刷新')
  assert.equal(schedule.teams.length, 0, '新团队和小队也只能先修改本地')
  await page.locator('.draft-status').filter({ hasText: '本地已保存' }).waitFor({ timeout: 15000 })
  assert.equal(backendWrites().length, 0, '10秒自动保存只写前端数据库')
  const storedDrafts = await page.evaluate(() => new Promise((resolve, reject) => {
    const request = indexedDB.open('guild-schedule-drafts', 1)
    request.onsuccess = () => { const db = request.result, tx = db.transaction('drafts'), read = tx.objectStore('drafts').getAll(); tx.oncomplete = () => { resolve(read.result); db.close() }; tx.onerror = () => reject(tx.error) }
    request.onerror = () => reject(request.error)
  }))
  assert.equal(storedDrafts.length, 1)
  assert.ok(storedDrafts[0].key.includes('999999'))
  assert.equal(storedDrafts[0].draft.schedule.teams[0].squads.length, 2)
  assert.equal(storedDrafts[0].draft.dirty, true)
  await page.reload({ waitUntil: 'domcontentloaded' })
  await seat(2).locator('strong').filter({ hasText: '测试临时替补' }).waitFor()
  assert.equal(schedule.teams.length, 0, '刷新恢复的是本地未提交草稿，而不是写后端')
  // IndexedDB quota/error must not report local success or start backend writes.
  await page.evaluate(() => { window.__draftPut = IDBObjectStore.prototype.put; IDBObjectStore.prototype.put = function(...args) { if (this.name === 'drafts') throw new DOMException('模拟本地空间不足', 'QuotaExceededError'); return window.__draftPut.apply(this, args) } })
  await drop(seat(2).locator('.seat-main'), seat(4))
  await seat(4).locator('strong').filter({ hasText: '测试临时替补' }).waitFor()
  await page.locator('.save-error').filter({ hasText: '模拟本地空间不足' }).waitFor({ timeout: 15000 })
  await button('保存').click()
  assert.equal(backendWrites().length, 0)
  await page.evaluate(() => { IDBObjectStore.prototype.put = window.__draftPut })
  await button('重试本地保存').click()
  await page.locator('.draft-status').filter({ hasText: '本地已保存' }).waitFor()
  failWorkbookSave = true
  await button('保存').click()
  await page.getByText(/模拟保存失败/).first().waitFor()
  await page.locator('.draft-status').filter({ hasText: '提交未完成' }).waitFor()
  assert.equal(await seat(4).locator('strong').textContent(), '测试临时替补')
  assert.equal(schedule.teams.length, 1)
  assert.equal(schedule.teams[0].squads.length, 2)
  failWorkbookSave = false
  await button('保存').click()
  await page.getByText('排表已保存到后端', { exact: true }).first().waitFor({ timeout: 7000 })
  assert.equal(workbook.custom.keepMe, '旧数据保留')
  assert.equal(workbook.custom.guildScheduleBoxes.tempAssignments[0].orderNum, 4)
  assert.equal(requests.filter(req => req.method === 'POST' && req.path === '/guild/schedule/team').length, 1, '重试不重复创建')
  const savedWrites = backendWrites().length
  await button('保存').click()
  assert.equal(backendWrites().length, savedWrites, '重复保存不重复写未变的数据')
  // Cancelled prompts must not prevent saving an otherwise valid snapshot.
  await button('创建团队').click()
  await page.locator('.el-message-box').getByRole('button', { name: '取消', exact: true }).click()
  await button('保存历史').click()
  await page.locator('.el-message-box input').waitFor({ timeout: 5000 })
  await page.locator('.el-message-box input').fill('测试快照')
  await page.locator('.el-message-box').getByRole('button', { name: '保存', exact: true }).click()
  await page.getByText('历史已保存', { exact: true }).waitFor()
  assert.equal(histories.length, 1)
  await button('历史查询').click()
  await page.locator('.history-preview .seat strong').filter({ hasText: '测试临时替补' }).waitFor()
  await assertSixSeatsInOneRow('.history-preview')
  const beforeHistoryWrites = backendWrites().length
  await button('加载到草稿').click()
  await page.locator('.el-message-box').getByRole('button', { name: '加载到草稿', exact: true }).click()
  await page.getByText('历史已加载到本地草稿，请点击保存提交', { exact: true }).waitFor()
  await seat(4).locator('strong').filter({ hasText: '测试临时替补' }).waitFor()
  assert.equal(backendWrites().length, beforeHistoryWrites, '加载历史只改草稿')
  await button('保存').click()
  await page.locator('.draft-status').filter({ hasText: '已提交到后端' }).waitFor()
  await assertSixSeatsInOneRow()
  assert.equal(workbook.custom.guildScheduleBoxes.tempAssignments[0].teamId, schedule.teams[0].team_id)
  await page.reload({ waitUntil: 'domcontentloaded' })
  await seat(4).locator('strong').filter({ hasText: '测试临时替补' }).waitFor()
  if (process.env.SCHEDULE_SCREENSHOT) await page.screenshot({ path: process.env.SCHEDULE_SCREENSHOT, fullPage: true })
  await seat(1).locator('.clear-seat').click()
  await seat(1).locator('.empty-seat').waitFor()
  const beforeDeleteWrites = backendWrites().length
  await page.locator('.schedule-panel .squad-box').first().getByRole('button', { name: '删除小队', exact: true }).click()
  await page.locator('.el-message-box').getByRole('button', { name: '删除', exact: true }).click()
  await page.locator('.schedule-panel .squad-box').getByRole('button', { name: '删除小队', exact: true }).click()
  await page.locator('.el-message-box').getByRole('button', { name: '删除', exact: true }).click()
  await page.getByText('还没有小队', { exact: true }).waitFor()
  assert.equal(backendWrites().length, beforeDeleteWrites)
  assert.equal(schedule.teams[0].squads.length, 2)
  await page.locator('.box-tools').getByRole('button', { name: '删除', exact: true }).click()
  await page.locator('.el-message-box').getByRole('button', { name: '删除', exact: true }).click()
  await page.getByText('暂无团队，请点击上方“创建团队”', { exact: true }).waitFor()
  assert.equal(schedule.teams.length, 1, '删除团队也不能立即修改后端')
  await button('保存').click()
  await page.locator('.draft-status').filter({ hasText: '已提交到后端' }).waitFor()
  assert.equal(schedule.teams.length, 0)
  assert.equal(workbook.custom.guildScheduleBoxes.tempAssignments.length, 0)
  assert.equal(workbook.custom.guildScheduleTempMembers.length, 1)
  await page.getByText('团队管理', { exact: true }).click()
  await page.getByText('暂未开发', { exact: true }).waitFor()
  assert.match(page.url(), /\/guild\/group\/team-management$/)
  assert.deepEqual(errors, [], '不能有未处理的页面错误')
  console.log(JSON.stringify({ headless: true, realApiWrites: 0, desktopWidths: [1024, 1280, 1440, 1920], assertions: '竖排紧凑小队/六位置单行/职业默认收起/编辑零后端请求/10秒IndexedDB/草稿刷新恢复/本地失败提示/手动保存/部分失败重试/重复保存幂等/历史草稿/显式删除保存/原交互回归', mockRequests: requests.length, screenshot: process.env.SCHEDULE_SCREENSHOT || null }))
} catch (error) {
  console.error('Headless test failed:', error.message)
  console.error('Page errors:', JSON.stringify(errors))
  console.error('Recent mock paths:', JSON.stringify(requests.slice(-10).map(req => `${req.method} ${req.path}`)))
  console.error('UI messages:', JSON.stringify(await page.evaluate(() => window.__testMessages)))
  console.error('Draft status:', await page.locator('.draft-status').allTextContents())
  console.error('Visible save errors:', await page.locator('.save-error').allTextContents())
  const persisted = await page.evaluate(() => new Promise(resolve => {
    const open = indexedDB.open('guild-schedule-drafts', 1)
    open.onsuccess = () => { const db = open.result, tx = db.transaction('drafts'), r = tx.objectStore('drafts').getAll(); tx.oncomplete = () => { resolve(r.result[0]?.draft); db.close() } }
    open.onerror = () => resolve(null)
  }))
  console.error('Mock desired:', JSON.stringify(persisted && { schedule: persisted.schedule, workbook: persisted.workbook }))
  console.error('Mock backend:', JSON.stringify({ schedule, workbook }))
  throw error
} finally { await context.close(); await browser.close() }
