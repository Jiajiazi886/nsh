// Isolated, headless detail-page regression. All API calls are intercepted.
import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { mkdir, writeFile } from 'node:fs/promises'
import { createServer } from 'vite'

const require = createRequire(import.meta.url)
const { chromium } = require(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright')
const frontend = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..')
const output = path.resolve(frontend, '../.artifacts/battle-detail')
await mkdir(output, { recursive: true })

const seats = (filled, profession) => Array.from({ length: 6 }, (_, index) => ({
  position: index + 1,
  requiredProfession: index >= filled && index === 5 ? '素问' : '',
  player: index < filled ? {
    memberId: `member-${profession}-${index}`,
    name: index === 3 ? '名字较长的测试玩家四号' : `测试玩家${index + 1}`,
    profession: index % 2 ? '潮光' : profession,
    isTemporary: false,
  } : null,
}))

const teams = [
  { id: 'team-1', name: '进攻一团', squads: [
    { id: 'squad-1', name: '一队', seats: seats(5, '沧澜') },
    { id: 'squad-2', name: '二队', seats: seats(3, '九灵') },
  ] },
  { id: 'team-2', name: '防守团', squads: [
    { id: 'squad-3', name: '三队', seats: seats(1, '铁衣') },
  ] },
]

const activity = {
  activityId: 'act-detail', orgId: 'guild-101', orgType: 'guild', orgName: '九肆帮会',
  name: '周四帮会约战', startsAt: '2026-09-17T20:30:00', remark: '公开报名，按职业缺口补位。',
  state: 'open', isPublic: true, revision: 4, canManage: true, canSignup: false,
  hasReport: false, reportIds: [], totalSeats: 18, emptySeats: 9,
  shortages: { 素问: 3, 铁衣: 2 },
  snapshot: { snapshotId: 'snap-4', version: 4, savedAt: '2026-09-15T19:40:00', teams },
}

const csv = [
  '九肆帮会,1',
  '玩家名字,职业,击败/清泉,助攻,资源,对玩家伤害,人伤卸甲,对建筑伤害,破塔卸甲,治疗值,承受伤害,重伤,复活/清泉,焚骨',
  '测试玩家1,铁衣,1/0,2,3,4,5,6,7,8,9,10,11,12',
].join('\r\n')
const csvPath = path.join(output, 'detail-import-sample.csv')
await writeFile(csvPath, csv, 'utf8')

const server = await createServer({ root: frontend, server: { host: '127.0.0.1', port: 0, open: false }, mode: 'development' })
let browser
try {
  await server.listen()
  const base = `http://127.0.0.1:${server.httpServer.address().port}`
  browser = await chromium.launch({ headless: true, channel: process.env.BATTLE_BROWSER_CHANNEL || 'msedge' })
  const context = await browser.newContext({ viewport: { width: 1648, height: 1040 }, deviceScaleFactor: 1 })
  await context.addCookies([{ name: 'Admin-Token', value: 'isolated-fixture-not-real-token', url: base }])
  const page = await context.newPage()
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })

  await page.route('**/*', async route => {
    const request = route.request()
    const url = new URL(request.url())
    if (url.origin !== base) return route.abort()
    if (!url.pathname.startsWith('/dev-api/')) return route.continue()
    const apiPath = url.pathname.slice(8)
    const reply = (data, extra = {}) => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ code: 200, msg: 'isolated fixture', success: true, requestId: 'req-detail', data, ...extra }),
    })
    if (apiPath === '/getInfo') return reply(null, { user: { userId: '101', userName: 'detail-owner', nickName: '测试管理员' }, roles: ['common'], permissions: ['activities:read'] })
    if (apiPath === '/getRouters') return reply([
      { path: '/personal', component: 'Layout', name: 'Personal', meta: { title: '个人管理' }, children: [] },
      { path: '/guild', component: 'Layout', name: 'Guild', meta: { title: '帮会管理' }, children: [] },
    ])
    if (apiPath === '/transport/crypto/frontend-config') return reply({ enabled: false, mode: 'off', policy: {} })
    if (apiPath === '/api/v1/activities/act-detail') return reply(activity)
    if (apiPath === '/api/v1/activities') return reply({ items: [], total: 0, page: 1, pageSize: 20 })
    if (apiPath === '/api/v1/organizations') return reply([])
    if (apiPath === '/api/v1/activity-profiles') return reply([])
    if (apiPath === '/api/v1/profession-styles') return reply([])
    return route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ code: 503, success: false, msg: `fixture missing: ${apiPath}` }) })
  })

  await page.goto(`${base}/battle-information/detail/act-detail`)
  await page.getByRole('heading', { name: '周四帮会约战' }).waitFor()
  assert.equal(await page.getByText('关联已有 CSV 战报', { exact: true }).count(), 0)
  assert.equal(await page.getByText('输入战报 ID', { exact: true }).count(), 0)
  assert.ok(await page.getByRole('button', { name: '上传 CSV', exact: true }).count() >= 1)
  assert.equal(await page.locator('body').evaluate(el => el.scrollWidth <= el.clientWidth), true, 'desktop must not overflow horizontally')
  await page.screenshot({ path: path.join(output, 'implementation-desktop.png'), fullPage: true })

  await page.getByRole('button', { name: '上传 CSV', exact: true }).first().click()
  const dialog = page.getByRole('dialog', { name: '上传 CSV 战报' })
  await dialog.waitFor()
  assert.ok(await dialog.getByText('文件会直接归属当前约战，不需要再输入战报 ID。', { exact: true }).isVisible())
  await dialog.locator('input[type=file]').setInputFiles(csvPath)
  await dialog.getByText('1 名玩家', { exact: false }).waitFor()
  await dialog.screenshot({ path: path.join(output, 'implementation-import-dialog.png') })

  await dialog.getByRole('button', { name: '取消', exact: true }).click()
  await page.setViewportSize({ width: 920, height: 1040 })
  await page.waitForTimeout(250)
  assert.equal(await page.locator('body').evaluate(el => el.scrollWidth <= el.clientWidth), true, 'narrow layout must not overflow horizontally')
  await page.screenshot({ path: path.join(output, 'implementation-narrow.png'), fullPage: true })

  await page.setViewportSize({ width: 1648, height: 1040 })
  await page.goto(`${base}/personal/battle-information/history`)
  await page.getByRole('heading', { name: '历史约战', exact: true, level: 2 }).waitFor()
  assert.equal(await page.getByText('战报记录（含未关联旧战报）', { exact: true }).count(), 0)
  assert.equal(await page.locator('.battle-panel').count(), 1, 'history page only keeps the activity list')
  await page.screenshot({ path: path.join(output, 'implementation-history-clean.png'), fullPage: true })
  assert.equal(errors.length, 0, errors.join('\n'))
  console.log(`Detail UI passed. Screenshots: ${output}`)
} finally {
  if (browser) await browser.close()
  await server.close()
}
