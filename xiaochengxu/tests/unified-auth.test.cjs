const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const roots = [path.resolve(__dirname, '..'), path.resolve(__dirname, '../hhhhhhtml/jiusi-data-dashboard-frontend/demo')]
function runtime(root) {
  const values = new Map(), calls = [], pending = []
  const app = { globalData: { user: { old: true } } }; let page
  const wx = { getStorageSync: k => values.get(k), setStorageSync: (k,v) => values.set(k,v), removeStorageSync: k => values.delete(k), getAccountInfoSync: () => ({ miniProgram: { envVersion: 'develop' } }), reLaunch: o => { calls.push(o.url); if(o.complete)o.complete() }, switchTab: o => calls.push(o.url), showToast:()=>{}, request: o => pending.push(o) }
  const cache = new Map()
  function load(file) {
    file = path.resolve(root, file); if (!path.extname(file)) file += '.js'
    if(cache.has(file))return cache.get(file).exports
    const module = {exports:{}}; cache.set(file,module)
    vm.runInNewContext(fs.readFileSync(file,'utf8'), {module,exports:module.exports,require: p => load(path.resolve(path.dirname(file),p)),wx,getApp:()=>app,Page: definition => {page=definition;page.setData=d=>Object.assign(page.data,d)},console})
    return module.exports
  }
  return {load,wx,values,calls,pending,app,get page(){return page},reply(status,data){pending.shift().success({statusCode:status,data})}}
}
const ok = data => ({code:200,success:true,data})
const expired = {code:401,success:false,msg:'登录已过期',errorKey:'UNAUTHORIZED'}
for(const root of roots) {
  const label = path.relative(roots[0],root)||'main'
  test(label+': JSON login uses the same backend account and never persists password',async()=>{
    const r=runtime(root), auth=r.load('services/auth'), storage=r.load('utils/storage')
    const promise=auth.login({username:' admin ',password:'test-secret',code:'123',uuid:'u'})
    await Promise.resolve()
    assert.match(r.pending[0].url,/\/api\/v1\/auth\/login$/)
    assert.equal(r.pending[0].header.Authorization,undefined)
    assert.equal(r.pending[0].data.userName,'admin')
    r.reply(200,ok({accessToken:'shared-token',expiresIn:3600}))
    assert.equal((await promise).token,'shared-token')
    assert.equal(storage.getToken(),'')
    assert.equal(JSON.stringify([...r.values.values()]).includes('test-secret'),false)
  })
  test(label+': authenticated 401 clears stored and global identity',async()=>{
    const r=runtime(root), storage=r.load('utils/storage'); storage.setToken('old')
    const promise=r.load('services/activities').getClient().me(); await Promise.resolve()
    r.reply(401,expired); await assert.rejects(promise)
    assert.equal(storage.getToken(),'');assert.equal(r.app.globalData.user,null)
    assert.equal(r.calls.length,1)
  })
  test(label+': late expired response does not log out a newer account',async()=>{
    const r=runtime(root), storage=r.load('utils/storage'); storage.setToken('old')
    const promise=r.load('services/activities').getClient().me();await Promise.resolve()
    storage.setToken('new');r.reply(401,expired);await assert.rejects(promise)
    assert.equal(storage.getToken(),'new');assert.equal(r.calls.length,0)
  })
  test(label+': network failure retains session for retry',async()=>{
    const r=runtime(root), storage=r.load('utils/storage');storage.setToken('old')
    const promise=r.load('services/auth').validateSession();await Promise.resolve()
    r.pending.shift().fail({errMsg:'timeout'});await assert.rejects(promise)
    assert.equal(storage.getToken(),'old');assert.equal(r.calls.length,0)
  })
  test(label+': bad password does not trigger an authenticated redirect',async()=>{
    const r=runtime(root), promise=r.load('services/auth').login({username:'admin',password:'wrong'})
    await Promise.resolve();r.reply(401,expired);await assert.rejects(promise)
    assert.equal(r.calls.length,0)
  })
  test(label+': stored token is validated before opening the home tab',async()=>{
    const r=runtime(root);r.load('utils/storage').setToken('saved')
    r.load(label==='main'?'pages/login/index':'pages/login/login')
    const promise=r.page.onLoad({});await Promise.resolve()
    assert.equal(r.calls.length,0);assert.match(r.pending[0].url,/\/auth\/me$/)
    r.reply(200,ok({userId:'23',userName:'existing',nickName:'现有账号',roles:['common'],permissions:[]}))
    await promise;assert.equal(r.calls.length,1)
    assert.equal(r.load('utils/storage').getUser().user.userId,'23')
  })
  test(label+': changing backend roots discards the old token',()=>{
    const r=runtime(root),storage=r.load('utils/storage');storage.setToken('old')
    r.values.set('nsh-mini-auth-root','http://another-server:9100')
    assert.equal(storage.getToken(),'');assert.equal(storage.getUser(),null)
  })
}
