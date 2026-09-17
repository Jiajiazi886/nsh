// Real loopback backend verification. Mock only the wx runtime, never API data.
const assert=require('node:assert/strict')
const path=require('node:path')
const values=new Map()
global.getApp=()=>({globalData:{}})
global.wx={
  getStorageSync:k=>values.get(k),setStorageSync:(k,v)=>values.set(k,v),removeStorageSync:k=>values.delete(k),
  showToast:()=>{},
  getAccountInfoSync:()=>({miniProgram:{envVersion:'develop'}}),reLaunch:()=>{},
  request:options=>{
    const headers=options.header||{}
    const form=String(headers['Content-Type']||'').includes('x-www-form-urlencoded')
    fetch(options.url,{method:options.method,headers,body:options.data===undefined?undefined:form?options.data:JSON.stringify(options.data)})
      .then(async response=>options.success({statusCode:response.status,data:await response.json(),header:{}}))
      .catch(()=>options.fail({errMsg:'request:fail'}))
  },
}
async function verify(root,write){
  const password=process.env.NSH_DEMO_PASSWORD
  if(!password)throw new Error('Set NSH_DEMO_PASSWORD before running the live mini verification')
  const auth=require(path.join(root,'services/auth.js'))
  const storage=require(path.join(root,'utils/storage.js'))
  const api=require(path.join(root,'services/activities.js')).getClient()
  storage.clearSession()
  const result=await auth.login({username:'nsh_demo_manager',password})
  storage.setToken(result.token)
  const user=await auth.validateSession()
  const mine=await api.activities({kind:'mine',pageSize:100})
  const activity=mine.items.find(a=>a.orgType==='guild'&&a.state==='open'&&!a.isPublic)
  assert.ok(activity)
  const detail=await api.activity(activity.activityId)
  assert.equal(detail.totalSeats,60)
  assert.ok(detail.snapshot.snapshotId)
  assert.equal(detail.canManage,true)
  assert.equal([...values.keys()].some(k=>/password/i.test(k)),false)
  const styles=require(path.join(root,'utils/profession-styles.js'));await styles.refresh()
  const remoteStyles=await api.professionStyles()
  assert.deepEqual(styles.style(remoteStyles[0].profession),{backgroundColor:remoteStyles[0].backgroundColor,color:remoteStyles[0].textColor})
  let definition;global.Component=d=>definition=d
  require(path.join(root,'components/player-profile-form/index.js'))
  const component={...definition.methods,data:JSON.parse(JSON.stringify(definition.data)),setData(data){for(const [k,v] of Object.entries(data)){const keys=k.split('.');if(keys.length===2)this.data[keys[0]][keys[1]]=v;else this.data[k]=v}}}
  await component.load();assert.equal(component.data.ready,true)
  if(write){component.input({currentTarget:{dataset:{field:'playerUid'}},detail:{value:'0009101'}});component.orange({detail:{value:true}});await component.save();assert.equal(component.data.error,'')}
  assert.equal(component.data.form.playerUid,'0009101');assert.equal(component.data.form.hasOrangeWeapon,true)
  assert.deepEqual(await api.playerProfile(),component.data.form)
  const profile=component.data.form
  await auth.logout();storage.clearSession()
  return {userId:user.userId,snapshotId:detail.snapshot.snapshotId,profile}

}
async function main(){
  const root=path.resolve(__dirname,'../../xiaochengxu')
  const a=await verify(root,true),b=await verify(path.join(root,'hhhhhhtml/jiusi-data-dashboard-frontend/demo'),false)
  assert.deepEqual(a,b)
  console.log('LIVE MINI PASSED: both mini service stacks log in to the real backend using the same account and read the same 60-seat saved snapshot, profession styles and persisted player profile through their real form components.')
}
main().catch(error=>{console.error(error.message);process.exitCode=1})
