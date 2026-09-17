import {createRequire} from 'node:module'
import assert from 'node:assert/strict'
import path from 'node:path'
const require=createRequire(import.meta.url)
const {chromium}=require('C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.js')
const browser=await chromium.launch({headless:true,channel:'msedge'})
const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage()
const demoPassword=process.env.NSH_DEMO_PASSWORD
if(!demoPassword)throw new Error('Set NSH_DEMO_PASSWORD before running this live browser test')
await page.route('**/*',r=>['localhost','127.0.0.1'].includes(new URL(r.request().url()).hostname)?r.continue():r.abort())
try{
 await page.goto('http://127.0.0.1:5173/login?redirect=/personal/profile-edit')
 await page.getByPlaceholder('请输入账号',{exact:true}).fill('nsh_demo_manager')
 await page.getByPlaceholder('请输入密码',{exact:true}).fill(demoPassword)
 await page.getByRole('button',{name:'登录',exact:true}).click()
 await page.getByPlaceholder('游戏玩家名').waitFor({timeout:45000})
 await page.waitForTimeout(1000)
 for(const name of ['系统公告','安全提示']){const d=page.getByRole('dialog',{name,exact:true});if(await d.isVisible()){await d.locator('.el-dialog__headerbtn,.el-message-box__headerbtn').click();await d.waitFor({state:'hidden'})}}
 assert.equal(await page.locator('.player-center .el-select__wrapper').first().evaluate(n=>getComputedStyle(n).isolation),'isolate','selected profession must paint above opaque select background')
 await page.goto('http://127.0.0.1:5173/user/profile')
 await page.waitForURL('**/personal/profile-edit')
 await page.getByPlaceholder('游戏玩家名').waitFor()
 const notice=page.getByRole('dialog',{name:'系统公告',exact:true});await notice.waitFor({timeout:4000}).catch(()=>{});if(await notice.isVisible()){await notice.locator('.el-dialog__headerbtn').click();await notice.waitFor({state:'hidden'})}
 assert.equal(await page.locator('.player-center').count(),1)
 assert.equal(await page.getByText('手机号码',{exact:true}).count(),0,'legacy account-profile layout removed')
 for(const placeholder of ['游戏玩家名','游戏 UID，保留前导零','仅本人及本帮会管理员／助手可见'])assert.ok(await page.getByPlaceholder(placeholder).isVisible())
 await page.goto('http://127.0.0.1:5173/user/profile/resetPwd')
 await page.waitForURL('**/personal/profile-edit?security=password')
 await notice.waitFor({timeout:4000}).catch(()=>{});if(await notice.isVisible()){await notice.locator('.el-dialog__headerbtn').click();await notice.waitFor({state:'hidden'})}
 const security=page.getByRole('dialog',{name:'修改登录密码',exact:true})
 await security.getByPlaceholder('请输入旧密码').waitFor()
 await security.getByRole('button',{name:'关闭',exact:true}).click()
 await security.waitFor({state:'hidden'});await page.waitForURL('**/personal/profile-edit')
 await page.locator('.avatar-wrapper').hover()
 const avatarLink=page.locator('.el-dropdown-menu a[href="/personal/profile-edit"]')
 await avatarLink.waitFor({state:'visible'});assert.ok(await avatarLink.isVisible());await avatarLink.click()
 await page.locator('.player-center .el-loading-mask').waitFor({state:'hidden'})
 await page.screenshot({path:path.resolve('../.artifacts/activity-dev/统一个人中心入口.png'),animations:'disabled',fullPage:true})
 assert.equal(await page.locator('.player-center .el-select .profession-tag').first().innerText(),'铁衣')
 console.log('UNIFIED PROFILE PASSED: old/new URLs and avatar share the sole game profile; legacy password link opens separate account-security dialog; visible compact career labels.')
}finally{await context.close();await browser.close()}
