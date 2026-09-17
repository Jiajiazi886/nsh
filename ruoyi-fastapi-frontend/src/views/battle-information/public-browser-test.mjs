// Isolated public-battle visual regression. No real backend or database calls.
import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { mkdir } from 'node:fs/promises'
import { createServer } from 'vite'

const require = createRequire(import.meta.url)
const { chromium } = require(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright')
const frontend = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..')
const output = path.resolve(frontend, '../.artifacts/battle-public')
await mkdir(output, { recursive: true })

const activities = [
  { activityId:'public-1',orgType:'guild',orgName:'九肆帮会',name:'周四帮会联赛约战',startsAt:'2026-09-17T20:30:00',state:'open',isPublic:true,totalSeats:60,emptySeats:8,hasReport:false,shortages:{素问:3,铁衣:2,潮光:3} },
  { activityId:'public-2',orgType:'club',orgName:'听风俱乐部',name:'周末友谊练习赛',startsAt:'2026-09-19T20:30:00',state:'open',isPublic:true,totalSeats:36,emptySeats:4,hasReport:false,shortages:{素问:2,九灵:1,沧澜:1} },
  { activityId:'public-3',orgType:'guild',orgName:'扶摇帮会',name:'下周二正式约战',startsAt:'2026-09-22T20:30:00',state:'open',isPublic:true,totalSeats:60,emptySeats:12,hasReport:false,shortages:{铁衣:4,神相:3,鸿音:2} },
]

const server = await createServer({ root: frontend, server: { host:'127.0.0.1',port:0,open:false }, mode:'development' })
let browser
try {
  await server.listen()
  const base = `http://127.0.0.1:${server.httpServer.address().port}`
  browser = await chromium.launch({ headless:true, channel:process.env.BATTLE_BROWSER_CHANNEL || 'msedge' })
  const context = await browser.newContext({ viewport:{width:1440,height:960},deviceScaleFactor:1 })
  await context.addCookies([{ name:'Admin-Token',value:'isolated-public-fixture',url:base }])
  const page = await context.newPage()
  const errors = []
  const activityQueries = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
  await page.route('**/*', async route => {
    const request = route.request(), url = new URL(request.url())
    if (url.origin !== base) return route.abort()
    if (!url.pathname.startsWith('/dev-api/')) return route.continue()
    const apiPath = url.pathname.slice(8)
    const reply = (data, extra={}) => route.fulfill({ status:200,contentType:'application/json',body:JSON.stringify({code:200,msg:'fixture',success:true,requestId:'req-public',data,...extra}) })
    if (apiPath === '/getInfo') return reply(null,{user:{userId:'23',userName:'member23',nickName:'测试成员'},roles:['common'],permissions:['activities:read']})
    if (apiPath === '/getRouters') return reply([
      {path:'/guild',component:'Layout',name:'Guild',meta:{title:'帮会管理'},children:[]},
      {path:'/personal',component:'Layout',name:'Personal',meta:{title:'个人管理'},children:[]},
    ])
    if (apiPath === '/transport/crypto/frontend-config') return reply({enabled:false,mode:'off',policy:{}})
    if (apiPath === '/api/v1/activities') { activityQueries.push(url.search); return reply({items:activities,total:activities.length,page:1,pageSize:20}) }
    if (apiPath === '/api/v1/organizations') return reply([])
    if (apiPath === '/api/v1/profession-styles') return reply([])
    return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({code:503,success:false,msg:`fixture missing: ${apiPath}`})})
  })

  await page.goto(`${base}/personal/battle-information/public`)
  await page.getByRole('heading',{name:'找约战',exact:true,level:2}).waitFor()
  await page.getByText('周四帮会联赛约战',{exact:true}).waitFor()
  assert.equal(await page.locator('.battle-public-card').count(),3)
  const actionColor = await page.getByRole('button',{name:'查看并报名',exact:true}).first().evaluate(el=>getComputedStyle(el).color)
  assert.match(actionColor,/(?:255\s*,\s*255\s*,\s*255|oklch\(0\.98)/,'primary action must use white text')
  assert.equal(await page.locator('body').evaluate(el=>el.scrollWidth<=el.clientWidth),true)
  await page.screenshot({path:path.join(output,process.env.PUBLIC_AFTER==='1'?'public-after.png':'public-before.png'),fullPage:true})
  await page.locator('.battle-public-filter-controls [data-slot="select-trigger"]').click()
  await page.getByRole('option',{name:'素问',exact:true}).click()
  await page.waitForTimeout(100)
  assert.ok(activityQueries.some(query=>query.includes('profession=%E7%B4%A0%E9%97%AE')),'profession filter must reach the API query')
  await page.getByRole('button',{name:'清除筛选',exact:true}).click()
  await page.setViewportSize({width:900,height:960})
  await page.waitForTimeout(150)
  assert.equal(await page.locator('body').evaluate(el=>el.scrollWidth<=el.clientWidth),true,'narrow public page must not overflow')
  if(process.env.PUBLIC_AFTER==='1')await page.screenshot({path:path.join(output,'public-after-narrow.png'),fullPage:true})
  assert.equal(errors.length,0,errors.join('\n'))
  console.log(`Public battle capture passed: ${output}`)
} finally {
  if (browser) await browser.close()
  await server.close()
}
