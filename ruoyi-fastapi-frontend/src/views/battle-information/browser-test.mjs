// Isolated, headless UI regression. Every API call is intercepted; no real backend or DB.
import assert from 'node:assert/strict'
import {createRequire} from 'node:module'
import {fileURLToPath} from 'node:url'
import path from 'node:path'
import {createServer} from 'vite'
const require=createRequire(import.meta.url)
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright')
const frontend=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..')
const output=path.resolve(frontend,'../.artifacts/battle-information')
const {mkdir}=await import('node:fs/promises');await mkdir(output,{recursive:true})
const server=await createServer({root:frontend,server:{host:'127.0.0.1',port:0,open:false},mode:'development'})
let browser
try {
  await server.listen()
  const base='http://127.0.0.1:'+server.httpServer.address().port
  browser=await chromium.launch({headless:true,channel:process.env.BATTLE_BROWSER_CHANNEL || 'msedge'})
  const context=await browser.newContext({viewport:{width:1360,height:960}})
  await context.addCookies([{name:'Admin-Token',value:'isolated-fixture-not-real-token',url:base}])
  const page=await context.newPage(),errors=[],writes=[]
  page.on('pageerror',e=>errors.push(e.message))
  const players=[{memberId:'9',name:'测试铁衣',profession:'铁衣',isTemporary:false},{memberId:'10',name:'测试素问',profession:'素问',isTemporary:false}]
  const squads=[{id:'s1',name:'一队',seats:Array.from({length:6},(_,i)=>({position:i+1,requiredProfession:'',player:null}))}]
  let activity={activityId:'act_test',orgId:'guild-101',orgType:'guild',orgName:'测试帮会',name:'帮会周末约战',startsAt:'2026-09-20T20:00:00',endsAt:'2026-09-20T22:00:00',remark:'隔离测试',state:'open',isPublic:false,revision:1,canManage:true,canSignup:false,hasReport:false,reportIds:[],totalSeats:6,emptySeats:6,shortages:{'不限职业':6},snapshot:{snapshotId:'snap1',version:1,savedAt:'2026-09-14T20:00:00',teams:[{id:'t1',name:'进攻一团',squads}]}}
  const clone=x=>JSON.parse(JSON.stringify(x))
  let failSave=false
  await page.route('**/*',async route=>{
    const req=route.request(),url=new URL(req.url())
    if(url.origin!==base)return route.abort()
    if(!url.pathname.startsWith('/dev-api/'))return route.continue()
    const p=url.pathname.slice(8),method=req.method(),body=req.postData()?JSON.parse(req.postData()):null
    const v1=p.startsWith('/api/v1')
    const reply=(data,extra={})=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({code:200,msg:'isolated fixture',...(v1?{success:true,requestId:'req_fixture'}:{}),data,...extra})})
    if(p==='/getInfo')return reply(null,{user:{userId:'101',userName:'test-owner',nickName:'测试帮会'},roles:['common'],permissions:['guild:schedule:list','activities:read']})
    if(p==='/getRouters')return reply([{path:'/guild',component:'Layout',name:'Guild',meta:{title:'帮会管理'},children:[{path:'schedule',component:'guild/schedule/index',name:'GuildSchedule',meta:{title:'约战排表'}}]},{path:'/personal',component:'Layout',name:'Personal',meta:{title:'个人管理'},children:[]}])
    if(p==='/transport/crypto/frontend-config')return reply({enabled:false,mode:'off',policy:{}})
    if(p==='/api/v1/organizations')return reply([{orgId:'guild-101',orgType:'guild',name:'测试帮会',role:'owner',canManage:true}])
    if(p==='/api/v1/activity-profiles')return reply(players)
    if(p==='/api/v1/activity-professions')return reply(['铁衣','素问','神相'])
    if(p==='/api/v1/activity-lineup-templates')return reply([])
    if(p==='/api/v1/profession-styles')return reply([])
    if(p==='/api/v1/activities'){
      const club={...clone(activity),activityId:'act_club',orgType:'club',orgName:'测试俱乐部',name:'俱乐部练习约战'}
      return reply({items:[clone(activity),club],total:2,page:1,pageSize:20})
    }
    if(p==='/api/v1/activities/act_test')return reply(clone(activity))
    if(p==='/api/v1/activities/act_test/snapshots')return reply([])
    if(p==='/api/v1/activities/act_test/lineup'&&method==='PUT'){
      writes.push(clone(body))
      if(failSave)return route.fulfill({status:500,contentType:'application/json',body:JSON.stringify({code:500,success:false,errorKey:'INTERNAL_ERROR',msg:'隔离模拟保存失败',requestId:'req_failure'})})
      assert.equal(body.expectedRevision,activity.revision)
      activity.revision++;activity.snapshot={snapshotId:'snap'+activity.revision,version:activity.revision,savedAt:'2026-09-14T20:01:00',teams:body.teams.map(t=>({...t,squads:t.squads.map(s=>({...s,seats:s.seats.map(seat=>({...seat,player:seat.player?(seat.player.memberId?players.find(p=>p.memberId===seat.player.memberId):{...seat.player,isTemporary:true}):null}))}))}))}
      return reply({activityId:activity.activityId,revision:activity.revision,snapshotId:activity.snapshot.snapshotId})
    }
    return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({code:503,success:false,errorKey:'FIXTURE_NOT_IMPLEMENTED',msg:'该请求未纳入隔离测试：'+p})})
  })
  await page.goto(base+'/personal/battle-information/mine')
  await page.getByRole('heading',{name:'帮会活动'}).waitFor()
  await page.getByText('俱乐部练习约战',{exact:true}).waitFor()
  const guild=await page.getByRole('heading',{name:'帮会活动'}).boundingBox(),club=await page.getByRole('heading',{name:'俱乐部活动'}).boundingBox()
  assert.ok(guild.x<club.x,'guild left, club right')
  await page.screenshot({path:path.join(output,'my-battles-pc.png'),fullPage:true})
  await page.goto(base+'/guild/schedule?activityId=act_test')
  await page.getByRole('heading',{name:'帮会周末约战 · 约战排表'}).waitFor()
  const folders=page.locator('.battle-candidate-tree button[data-state]')
  await folders.first().waitFor()
  assert.equal(await page.locator('.battle-candidate-tree button[data-state="open"]').count(),0,'profession folders initially collapsed')
  await folders.filter({hasText:'铁衣'}).click()
  assert.equal(await page.locator('.battle-candidate-tree button[data-state="open"]').count(),1,'only one profession folder opens')
  await page.locator('.battle-player',{hasText:'测试铁衣'}).dragTo(page.locator('.battle-seat').first())
  assert.equal(writes.length,0,'assignment does not write backend')
  await page.waitForTimeout(10500)
  assert.equal(writes.length,0,'ten-second autosave stays local')
  const stored=await page.evaluate(()=>new Promise((resolve,reject)=>{const r=indexedDB.open('guild-schedule-drafts',1);r.onsuccess=()=>{const q=r.result.transaction('drafts').objectStore('drafts').getAll();q.onsuccess=()=>resolve(q.result)};r.onerror=reject}))
  assert.ok(stored.some(r=>r.draft.activityId==='act_test'&&r.draft.dirty))
  await page.getByRole('button',{name:'保存',exact:true}).click()
  await page.getByText('已保存，网页和小程序成员可查看此版本。',{exact:true}).waitFor()
  assert.equal(writes.length,1,'one atomic save request')
  assert.equal(activity.snapshot.teams[0].squads[0].seats[0].player.name,'测试铁衣')
  // Occupied seat cannot be fixed to a mismatched profession.
  await page.locator('.battle-seat').first().locator('[data-slot="select-trigger"]').click()
  await page.getByRole('option',{name:'素问',exact:true}).click()
  await page.getByText('已安排玩家的职业与指定职业不符，请先移出玩家',{exact:true}).waitFor()
  await page.screenshot({path:path.join(output,'lineup-editor-pc.png'),fullPage:true})
  failSave=true
  await page.locator('.battle-seat').first().getByRole('button',{name:'移出',exact:true}).click()
  await page.getByRole('button',{name:'保存',exact:true}).click()
  await page.locator('.battle-error').filter({hasText:'隔离模拟保存失败'}).waitFor()
  assert.equal(activity.snapshot.teams[0].squads[0].seats[0].player.name,'测试铁衣','failed save retains visible snapshot')
  assert.equal(errors.length,0,errors.join('\n'))
  console.log('Isolated UI passed: columns, collapsed picker, local autosave, atomic save, profession warning, failed save. Screenshots: '+output)
}finally{if(browser)await browser.close();await server.close()}
