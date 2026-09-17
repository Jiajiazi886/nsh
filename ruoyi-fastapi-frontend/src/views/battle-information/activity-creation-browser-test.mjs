// Isolated entry-placement regression. No real backend or database calls.
import assert from 'node:assert/strict'
import {createRequire} from 'node:module'
import {fileURLToPath} from 'node:url'
import path from 'node:path'
import {createServer} from 'vite'

const require=createRequire(import.meta.url)
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_PATH||'playwright')
const frontend=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..')
const server=await createServer({root:frontend,server:{host:'127.0.0.1',port:0,open:false},mode:'development'})
let browser

try{
  await server.listen()
  const base=`http://127.0.0.1:${server.httpServer.address().port}`
  browser=await chromium.launch({headless:true,channel:process.env.BATTLE_BROWSER_CHANNEL||'msedge'})
  const context=await browser.newContext({viewport:{width:1360,height:900}})
  await context.addCookies([{name:'Admin-Token',value:'isolated-entry-fixture',url:base}])
  const page=await context.newPage()
  const errors=[]
  const creates=[]
  page.on('pageerror',error=>errors.push(error.message))
  page.on('console',message=>{if(message.type()==='error')errors.push(message.text())})

  await page.route('**/*',async route=>{
    const request=route.request(),url=new URL(request.url())
    if(url.origin!==base)return route.abort()
    if(!url.pathname.startsWith('/dev-api/'))return route.continue()
    const apiPath=url.pathname.slice(8),method=request.method()
    const reply=(data,extra={})=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({code:200,msg:'fixture',success:true,requestId:'req-entry',data,...extra})})
    if(apiPath==='/getInfo')return reply(null,{user:{userId:'101',userName:'owner',nickName:'测试管理员'},roles:['common'],permissions:['guild:schedule:list','activities:read']})
    if(apiPath==='/getRouters')return reply([
      {path:'/guild',component:'Layout',name:'Guild',meta:{title:'帮会管理'},children:[{path:'schedule',component:'guild/schedule/index',name:'GuildSchedule',meta:{title:'约战排表'}}]},
      {path:'/personal',component:'Layout',name:'Personal',meta:{title:'个人管理'},children:[]},
    ])
    if(apiPath==='/transport/crypto/frontend-config')return reply({enabled:false,mode:'off',policy:{}})
    if(apiPath==='/api/v1/profession-styles')return reply([])
    if(apiPath==='/api/v1/organizations')return reply([{orgId:'guild-101',orgType:'guild',name:'测试帮会',role:'owner',canManage:true}])
    if(apiPath==='/api/v1/activities'&&method==='GET')return reply({items:[],total:0,page:1,pageSize:100})
    if(apiPath==='/api/v1/activities'&&method==='POST'){
      creates.push(JSON.parse(request.postData()))
      return reply({activityId:'activity-new'})
    }
    if(apiPath==='/api/v1/activities/activity-new')return reply({activityId:'activity-new',orgId:'guild-101',orgType:'guild',orgName:'测试帮会',name:'新建周四约战',startsAt:'2026-09-17T20:30:00',state:'open',isPublic:false,revision:0,canManage:true,canSignup:false,hasReport:false,reportIds:[],totalSeats:0,emptySeats:0,shortages:{},snapshot:null})
    if(apiPath==='/api/v1/activity-profiles'||apiPath==='/api/v1/activity-professions')return reply([])
    return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({code:503,success:false,msg:`fixture missing: ${apiPath}`})})
  })

  await page.goto(`${base}/personal/battle-information/mine`)
  await page.getByRole('heading',{name:'我的约战',exact:true,level:2}).waitFor()
  assert.equal(await page.getByRole('button',{name:'创建约战',exact:true}).count(),0,'My Battles must be view-only')

  await page.goto(`${base}/guild/schedule`)
  await page.getByRole('heading',{name:'约战排表',exact:true,level:2}).waitFor()
  const createButton=page.getByRole('button',{name:'创建约战',exact:true})
  await createButton.waitFor()
  assert.equal(await createButton.isEnabled(),true,'organization managers can create from lineup schedule')
  await createButton.click()
  const dialog=page.getByRole('dialog',{name:'创建约战'})
  await dialog.waitFor()
  await dialog.locator('.el-form-item').filter({hasText:'活动名称'}).locator('input').fill('新建周四约战')
  await dialog.getByRole('button',{name:'创建并配置排表',exact:true}).click()
  await page.waitForURL('**/guild/schedule?activityId=activity-new')
  assert.equal(creates.length,1,'creation must send one API request')
  assert.equal(creates[0].orgId,'guild-101')
  assert.equal(creates[0].name,'新建周四约战')
  assert.equal(errors.length,0,errors.join('\n'))
  console.log('Activity creation entry passed: My Battles is view-only; Schedule creates and opens lineup.')
}finally{
  if(browser)await browser.close()
  await server.close()
}
