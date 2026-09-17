// Isolated headless browser. Real local APIs only; never uses the user's browser session.
import {createRequire} from 'node:module'
import path from 'node:path'
import assert from 'node:assert/strict'
const require=createRequire(import.meta.url)
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright')
const browser=await chromium.launch({headless:true,channel:'msedge'})
const context=await browser.newContext({viewport:{width:1440,height:1000}})
const page=await context.newPage()
const failures=[]
const demoPassword=process.env.NSH_DEMO_PASSWORD
if(!demoPassword)throw new Error('Set NSH_DEMO_PASSWORD before running this live browser test')
await page.route('**/*',route=>{
  const url=new URL(route.request().url())
  if(url.hostname!=='127.0.0.1' && url.hostname!=='localhost')return route.abort()
  return route.continue()
})
page.on('response',response=>{if(response.url().includes('/dev-api/')&&response.status()>=500)failures.push(new URL(response.url()).pathname)})
const output=path.resolve('../.artifacts/activity-dev')
try{
  await page.goto('http://127.0.0.1:5173/login?redirect=/personal/battle-information/mine')
  await page.getByPlaceholder('请输入账号',{exact:true}).fill('nsh_demo_manager')
  await page.getByPlaceholder('请输入密码',{exact:true}).fill(demoPassword)
  await page.getByRole('button',{name:'登录',exact:true}).click()
  await page.waitForURL('**/personal/battle-information/mine',{timeout:45000})
  await page.getByText('组织内部约战 · 可编辑阵容',{exact:true}).waitFor({timeout:45000})
  await page.getByText('暂无俱乐部活动',{exact:true}).waitFor()
  assert.equal(await page.getByText('俱乐部六人练习',{exact:true}).count(),0)
  const notice=page.getByRole('dialog',{name:'系统公告',exact:true})
  if(await notice.isVisible())await notice.locator('.el-dialog__headerbtn').click()
  await page.screenshot({path:path.join(output,'新版我的约战.png'),fullPage:true})
  await page.locator('.battle-compact-card').filter({hasText:'组织内部约战 · 可编辑阵容'}).getByRole('button',{name:'查看详情',exact:true}).click()
  await page.waitForURL('**/battle-information/detail/**')
  await page.getByRole('button',{name:'配置排表',exact:true}).click()
  await page.waitForURL('**/guild/schedule?activityId=*')
  await page.getByRole('button',{name:'创建团队',exact:true}).waitFor({timeout:5000})
  await page.getByText('候选玩家',{exact:true}).waitFor()
  assert.equal(await page.locator('.battle-candidate-tree button[data-state="open"]').count(),0)
  const [saved]=await Promise.all([
    page.waitForResponse(response=>response.request().method()==='PUT'&&response.url().endsWith('/lineup')),
    page.getByRole('button',{name:'保存',exact:true}).click(),
  ])
  assert.equal(saved.status(),200)
  assert.equal((await saved.json()).success,true)
  await page.screenshot({path:path.join(output,'新版真实阵容编辑.png'),fullPage:true})
  assert.deepEqual(failures,[])
  console.log('LIVE BROWSER PASSED: real login, participation-only personal activities, lineup editor, real snapshot save, collapsed profession tree; no mocked API, no 500 responses.')
}catch(error){
  await page.waitForLoadState('domcontentloaded',{timeout:5000}).catch(()=>{})
  let texts=[]
  try{texts=await page.locator('.battle-page').allInnerTexts()}catch{}
  console.error('Local UI verification failed:',new URL(page.url()).pathname,texts,error.message)
  await page.screenshot({path:path.join(output,'界面检查失败.png'),fullPage:true}).catch(()=>{})
  throw error
}finally{
  await context.close()
  await browser.close()
}
